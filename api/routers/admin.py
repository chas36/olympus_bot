from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from database.database import get_async_session
from database import crud
from utils.auth import generate_multiple_codes
from typing import List, Dict
from pydantic import BaseModel

router = APIRouter(prefix="/admin", tags=["Admin"])


class StudentCreate(BaseModel):
    """Модель для создания ученика"""
    full_name: str


class BulkStudentsCreate(BaseModel):
    """Модель для массового создания учеников"""
    students: List[str]  # Список ФИО


@router.post("/students")
async def create_student(
    student_data: StudentCreate,
    session: AsyncSession = Depends(get_async_session)
) -> Dict:
    """
    Создать нового ученика с регистрационным кодом
    """
    # Генерируем регистрационный код
    registration_code = generate_multiple_codes(1)[0]
    
    # Создаем ученика
    student = await crud.create_student(
        session,
        full_name=student_data.full_name,
        registration_code=registration_code
    )
    
    return {
        "id": student.id,
        "full_name": student.full_name,
        "registration_code": student.registration_code,
        "is_registered": student.is_registered
    }


@router.post("/students/bulk")
async def create_students_bulk(
    data: BulkStudentsCreate,
    session: AsyncSession = Depends(get_async_session)
) -> Dict:
    """
    Массовое создание учеников
    """
    # Генерируем коды для всех учеников
    codes = generate_multiple_codes(len(data.students))
    
    created_students = []
    
    for full_name, code in zip(data.students, codes):
        student = await crud.create_student(
            session,
            full_name=full_name.strip(),
            registration_code=code
        )
        created_students.append({
            "id": student.id,
            "full_name": student.full_name,
            "registration_code": student.registration_code
        })
    
    return {
        "success": True,
        "count": len(created_students),
        "students": created_students
    }


@router.get("/students")
async def get_all_students(
    session: AsyncSession = Depends(get_async_session)
) -> List[Dict]:
    """
    Получить список всех учеников
    """
    students = await crud.get_all_students(session)
    
    return [
        {
            "id": s.id,
            "full_name": s.full_name,
            "registration_code": s.registration_code,
            "is_registered": s.is_registered,
            "telegram_id": s.telegram_id,
            "created_at": s.created_at.isoformat(),
            "registered_at": s.registered_at.isoformat() if s.registered_at else None
        }
        for s in students
    ]


@router.get("/students/unregistered")
async def get_unregistered_students(
    session: AsyncSession = Depends(get_async_session)
) -> List[Dict]:
    """
    Получить список незарегистрированных учеников
    """
    students = await crud.get_all_students(session)
    unregistered = [s for s in students if not s.is_registered]
    
    return [
        {
            "id": s.id,
            "full_name": s.full_name,
            "registration_code": s.registration_code,
            "created_at": s.created_at.isoformat()
        }
        for s in unregistered
    ]


@router.post("/students/{student_id}/regenerate-code")
async def regenerate_registration_code(
    student_id: int,
    session: AsyncSession = Depends(get_async_session)
) -> Dict:
    """
    Перегенерировать регистрационный код для ученика
    (полезно если код был потерян или скомпрометирован)
    """
    from sqlalchemy import select, update
    from database.models import Student
    
    # Проверяем существование ученика
    result = await session.execute(
        select(Student).where(Student.id == student_id)
    )
    student = result.scalar_one_or_none()
    
    if not student:
        raise HTTPException(status_code=404, detail="Ученик не найден")
    
    if student.is_registered:
        raise HTTPException(
            status_code=400,
            detail="Нельзя перегенерировать код для зарегистрированного ученика"
        )
    
    # Генерируем новый код
    new_code = generate_multiple_codes(1)[0]
    
    # Обновляем код
    await session.execute(
        update(Student)
        .where(Student.id == student_id)
        .values(registration_code=new_code)
    )
    await session.commit()
    
    return {
        "success": True,
        "student_id": student_id,
        "full_name": student.full_name,
        "new_registration_code": new_code
    }


@router.delete("/students/{student_id}")
async def delete_student(
    student_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Удалить ученика (только если не зарегистрирован)
    """
    from sqlalchemy import select, delete
    from database.models import Student
    
    result = await session.execute(
        select(Student).where(Student.id == student_id)
    )
    student = result.scalar_one_or_none()
    
    if not student:
        raise HTTPException(status_code=404, detail="Ученик не найден")
    
    if student.is_registered:
        raise HTTPException(
            status_code=400,
            detail="Нельзя удалить зарегистрированного ученика"
        )
    
    await session.execute(
        delete(Student).where(Student.id == student_id)
    )
    await session.commit()
    
    return {"success": True, "deleted_student_id": student_id}


@router.post("/generate-codes")
async def generate_registration_codes(count: int = 10) -> Dict:
    """
    Сгенерировать регистрационные коды без привязки к ученикам
    (для печати и раздачи)
    """
    if count < 1 or count > 100:
        raise HTTPException(
            status_code=400,
            detail="Количество кодов должно быть от 1 до 100"
        )
    
    codes = generate_multiple_codes(count)
    
    return {
        "count": count,
        "codes": codes
    }


@router.get("/export/students")
async def export_students_csv(
    session: AsyncSession = Depends(get_async_session)
):
    """
    Экспорт списка учеников в CSV формат
    """
    import io
    import csv
    from fastapi.responses import StreamingResponse
    
    students = await crud.get_all_students(session)
    
    # Создаем CSV в памяти
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Заголовки
    writer.writerow([
        "ID", "ФИО", "Регистрационный код", 
        "Зарегистрирован", "Telegram ID", "Дата создания"
    ])
    
    # Данные
    for s in students:
        writer.writerow([
            s.id,
            s.full_name,
            s.registration_code,
            "Да" if s.is_registered else "Нет",
            s.telegram_id or "-",
            s.created_at.strftime("%Y-%m-%d %H:%M:%S")
        ])
    
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=students.csv"
        }
    )
