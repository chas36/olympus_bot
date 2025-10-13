from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import List, Dict
import tempfile
import os
import io
import csv

from database.database import get_async_session
from database.models import OlympiadSession, Grade8Code, Grade9Code, Student
from parser.csv_parser import parse_codes_csv
from datetime import datetime

router = APIRouter(prefix="/api/codes", tags=["Codes"])


@router.post("/upload-csv")
async def upload_codes_csv(
    files: List[UploadFile] = File(...),
    auto_reserve: bool = Query(True, description="Автоматически резервировать коды 9 класса для 8"),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Загрузка кодов из CSV с группировкой по предметам.

    Все коды одного предмета из разных параллелей объединяются в одну сессию.
    Дата берется из CSV файла.
    """
    results = []
    # Словарь для группировки: {subject: {date: datetime, codes_by_class: {8: [...], 9: [...]}}}
    subjects_map = {}

    for file in files:
        if not file.filename.endswith('.csv'):
            continue

        # Сохраняем временно
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        try:
            # Парсим
            parsed = parse_codes_csv(tmp_path, encoding='windows-1251')

            for subject_data in parsed:
                subject = subject_data['subject']
                class_num = subject_data['class_number']
                codes = subject_data['codes']
                date = subject_data.get('date') or datetime.now()

                # Группируем по предметам
                if subject not in subjects_map:
                    subjects_map[subject] = {
                        'date': date,
                        'codes_by_class': {}
                    }

                # Добавляем коды для этого класса
                if class_num not in subjects_map[subject]['codes_by_class']:
                    subjects_map[subject]['codes_by_class'][class_num] = []

                subjects_map[subject]['codes_by_class'][class_num].extend(codes)

                results.append({
                    "file": file.filename,
                    "subject": subject,
                    "class": class_num,
                    "codes_count": len(codes)
                })

        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    # Создаем сессии для каждого предмета
    created_sessions = []
    for subject, data in subjects_map.items():
        # Проверяем, существует ли уже сессия для этого предмета
        result = await session.execute(
            select(OlympiadSession).where(
                OlympiadSession.subject == subject
            )
        )
        existing_session = result.scalar_one_or_none()

        if existing_session:
            # Обновляем существующую сессию
            olympiad = existing_session
            olympiad.date = data['date']
        else:
            # Создаем новую сессию
            olympiad = OlympiadSession(
                subject=subject,
                date=data['date'],
                is_active=False
            )
            session.add(olympiad)

        await session.flush()

        # Добавляем коды всех классов
        for class_num, codes in data['codes_by_class'].items():
            if class_num == 8:
                for code_str in codes:
                    code = Grade8Code(
                        student_id=None,
                        session_id=olympiad.id,
                        code=code_str,
                        is_issued=False
                    )
                    session.add(code)

            elif class_num == 9:
                for code_str in codes:
                    code = Grade9Code(
                        session_id=olympiad.id,
                        code=code_str,
                        is_used=False
                    )
                    session.add(code)

        created_sessions.append({
            "subject": subject,
            "date": data['date'].isoformat() if isinstance(data['date'], datetime) else str(data['date']),
            "classes": list(data['codes_by_class'].keys())
        })

    await session.commit()

    # Автоматическое резервирование
    if auto_reserve:
        reserve_result = await reserve_grade9_for_grade8(session)
        return {
            "success": True,
            "uploaded": results,
            "sessions_created": created_sessions,
            "reservation": reserve_result
        }

    return {
        "success": True,
        "uploaded": results,
        "sessions_created": created_sessions
    }


async def reserve_grade9_for_grade8(session: AsyncSession) -> Dict:
    """
    Автоматическое резервирование кодов 9 класса для 8 классов
    
    Логика:
    1. Получаем количество учеников 8 класса
    2. Получаем количество свободных кодов 8 класса
    3. Если кодов не хватает - берем из 9 класса
    """
    # Получаем активную сессию
    result = await session.execute(
        select(OlympiadSession).where(OlympiadSession.is_active == True)
    )
    active_session = result.scalar_one_or_none()
    
    if not active_session:
        return {"message": "Нет активной сессии", "reserved": 0}
    
    # Количество учеников 8 класса
    result = await session.execute(
        select(func.count(Student.id)).where(Student.is_registered == True)
    )
    students_count = result.scalar()
    
    # Количество свободных кодов 8 класса
    result = await session.execute(
        select(func.count(Grade8Code.id)).where(
            and_(
                Grade8Code.session_id == active_session.id,
                Grade8Code.student_id == None
            )
        )
    )
    available_grade8 = result.scalar()
    
    # Нужно зарезервировать
    needed = max(0, students_count - available_grade8)
    
    if needed == 0:
        return {"message": "Резервирование не требуется", "reserved": 0}
    
    # Получаем свободные коды 9 класса
    result = await session.execute(
        select(Grade9Code).where(
            and_(
                Grade9Code.session_id == active_session.id,
                Grade9Code.is_used == False
            )
        ).limit(needed)
    )
    grade9_codes = result.scalars().all()
    
    # Конвертируем коды 9 класса в коды 8 класса
    reserved_count = 0
    for grade9_code in grade9_codes:
        # Создаем новый код для 8 класса
        new_grade8_code = Grade8Code(
            student_id=None,
            session_id=active_session.id,
            code=grade9_code.code,  # Используем тот же код
            is_issued=False
        )
        session.add(new_grade8_code)
        
        # Помечаем код 9 класса как использованный
        grade9_code.is_used = True
        
        reserved_count += 1
    
    await session.commit()
    
    return {
        "message": f"Зарезервировано {reserved_count} кодов из 9 класса для 8 класса",
        "reserved": reserved_count,
        "needed": needed
    }


@router.post("/reserve")
async def manual_reserve(
    session: AsyncSession = Depends(get_async_session)
):
    """Ручное резервирование кодов 9→8"""
    result = await reserve_grade9_for_grade8(session)
    return result


@router.get("/sessions")
async def get_sessions(
    session: AsyncSession = Depends(get_async_session)
):
    """Получить все сессии"""
    result = await session.execute(
        select(OlympiadSession).order_by(OlympiadSession.date.desc())
    )
    sessions = result.scalars().all()
    
    return [
        {
            "id": s.id,
            "subject": s.subject,
            "date": s.date.isoformat(),
            "is_active": s.is_active
        }
        for s in sessions
    ]


@router.post("/sessions/{session_id}/activate")
async def activate_session(
    session_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    """Активировать сессию"""
    # Деактивируем все
    result = await session.execute(select(OlympiadSession))
    for s in result.scalars().all():
        s.is_active = False
    
    # Активируем нужную
    result = await session.execute(
        select(OlympiadSession).where(OlympiadSession.id == session_id)
    )
    target = result.scalar_one_or_none()
    
    if not target:
        raise HTTPException(404, "Сессия не найдена")
    
    target.is_active = True
    await session.commit()
    
    return {"success": True, "session_id": session_id}


@router.get("/stats")
async def get_codes_stats(
    session: AsyncSession = Depends(get_async_session)
):
    """Статистика по кодам"""
    # Коды 8 класса
    result = await session.execute(select(func.count(Grade8Code.id)))
    total_grade8 = result.scalar()
    
    result = await session.execute(
        select(func.count(Grade8Code.id)).where(Grade8Code.student_id != None)
    )
    assigned_grade8 = result.scalar()
    
    result = await session.execute(
        select(func.count(Grade8Code.id)).where(Grade8Code.is_issued == True)
    )
    issued_grade8 = result.scalar()
    
    # Коды 9 класса
    result = await session.execute(select(func.count(Grade9Code.id)))
    total_grade9 = result.scalar()
    
    result = await session.execute(
        select(func.count(Grade9Code.id)).where(Grade9Code.is_used == True)
    )
    used_grade9 = result.scalar()
    
    return {
        "grade8": {
            "total": total_grade8,
            "assigned": assigned_grade8,
            "unassigned": total_grade8 - assigned_grade8,
            "issued": issued_grade8
        },
        "grade9": {
            "total": total_grade9,
            "used": used_grade9,
            "available": total_grade9 - used_grade9
        }
    }


@router.get("/export/session/{session_id}")
async def export_session_codes(
    session_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    """Экспорт кодов сессии в CSV"""
    from urllib.parse import quote
    
    # Получаем сессию
    result = await session.execute(
        select(OlympiadSession).where(OlympiadSession.id == session_id)
    )
    olympiad = result.scalar_one_or_none()
    
    if not olympiad:
        raise HTTPException(404, "Сессия не найдена")
    
    # Получаем коды 8 класса
    result = await session.execute(
        select(Grade8Code).where(Grade8Code.session_id == session_id)
    )
    codes8 = result.scalars().all()
    
    # Создаем CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([f"Коды - {olympiad.subject} - 8 класс"])
    writer.writerow([f"Дата: {olympiad.date.strftime('%d.%m.%Y')}"])
    writer.writerow([])
    writer.writerow(["№", "ФИО", "Код", "Выдан"])
    
    for i, code in enumerate(codes8, 1):
        student_name = "-"
        if code.student:
            student_name = code.student.full_name
        
        writer.writerow([
            i,
            student_name,
            code.code,
            "Да" if code.is_issued else "Нет"
        ])
    
    output.seek(0)
    
    # Используем транслитерацию для имени файла
    # Простая замена русских букв на латинские
    transliteration = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
        'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
        'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
        ' ': '_', '-': '_'
    }
    
    safe_subject = olympiad.subject.lower()
    for ru, en in transliteration.items():
        safe_subject = safe_subject.replace(ru, en)
    
    filename = f"{safe_subject}_8klass.csv"
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )