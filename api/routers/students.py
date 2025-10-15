from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Optional
from pydantic import BaseModel
import tempfile
import os

from database.database import get_async_session
from database.models import Student
from parser.excel_parser import parse_students_excel
from utils.auth import generate_multiple_codes, generate_registration_code

router = APIRouter(prefix="/api/students", tags=["Students"])


class StudentCreate(BaseModel):
    full_name: str
    class_number: Optional[int] = None
    parallel: Optional[str] = None


class StudentUpdate(BaseModel):
    full_name: Optional[str] = None
    class_number: Optional[int] = None
    parallel: Optional[str] = None


@router.get("/", response_model=List[Dict])
async def get_all_students(
    include_inactive: bool = Query(False, description="Включить не зарегистрированных учеников"),
    session: AsyncSession = Depends(get_async_session)
):
    """Получить всех учеников"""
    query = select(Student).order_by(Student.class_number, Student.parallel, Student.full_name)
    if not include_inactive:
        query = query.where(Student.is_registered == True)

    result = await session.execute(query)
    students = result.scalars().all()

    return [
        {
            "id": s.id,
            "full_name": s.full_name,
            "registration_code": s.registration_code,
            "is_registered": s.is_registered,
            "telegram_id": s.telegram_id,
            "class_number": s.class_number,
            "parallel": s.parallel,
            "class_display": f"{s.class_number}{s.parallel or ''}" if s.class_number else None
        }
        for s in students
    ]


