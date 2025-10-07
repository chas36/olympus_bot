from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from database.database import get_async_session
from typing import List, Dict
from pydantic import BaseModel
import os
import tempfile
import io

from database.models import OlympiadSession, DistributionMode
from parser.csv_parser import parse_codes_csv
from utils.code_distribution import CodeDistributor
from utils.export import CodeExporter
from datetime import datetime

router = APIRouter(prefix="/admin/codes", tags=["Codes Management"])


class SessionCreate(BaseModel):
    """Модель для создания сессии"""
    subject: str
    date: datetime = None
    distribution_mode: str = "on_demand"  # pre_distributed или on_demand


@router.post("/upload-csv")
async def upload_codes_csv(
    files: List[UploadFile] = File(...),
    subject: str = None,
    distribution_mode: str = "on_demand",
    session: AsyncSession = Depends(get_async_session)
) -> Dict:
    """
    Загрузка CSV файлов с кодами
    
    Процесс:
    1. Парсит все CSV файлы
    2. Создает сессию олимпиады
    3. Создает коды для каждого класса
    4. Создает резерв из кодов 9 класса
    5. Опционально распределяет коды сразу (pre-distributed режим)
    """
    results = []
    parsed_data = []
    
    # Парсим все файлы
    for file in files:
        if not file.filename.endswith('.csv'):
            continue
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        try:
            data = parse_codes_csv(tmp_path)
            parsed_data.append({
                "filename": file.filename,
                "data": data
            })
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    
    if not parsed_data:
        raise HTTPException(
            status_code=400,
            detail="Не удалось распарсить ни один файл"
        )
    
    # Определяем предмет и дату
    first_data = parsed_data[0]["data"]
    session_subject = subject or first_data["subject"]
    session_date = first_data["date"] or datetime.now()
    
    # Деактивируем предыдущие сессии этого предмета
    from sqlalchemy import update
    await session.execute(
        update(OlympiadSession)
        .where(OlympiadSession.subject == session_subject)
        .values(is_active=False)
    )
    
    # Создаем новую сессию
    mode = DistributionMode.PRE_DISTRIBUTED if distribution_mode == "pre_distributed" else DistributionMode.ON_DEMAND
    
    olympiad = OlympiadSession(
        subject=session_subject,
        date=session_date,
        distribution_mode=mode,
        uploaded_file_name=", ".join([p["filename"] for p in parsed_data])
    )
    session.add(olympiad)
    await session.flush()
    
    # Создаем коды
    codes_created = {}
    
    for parsed in parsed_data:
        data = parsed["data"]
        class_num = data["class_number"]
        codes = data["codes"]
        
        if class_num and codes:
            created = await CodeDistributor.create_codes_from_csv(
                session,
                session_id=olympiad.id,
                class_number=class_num,
                codes=codes
            )
            
            codes_created[class_num] = len(created)
            results.append({
                "filename": parsed["filename"],
                "class": class_num,
                "codes_count": len(created)
            })
    
    await session.commit()
    
    # Создаем резерв из 9 класса
    reserve_distribution = {}
    if 9 in codes_created:
        reserve_distribution = await CodeDistributor.create_reserve_from_grade9(
            session, olympiad.id
        )
    
    # Предварительное распределение если нужно
    distribution_results = None
    if mode == DistributionMode.PRE_DISTRIBUTED:
        distribution_results = await CodeDistributor.distribute_codes_pre_assign(
            session, olympiad.id
        )
    
    return {
        "success": True,
        "session_id": olympiad.id,
        "subject": session_subject,
        "distribution_mode": mode.value,
        "files_processed": results,
        "reserve_distribution": reserve_distribution,
        "pre_distribution": distribution_results
    }


@router.post("/distribute/{session_id}")
async def distribute_codes(
    session_id: int,
    session: AsyncSession = Depends(get_async_session)
) -> Dict:
    """
    Распределение кодов между учениками (для pre-distributed режима)
    
    Использовать, если изначально коды были загружены в on-demand режиме,
    но теперь нужно распределить их заранее
    """
    results = await CodeDistributor.distribute_codes_pre_assign(
        session, session_id
    )
    
    return {
        "success": True,
        "assigned": len(results["assigned"]),
        "failed": len(results["failed"]),
        "details": results
    }


@router.get("/available/{session_id}")
async def get_available_codes(
    session_id: int,
    class_number: int = None,
    session: AsyncSession = Depends(get_async_session)
) -> Dict:
    """Получить количество доступных кодов"""
    counts = await CodeDistributor.get_available_codes_count(
        session, session_id, class_number
    )
    
    return {
        "session_id": session_id,
        "available_codes": counts
    }


@router.post("/reassign/{code_id}")
async def reassign_code(
    code_id: int,
    new_student_id: int,
    session: AsyncSession = Depends(get_async_session)
) -> Dict:
    """Переназначить код другому ученику"""
    code = await CodeDistributor.reassign_code(
        session, code_id, new_student_id
    )
    
    return {
        "success": True,
        "code_id": code.id,
        "new_student_id": new_student_id,
        "code": code.code
    }


@router.get("/export/class/{session_id}/{class_number}")
async def export_class_codes(
    session_id: int,
    class_number: int,
    include_unassigned: bool = False,
    session: AsyncSession = Depends(get_async_session)
):
    """Экспорт кодов конкретного класса в CSV"""
    csv_data = await CodeExporter.export_class_codes_csv(
        session, session_id, class_number, include_unassigned
    )
    
    # Получаем информацию о сессии для имени файла
    from sqlalchemy import select
    result = await session.execute(
        select(OlympiadSession).where(OlympiadSession.id == session_id)
    )
    olympiad = result.scalar_one_or_none()
    
    filename = f"{olympiad.subject}_{class_number}_класс.csv"
    
    return StreamingResponse(
        io.StringIO(csv_data),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.get("/export/all/{session_id}")
async def export_all_classes_archive(
    session_id: int,
    include_unassigned: bool = False,
    session: AsyncSession = Depends(get_async_session)
):
    """Экспорт всех классов в ZIP архив"""
    zip_data = await CodeExporter.export_all_classes_zip(
        session, session_id, include_unassigned
    )
    
    # Получаем информацию о сессии для имени файла
    from sqlalchemy import select
    result = await session.execute(
        select(OlympiadSession).where(OlympiadSession.id == session_id)
    )
    olympiad = result.scalar_one_or_none()
    
    filename = f"{olympiad.subject}_все_классы.zip"
    
    return StreamingResponse(
        io.BytesIO(zip_data),
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.get("/sessions")
async def get_all_sessions(
    session: AsyncSession = Depends(get_async_session)
) -> List[Dict]:
    """Получить список всех сессий"""
    from sqlalchemy import select
    
    result = await session.execute(
        select(OlympiadSession).order_by(OlympiadSession.date.desc())
    )
    sessions = result.scalars().all()
    
    return [
        {
            "id": s.id,
            "subject": s.subject,
            "date": s.date.isoformat(),
            "distribution_mode": s.distribution_mode.value,
            "is_active": s.is_active
        }
        for s in sessions
    ]


@router.post("/sessions/{session_id}/activate")
async def activate_session(
    session_id: int,
    session: AsyncSession = Depends(get_async_session)
) -> Dict:
    """Активировать сессию"""
    from sqlalchemy import update, select
    
    # Деактивируем все
    await session.execute(
        update(OlympiadSession).values(is_active=False)
    )
    
    # Активируем нужную
    await session.execute(
        update(OlympiadSession)
        .where(OlympiadSession.id == session_id)
        .values(is_active=True)
    )
    
    await session.commit()
    
    return {"success": True, "session_id": session_id}