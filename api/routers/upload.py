from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from database.database import get_async_session
from database import crud
from parser.docx_parser import parse_olympiad_file
from datetime import datetime
import os
import shutil
from typing import Dict

router = APIRouter(prefix="/upload", tags=["Upload"])

UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@router.post("/olympiad-file")
async def upload_olympiad_file(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_async_session)
) -> Dict:
    """
    Загрузка файла с кодами олимпиады
    
    Процесс:
    1. Сохраняет файл
    2. Парсит содержимое
    3. Создает новую сессию олимпиады
    4. Деактивирует предыдущие сессии
    5. Создает коды для 8 и 9 классов
    """
    
    # Проверяем расширение файла
    if not file.filename.endswith(('.doc', '.docx')):
        raise HTTPException(
            status_code=400,
            detail="Неверный формат файла. Поддерживаются только .doc и .docx"
        )
    
    # Генерируем уникальное имя файла
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{file.filename}"
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    
    # Сохраняем файл
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка сохранения файла: {str(e)}"
        )
    
    # Парсим файл
    parsed_data = None
    try:
        parsed_data = parse_olympiad_file(file_path)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Ошибка парсинга файла: {str(e)}"
        )
    finally:
        # Удаляем файл после парсинга, независимо от результата
        if os.path.exists(file_path):
            os.remove(file_path)
    
    # Деактивируем все предыдущие сессии
    await crud.deactivate_all_sessions(session)
    
    # Создаем новую сессию олимпиады
    olympiad_session = await crud.create_olympiad_session(
        session,
        subject=parsed_data["subject"],
        date=datetime.now(),
        uploaded_file_name=filename
    )
    
    # Создаем коды для 8 класса (именные)
    grade8_count = 0
    students_not_found = []
    
    for student_data in parsed_data["grade8_codes"]:
        full_name = student_data["full_name"]
        code = student_data["code"]
        
        # Ищем ученика по ФИО
        students = await crud.get_all_students(session)
        student = next((s for s in students if s.full_name == full_name), None)
        
        if student:
            await crud.create_grade8_code(
                session,
                student_id=student.id,
                session_id=olympiad_session.id,
                code=code
            )
            grade8_count += 1
        else:
            students_not_found.append(full_name)
    
    # Создаем коды для 9 класса (пул)
    grade9_count = 0
    for code in parsed_data["grade9_codes"]:
        await crud.create_grade9_code(
            session,
            session_id=olympiad_session.id,
            code=code
        )
        grade9_count += 1
    
    result = {
        "success": True,
        "session_id": olympiad_session.id,
        "subject": parsed_data["subject"],
        "grade8_codes_created": grade8_count,
        "grade9_codes_created": grade9_count,
        "filename": filename
    }
    
    if students_not_found:
        result["warning"] = {
            "message": "Некоторые ученики не найдены в базе данных",
            "students": students_not_found
        }
    
    return result


@router.get("/sessions")
async def get_all_sessions(
    session: AsyncSession = Depends(get_async_session)
):
    """Получить список всех сессий олимпиад"""
    from sqlalchemy import select
    from database.models import OlympiadSession
    
    result = await session.execute(
        select(OlympiadSession).order_by(OlympiadSession.date.desc())
    )
    sessions = result.scalars().all()
    
    return [
        {
            "id": s.id,
            "subject": s.subject,
            "date": s.date.isoformat(),
            "is_active": s.is_active,
            "uploaded_file_name": s.uploaded_file_name
        }
        for s in sessions
    ]


@router.post("/sessions/{session_id}/activate")
async def activate_session(
    session_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    """Активировать определенную сессию"""
    
    # Деактивируем все сессии
    await crud.deactivate_all_sessions(session)
    
    # Активируем выбранную
    olympiad_session = await crud.get_session_by_id(session, session_id)
    
    if not olympiad_session:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    
    from sqlalchemy import update
    from database.models import OlympiadSession
    
    await session.execute(
        update(OlympiadSession)
        .where(OlympiadSession.id == session_id)
        .values(is_active=True)
    )
    await session.commit()
    
    return {"success": True, "session_id": session_id}
