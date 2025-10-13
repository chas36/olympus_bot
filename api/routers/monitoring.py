from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from database.database import get_async_session
from database import crud
from typing import List, Dict

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])


@router.get("/statistics")
async def get_statistics(
    session: AsyncSession = Depends(get_async_session)
) -> Dict:
    """
    Получить общую статистику
    """
    # Получаем активную сессию
    active_session = await crud.get_active_session(session)
    
    if not active_session:
        return {
            "active_session": None,
            "message": "Нет активной сессии"
        }
    
    # Получаем все запросы для сессии
    all_requests = await crud.get_all_requests_for_session(session, active_session.id)
    
    # Подсчитываем статистику
    total_students = len(await crud.get_all_students(session))
    registered_students = len([s for s in await crud.get_all_students(session) if s.is_registered])
    
    requested_code_count = len(all_requests)
    grade8_requests = len([r for r in all_requests if r.grade == 8])
    grade9_requests = len([r for r in all_requests if r.grade == 9])
    
    screenshots_submitted = len([r for r in all_requests if r.screenshot_submitted])
    screenshots_missing = requested_code_count - screenshots_submitted
    
    # Доступные коды 9 класса
    available_grade9 = await crud.count_available_grade9_codes(session, active_session.id)
    
    return {
        "active_session": {
            "id": active_session.id,
            "subject": active_session.subject,
            "date": active_session.date.isoformat(),
            "uploaded_file_name": active_session.uploaded_file_name
        },
        "students": {
            "total": total_students,
            "registered": registered_students,
            "unregistered": total_students - registered_students
        },
        "codes": {
            "total_requested": requested_code_count,
            "grade8_requested": grade8_requests,
            "grade9_requested": grade9_requests,
            "grade9_available": available_grade9
        },
        "screenshots": {
            "submitted": screenshots_submitted,
            "missing": screenshots_missing,
            "percentage": round((screenshots_submitted / requested_code_count * 100) if requested_code_count > 0 else 0, 1)
        }
    }


@router.get("/students-status")
async def get_students_status(
    session: AsyncSession = Depends(get_async_session)
) -> List[Dict]:
    """
    Получить детальный статус всех учеников для активной сессии
    """
    # Получаем активную сессию
    active_session = await crud.get_active_session(session)
    
    if not active_session:
        raise HTTPException(status_code=404, detail="Нет активной сессии")
    
    # Получаем всех учеников
    all_students = await crud.get_all_students(session)
    
    # Получаем все запросы для сессии
    all_requests = await crud.get_all_requests_for_session(session, active_session.id)
    
    # Создаем словарь запросов по student_id
    requests_dict = {r.student_id: r for r in all_requests}
    
    result = []
    
    for student in all_students:
        request = requests_dict.get(student.id)
        
        student_info = {
            "id": student.id,
            "full_name": student.full_name,
            "is_registered": student.is_registered,
            "telegram_id": student.telegram_id,
            "code_requested": request is not None,
            "grade": request.grade if request else None,
            "code": request.code if request else None,
            "requested_at": request.requested_at.isoformat() if request else None,
            "screenshot_submitted": request.screenshot_submitted if request else False,
            "screenshot_path": request.screenshot_path if request else None,
            "screenshot_submitted_at": request.screenshot_submitted_at.isoformat() if (request and request.screenshot_submitted_at) else None
        }
        
        result.append(student_info)
    
    # Сортируем: сначала те, кто запросил коды
    result.sort(key=lambda x: (not x["code_requested"], x["full_name"]))
    
    return result


@router.get("/missing-screenshots")
async def get_missing_screenshots(
    session: AsyncSession = Depends(get_async_session)
) -> List[Dict]:
    """
    Получить список учеников, которые не прислали скриншоты
    """
    # Получаем активную сессию
    active_session = await crud.get_active_session(session)
    
    if not active_session:
        raise HTTPException(status_code=404, detail="Нет активной сессии")
    
    # Получаем запросы без скриншотов
    requests = await crud.get_requests_without_screenshot(session, active_session.id)
    
    return [
        {
            "student_id": r.student_id,
            "full_name": r.student.full_name,
            "telegram_id": r.student.telegram_id,
            "grade": r.grade,
            "code": r.code,
            "requested_at": r.requested_at.isoformat()
        }
        for r in requests
    ]


@router.get("/screenshot/{request_id}")
async def get_screenshot_info(
    request_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Получить информацию о скриншоте для конкретного запроса
    """
    from sqlalchemy import select
    from database.models import CodeRequest
    
    result = await session.execute(
        select(CodeRequest).where(CodeRequest.id == request_id)
    )
    request = result.scalar_one_or_none()
    
    if not request:
        raise HTTPException(status_code=404, detail="Запрос не найден")
    
    if not request.screenshot_submitted:
        raise HTTPException(status_code=404, detail="Скриншот не был прислан")
    
    return {
        "student_name": request.student.full_name,
        "screenshot_path": request.screenshot_path,
        "submitted_at": request.screenshot_submitted_at.isoformat()
    }
