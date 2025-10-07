from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from database.database import get_async_session
from typing import List, Dict
from pydantic import BaseModel
import os
import tempfile

from parser.excel_parser import parse_students_excel
from utils.student_management import StudentManager

router = APIRouter(prefix="/admin/students", tags=["Students Management"])


class StudentCreate(BaseModel):
    """Модель для создания ученика"""
    full_name: str
    class_number: int


class StudentUpdate(BaseModel):
    """Модель для обновления ученика"""
    full_name: str = None
    class_number: int = None


class ClassChange(BaseModel):
    """Модель для перевода в другой класс"""
    new_class: int


@router.post("/upload-excel")
async def upload_students_excel(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_async_session)
) -> Dict:
    """
    Массовая загрузка учеников из Excel файла
    """
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=400,
            detail="Неверный формат файла. Поддерживаются только .xlsx и .xls"
        )
    
    # Сохраняем временный файл
    with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_path = tmp_file.name
    
    try:
        # Парсим Excel
        students_data, validation = parse_students_excel(tmp_path)
        
        # Создаем учеников
        created_students = await StudentManager.bulk_create_students(
            session, students_data
        )
        
        return {
            "success": True,
            "count": len(created_students),
            "students": [
                {
                    "id": s.id,
                    "full_name": s.full_name,
                    "class_number": s.class_number,
                    "registration_code": s.registration_code
                }
                for s in created_students
            ],
            "validation": {
                "duplicates": validation["duplicates"],
                "invalid_names": validation["invalid_names"],
                "class_distribution": validation["class_distribution"]
            }
        }
    
    finally:
        # Удаляем временный файл
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@router.post("/update-from-excel")
async def update_students_from_excel(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_async_session)
) -> Dict:
    """
    Обновление списка учеников из Excel с автоматической сверкой
    
    Процесс:
    - Сравнивает новый список с существующим
    - Добавляет новых учеников
    - Обновляет изменившихся
    - Деактивирует отсутствующих
    """
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=400,
            detail="Неверный формат файла"
        )
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_path = tmp_file.name
    
    try:
        students_data, validation = parse_students_excel(tmp_path)
        
        # Сверка и обновление
        results = await StudentManager.compare_and_update(session, students_data)
        
        return {
            "success": True,
            "added": results["added"],
            "updated": results["updated"],
            "deactivated": results["deactivated"],
            "unchanged_count": len(results["unchanged"]),
            "validation": validation
        }
    
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@router.post("/")
async def create_student(
    student_data: StudentCreate,
    session: AsyncSession = Depends(get_async_session)
) -> Dict:
    """Создание одного ученика"""
    student = await StudentManager.create_student(
        session,
        full_name=student_data.full_name,
        class_number=student_data.class_number
    )
    
    return {
        "id": student.id,
        "full_name": student.full_name,
        "class_number": student.class_number,
        "registration_code": student.registration_code
    }


@router.put("/{student_id}")
async def update_student(
    student_id: int,
    student_data: StudentUpdate,
    session: AsyncSession = Depends(get_async_session)
) -> Dict:
    """Обновление данных ученика"""
    student = await StudentManager.update_student(
        session,
        student_id=student_id,
        full_name=student_data.full_name,
        class_number=student_data.class_number
    )
    
    return {
        "id": student.id,
        "full_name": student.full_name,
        "class_number": student.class_number
    }


@router.put("/{student_id}/change-class")
async def change_student_class(
    student_id: int,
    class_data: ClassChange,
    session: AsyncSession = Depends(get_async_session)
) -> Dict:
    """Перевод ученика в другой класс"""
    student = await StudentManager.change_class(
        session,
        student_id=student_id,
        new_class=class_data.new_class
    )
    
    return {
        "id": student.id,
        "full_name": student.full_name,
        "old_class": None,  # Можно получить из истории
        "new_class": student.class_number,
        "message": "Ученик успешно переведен"
    }


@router.delete("/{student_id}")
async def deactivate_student(
    student_id: int,
    session: AsyncSession = Depends(get_async_session)
) -> Dict:
    """Деактивация (архивирование) ученика"""
    student = await StudentManager.deactivate_student(session, student_id)
    
    return {
        "id": student.id,
        "full_name": student.full_name,
        "is_active": student.is_active,
        "message": "Ученик деактивирован"
    }


@router.get("/by-class/{class_number}")
async def get_students_by_class(
    class_number: int,
    include_inactive: bool = False,
    session: AsyncSession = Depends(get_async_session)
) -> List[Dict]:
    """Получение учеников конкретного класса"""
    students = await StudentManager.get_class_students(
        session, class_number, include_inactive
    )
    
    return [
        {
            "id": s.id,
            "full_name": s.full_name,
            "class_number": s.class_number,
            "is_registered": s.is_registered,
            "is_active": s.is_active
        }
        for s in students
    ]


@router.get("/distribution")
async def get_class_distribution(
    include_inactive: bool = False,
    session: AsyncSession = Depends(get_async_session)
) -> Dict:
    """Получение распределения учеников по классам"""
    distribution = await StudentManager.get_students_by_class_distribution(
        session, include_inactive
    )
    
    return {
        class_num: {
            "count": len(students),
            "students": [
                {
                    "id": s.id,
                    "full_name": s.full_name,
                    "is_registered": s.is_registered
                }
                for s in students
            ]
        }
        for class_num, students in distribution.items()
    }