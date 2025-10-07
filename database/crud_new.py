from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload
from database.models import (
    Student, OlympiadSession, OlympiadCode, CodeRequest, 
    Reminder, DistributionMode
)
from typing import Optional, List
from datetime import datetime


# ==================== STUDENTS ====================

async def get_student_by_telegram_id(
    session: AsyncSession,
    telegram_id: str
) -> Optional[Student]:
    """Получает ученика по Telegram ID"""
    result = await session.execute(
        select(Student).where(Student.telegram_id == telegram_id)
    )
    return result.scalar_one_or_none()


async def get_student_by_registration_code(
    session: AsyncSession,
    code: str
) -> Optional[Student]:
    """Получает ученика по регистрационному коду"""
    result = await session.execute(
        select(Student).where(Student.registration_code == code)
    )
    return result.scalar_one_or_none()


async def register_student(
    session: AsyncSession,
    student_id: int,
    telegram_id: str
) -> Student:
    """Регистрирует ученика (привязывает Telegram ID)"""
    result = await session.execute(
        select(Student).where(Student.id == student_id)
    )
    student = result.scalar_one_or_none()
    
    if student:
        student.telegram_id = telegram_id
        student.is_registered = True
        student.registered_at = datetime.utcnow()
        await session.commit()
        await session.refresh(student)
    
    return student


async def get_all_students(
    session: AsyncSession,
    include_inactive: bool = False
) -> List[Student]:
    """Получает всех учеников"""
    query = select(Student)
    
    if not include_inactive:
        query = query.where(Student.is_active == True)
    
    result = await session.execute(query)
    return result.scalars().all()


async def get_students_by_class(
    session: AsyncSession,
    class_number: int,
    include_inactive: bool = False
) -> List[Student]:
    """Получает учеников конкретного класса"""
    query = select(Student).where(Student.class_number == class_number)
    
    if not include_inactive:
        query = query.where(Student.is_active == True)
    
    result = await session.execute(query)
    return result.scalars().all()


# ==================== OLYMPIAD SESSIONS ====================

async def get_active_session(session: AsyncSession) -> Optional[OlympiadSession]:
    """Получает активную сессию олимпиады"""
    result = await session.execute(
        select(OlympiadSession)
        .where(OlympiadSession.is_active == True)
        .order_by(OlympiadSession.date.desc())
    )
    return result.scalar_one_or_none()


async def get_active_sessions(session: AsyncSession) -> List[OlympiadSession]:
    """Получает все активные сессии олимпиад"""
    result = await session.execute(
        select(OlympiadSession)
        .where(OlympiadSession.is_active == True)
        .order_by(OlympiadSession.date.desc())
    )
    return result.scalars().all()


async def get_session_by_id(
    session: AsyncSession,
    session_id: int
) -> Optional[OlympiadSession]:
    """Получает сессию по ID"""
    result = await session.execute(
        select(OlympiadSession).where(OlympiadSession.id == session_id)
    )
    return result.scalar_one_or_none()


async def deactivate_all_sessions(session: AsyncSession):
    """Деактивирует все сессии"""
    result = await session.execute(select(OlympiadSession))
    sessions = result.scalars().all()
    
    for sess in sessions:
        sess.is_active = False
    
    await session.commit()


# ==================== OLYMPIAD CODES ====================

async def get_code_for_student(
    session: AsyncSession,
    student_id: int,
    session_id: int
) -> Optional[OlympiadCode]:
    """Получает код для конкретного ученика в сессии"""
    result = await session.execute(
        select(OlympiadCode).where(
            and_(
                OlympiadCode.student_id == student_id,
                OlympiadCode.session_id == session_id
            )
        )
    )
    return result.scalar_one_or_none()


async def get_available_codes_count(
    session: AsyncSession,
    session_id: int,
    class_number: int
) -> int:
    """Считает доступные коды для класса"""
    result = await session.execute(
        select(func.count(OlympiadCode.id)).where(
            and_(
                OlympiadCode.session_id == session_id,
                OlympiadCode.class_number == class_number,
                OlympiadCode.is_assigned == False
            )
        )
    )
    return result.scalar()


async def mark_code_issued(
    session: AsyncSession,
    code_id: int
):
    """Помечает код как выданный"""
    result = await session.execute(
        select(OlympiadCode).where(OlympiadCode.id == code_id)
    )
    code = result.scalar_one_or_none()
    
    if code:
        code.is_issued = True
        code.issued_at = datetime.utcnow()
        await session.commit()