@router.post("/upload-excel")
async def upload_students_excel(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_async_session)
):
    """Загрузка учеников из Excel"""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(400, "Поддерживаются только .xlsx и .xls файлы")
    
    # Сохраняем временный файл
    with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        # Парсим
        students_data, validation = parse_students_excel(tmp_path)
        
        # Генерируем коды
        reg_codes = generate_multiple_codes(len(students_data))
        
        created = []
        skipped = []
        
        for student_data, reg_code in zip(students_data, reg_codes):
            # Проверяем существование
            result = await session.execute(
                select(Student).where(Student.full_name == student_data["full_name"])
            )
            existing = result.scalar_one_or_none()

            if existing:
                skipped.append(student_data["full_name"])
                continue

            # Создаем
            student = Student(
                full_name=student_data["full_name"],
                registration_code=reg_code,
                is_registered=False,
                class_number=student_data.get("class_number"),
                parallel=student_data.get("parallel")
            )
            session.add(student)
            created.append({
                "name": student_data["full_name"],
                "code": reg_code,
                "class": f"{student_data.get('class_number')}{student_data.get('parallel') or ''}"
            })
        
        await session.commit()
        
        return {
            "success": True,
            "created": len(created),
            "skipped": len(skipped),
            "students": created,
            "validation": validation
        }
    
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@router.post("/create")
async def create_student(
    student_data: StudentCreate,
    session: AsyncSession = Depends(get_async_session)
):
    """Создать нового ученика"""

    # Проверяем, что ученик с таким именем не существует
    result = await session.execute(
        select(Student).where(Student.full_name == student_data.full_name)
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(400, f"Ученик с именем '{student_data.full_name}' уже существует")

    # Генерируем регистрационный код
    reg_code = generate_registration_code()

    # Создаем ученика
    student = Student(
        full_name=student_data.full_name,
        registration_code=reg_code,
        is_registered=False,
        class_number=student_data.class_number,
        parallel=student_data.parallel
    )

    session.add(student)
    await session.commit()
    await session.refresh(student)

    return {
        "success": True,
        "message": "Ученик создан",
        "student": {
            "id": student.id,
            "full_name": student.full_name,
            "registration_code": student.registration_code,
            "class_number": student.class_number,
            "parallel": student.parallel,
            "class_display": f"{student.class_number}{student.parallel or ''}" if student.class_number else None
        }
    }


@router.put("/{student_id}")
async def update_student(
    student_id: int,
    student_data: StudentUpdate,
    session: AsyncSession = Depends(get_async_session)
):
    """Обновить данные ученика (например, перевести в другой класс)"""

    result = await session.execute(
        select(Student).where(Student.id == student_id)
    )
    student = result.scalar_one_or_none()

    if not student:
        raise HTTPException(404, "Ученик не найден")

    # Обновляем поля
    if student_data.full_name is not None:
        student.full_name = student_data.full_name

    if student_data.class_number is not None:
        student.class_number = student_data.class_number

    if student_data.parallel is not None:
        student.parallel = student_data.parallel

    await session.commit()
    await session.refresh(student)

    return {
        "success": True,
        "message": "Данные ученика обновлены",
        "student": {
            "id": student.id,
            "full_name": student.full_name,
            "registration_code": student.registration_code,
            "class_number": student.class_number,
            "parallel": student.parallel,
            "class_display": f"{student.class_number}{student.parallel or ''}" if student.class_number else None,
            "is_registered": student.is_registered,
            "telegram_id": student.telegram_id
        }
    }


@router.get("/stats")
async def get_students_stats(
    session: AsyncSession = Depends(get_async_session)
):
    """Статистика по ученикам"""
    from sqlalchemy import func

    # Всего
    result = await session.execute(select(func.count(Student.id)))
    total = result.scalar()

    # Зарегистрированных
    result = await session.execute(
        select(func.count(Student.id)).where(Student.is_registered == True)
    )
    registered = result.scalar()

    # Статистика по классам
    result = await session.execute(
        select(Student.class_number, func.count(Student.id))
        .where(Student.class_number.isnot(None))
        .group_by(Student.class_number)
        .order_by(Student.class_number)
    )
    by_class = {row[0]: row[1] for row in result.fetchall()}

    return {
        "total": total,
        "registered": registered,
        "not_registered": total - registered,
        "by_class": by_class
    }


@router.get("/classes")
async def get_classes_list(
    session: AsyncSession = Depends(get_async_session)
):
    """Получить список всех классов с параллелями"""
    from sqlalchemy import func, distinct

    # Получаем все уникальные комбинации класс-параллель
    result = await session.execute(
        select(Student.class_number, Student.parallel, func.count(Student.id))
        .where(Student.class_number.isnot(None))
        .group_by(Student.class_number, Student.parallel)
        .order_by(Student.class_number, Student.parallel)
    )

    classes_data = []
    for row in result.fetchall():
        class_num, parallel, count = row
        classes_data.append({
            "class_number": class_num,
            "parallel": parallel,
            "display": f"{class_num}{parallel or ''}",
            "students_count": count
        })

    return {"classes": classes_data}


@router.get("/{student_id}")
async def get_student(
    student_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    """Получить информацию об ученике"""
    result = await session.execute(
        select(Student).where(Student.id == student_id)
    )
    student = result.scalar_one_or_none()

    if not student:
        raise HTTPException(404, "Ученик не найден")

    return {
        "id": student.id,
        "full_name": student.full_name,
        "registration_code": student.registration_code,
        "class_number": student.class_number,
        "parallel": student.parallel,
        "class_display": f"{student.class_number}{student.parallel or ''}" if student.class_number else None,
        "is_registered": student.is_registered,
        "telegram_id": student.telegram_id,
        "telegram_username": getattr(student, 'telegram_username', None)
    }


@router.delete("/{student_id}")
async def delete_student(
    student_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    """Удалить ученика"""
    result = await session.execute(
        select(Student).where(Student.id == student_id)
    )
    student = result.scalar_one_or_none()

    if not student:
        raise HTTPException(404, "Ученик не найден")

    await session.delete(student)
    await session.commit()

    return {"success": True, "message": "Ученик удален"}


@router.get("/export/registration-codes")
async def export_registration_codes(
    class_number: int = Query(None, description="Фильтр по классу"),
    parallel: str = Query(None, description="Фильтр по параллели"),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Экспорт регистрационных кодов учеников в CSV.

    Коды группируются по классам и параллелям.
    """
    from fastapi.responses import StreamingResponse
    import csv
    import io

    # Строим запрос с фильтрами
    query = select(Student).order_by(Student.class_number, Student.parallel, Student.full_name)

    if class_number:
        query = query.where(Student.class_number == class_number)

    if parallel:
        query = query.where(Student.parallel == parallel)

    result = await session.execute(query)
    students = result.scalars().all()

    if not students:
        raise HTTPException(404, "Ученики не найдены")

    # Создаем CSV
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["Регистрационные коды для бота Olympus"])
    writer.writerow([])
    writer.writerow(["№", "ФИО", "Класс", "Код регистрации", "Статус"])

    for i, student in enumerate(students, 1):
        class_display = f"{student.class_number}{student.parallel or ''}" if student.class_number else "-"
        status = "Зарегистрирован" if student.is_registered else "Ожидает"

        writer.writerow([
            i,
            student.full_name,
            class_display,
            student.registration_code,
            status
        ])

    output.seek(0)

    # Формируем имя файла
    from urllib.parse import quote

    filename_parts = ["registration_codes"]
    if class_number:
        filename_parts.append(f"class{class_number}")
    if parallel:
        filename_parts.append(f"parallel{parallel}")
    filename = "_".join(filename_parts) + ".csv"

    # Кодируем имя файла для поддержки русских букв
    filename_encoded = quote(filename, safe='')

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{filename_encoded}"
        }
    )