# ==================== CODE REQUESTS ====================

async def create_code_request(
    session: AsyncSession,
    student_id: int,
    session_id: int,
    code_id: int
) -> CodeRequest:
    """Создает запись о запросе кода"""
    request = CodeRequest(
        student_id=student_id,
        session_id=session_id,
        code_id=code_id
    )
    session.add(request)
    await session.commit()
    await session.refresh(request)
    return request


async def get_code_request_for_student_in_session(
    session: AsyncSession,
    student_id: int,
    session_id: int
) -> Optional[CodeRequest]:
    """Получает запрос кода ученика в текущей сессии"""
    result = await session.execute(
        select(CodeRequest).where(
            and_(
                CodeRequest.student_id == student_id,
                CodeRequest.session_id == session_id
            )
        )
    )
    return result.scalar_one_or_none()


async def mark_screenshot_submitted(
    session: AsyncSession,
    request_id: int,
    screenshot_path: str
):
    """Помечает, что скриншот прислан"""
    result = await session.execute(
        select(CodeRequest).where(CodeRequest.id == request_id)
    )
    request = result.scalar_one_or_none()
    
    if request:
        request.screenshot_submitted = True
        request.screenshot_path = screenshot_path
        request.screenshot_submitted_at = datetime.utcnow()
        await session.commit()


async def get_requests_without_screenshot(
    session: AsyncSession,
    session_id: int
) -> List[CodeRequest]:
    """Получает запросы без скриншотов для сессии"""
    result = await session.execute(
        select(CodeRequest)
        .where(
            and_(
                CodeRequest.session_id == session_id,
                CodeRequest.screenshot_submitted == False
            )
        )
        .options(selectinload(CodeRequest.student))
    )
    return result.scalars().all()


async def get_all_requests_for_session(
    session: AsyncSession,
    session_id: int
) -> List[CodeRequest]:
    """Получает все запросы для сессии"""
    result = await session.execute(
        select(CodeRequest)
        .where(CodeRequest.session_id == session_id)
        .options(selectinload(CodeRequest.student))
    )
    return result.scalars().all()


# ==================== REMINDERS ====================

async def create_reminder(
    session: AsyncSession,
    request_id: int,
    reminder_type: str = "screenshot"
) -> Reminder:
    """Создает запись о напоминании"""
    reminder = Reminder(
        request_id=request_id,
        reminder_type=reminder_type
    )
    session.add(reminder)
    await session.commit()
    await session.refresh(reminder)
    return reminder


# ==================== STATISTICS ====================

async def get_session_statistics(
    session: AsyncSession,
    session_id: int
) -> dict:
    """Получает статистику по сессии"""
    olympiad = await get_session_by_id(session, session_id)
    
    if not olympiad:
        return None
    
    # Всего кодов
    total_codes_result = await session.execute(
        select(func.count(OlympiadCode.id)).where(
            OlympiadCode.session_id == session_id
        )
    )
    total_codes = total_codes_result.scalar()
    
    # Распределенных кодов
    assigned_codes_result = await session.execute(
        select(func.count(OlympiadCode.id)).where(
            and_(
                OlympiadCode.session_id == session_id,
                OlympiadCode.is_assigned == True
            )
        )
    )
    assigned_codes = assigned_codes_result.scalar()
    
    # Выданных кодов
    issued_codes_result = await session.execute(
        select(func.count(OlympiadCode.id)).where(
            and_(
                OlympiadCode.session_id == session_id,
                OlympiadCode.is_issued == True
            )
        )
    )
    issued_codes = issued_codes_result.scalar()
    
    # Скриншотов
    screenshots_result = await session.execute(
        select(func.count(CodeRequest.id)).where(
            and_(
                CodeRequest.session_id == session_id,
                CodeRequest.screenshot_submitted == True
            )
        )
    )
    screenshots = screenshots_result.scalar()
    
    # Запросов всего
    requests_result = await session.execute(
        select(func.count(CodeRequest.id)).where(
            CodeRequest.session_id == session_id
        )
    )
    total_requests = requests_result.scalar()
    
    return {
        "session_id": session_id,
        "subject": olympiad.subject,
        "date": olympiad.date,
        "distribution_mode": olympiad.distribution_mode.value,
        "codes": {
            "total": total_codes,
            "assigned": assigned_codes,
            "issued": issued_codes,
            "available": total_codes - assigned_codes
        },
        "requests": {
            "total": total_requests,
            "with_screenshot": screenshots,
            "without_screenshot": total_requests - screenshots
        }
    }