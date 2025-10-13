from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload
from database.models import (
    Student, OlympiadSession, Grade8Code, Grade9Code, 
    CodeRequest, Reminder
)
from typing import Optional, List
from datetime import datetime


# ==================== STUDENTS ====================

async def create_student(
    session: AsyncSession,
    full_name: str,
    registration_code: str
) -> Student:
    """Создает нового ученика"""
    student = Student(
        full_name=full_name,
        registration_code=registration_code
    )
    session.add(student)
    await session.commit()
    await session.refresh(student)
    return student


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


async def get_all_students(session: AsyncSession) -> List[Student]:
    """Получает всех учеников"""
    result = await session.execute(select(Student))
    return result.scalars().all()


# ==================== OLYMPIAD SESSIONS ====================

async def create_olympiad_session(
    session: AsyncSession,
    subject: str,
    date: datetime,
    uploaded_file_name: str
) -> OlympiadSession:
    """Создает новую сессию олимпиады"""
    olympiad = OlympiadSession(
        subject=subject,
        date=date,
        uploaded_file_name=uploaded_file_name
    )
    session.add(olympiad)
    await session.commit()
    await session.refresh(olympiad)
    return olympiad


async def get_active_session(session: AsyncSession) -> Optional[OlympiadSession]:
    """Получает активную сессию олимпиады"""
    result = await session.execute(
        select(OlympiadSession)
        .where(OlympiadSession.is_active == True)
        .order_by(OlympiadSession.date.desc())
    )
    return result.scalar_one_or_none()


async def deactivate_all_sessions(session: AsyncSession):
    """Деактивирует все сессии"""
    result = await session.execute(select(OlympiadSession))
    sessions = result.scalars().all()
    
    for sess in sessions:
        sess.is_active = False
    
    await session.commit()


async def get_session_by_id(
    session: AsyncSession,
    session_id: int
) -> Optional[OlympiadSession]:
    """Получает сессию по ID"""
    result = await session.execute(
        select(OlympiadSession).where(OlympiadSession.id == session_id)
    )
    return result.scalar_one_or_none()


# ==================== GRADE 8 CODES ====================

async def create_grade8_code(
    session: AsyncSession,
    student_id: int,
    session_id: int,
    code: str
) -> Grade8Code:
    """Создает код для 8 класса"""
    grade8_code = Grade8Code(
        student_id=student_id,
        session_id=session_id,
        code=code
    )
    session.add(grade8_code)
    await session.commit()
    await session.refresh(grade8_code)
    return grade8_code


async def get_grade8_code_for_student(
    session: AsyncSession,
    student_id: int,
    session_id: int
) -> Optional[Grade8Code]:
    """Получает код 8 класса для конкретного ученика в сессии"""
    result = await session.execute(
        select(Grade8Code).where(
            and_(
                Grade8Code.student_id == student_id,
                Grade8Code.session_id == session_id
            )
        )
    )
    return result.scalar_one_or_none()


async def mark_grade8_code_issued(
    session: AsyncSession,
    code_id: int
):
    """Помечает код 8 класса как выданный"""
    result = await session.execute(
        select(Grade8Code).where(Grade8Code.id == code_id)
    )
    code = result.scalar_one_or_none()
    
    if code:
        code.is_issued = True
        code.issued_at = datetime.utcnow()
        await session.commit()


# ==================== GRADE 9 CODES ====================

async def create_grade9_code(
    session: AsyncSession,
    session_id: int,
    code: str
) -> Grade9Code:
    """Создает код для 9 класса"""
    grade9_code = Grade9Code(
        session_id=session_id,
        code=code
    )
    session.add(grade9_code)
    await session.commit()
    await session.refresh(grade9_code)
    return grade9_code


async def get_available_grade9_code(
    session: AsyncSession,
    session_id: int
) -> Optional[Grade9Code]:
    """Получает свободный код 9 класса"""
    result = await session.execute(
        select(Grade9Code).where(
            and_(
                Grade9Code.session_id == session_id,
                Grade9Code.is_used == False
            )
        ).limit(1)
    )
    return result.scalar_one_or_none()


async def assign_grade9_code(
    session: AsyncSession,
    code_id: int,
    student_id: int
) -> Grade9Code:
    """Присваивает код 9 класса ученику"""
    result = await session.execute(
        select(Grade9Code).where(Grade9Code.id == code_id)
    )
    code = result.scalar_one_or_none()
    
    if code:
        code.assigned_student_id = student_id
        code.is_used = True
        code.assigned_at = datetime.utcnow()
        await session.commit()
        await session.refresh(code)
    
    return code


async def count_available_grade9_codes(
    session: AsyncSession,
    session_id: int
) -> int:
    """Считает доступные коды 9 класса"""
    result = await session.execute(
        select(func.count(Grade9Code.id)).where(
            and_(
                Grade9Code.session_id == session_id,
                Grade9Code.is_used == False
            )
        )
    )
    return result.scalar()


# ==================== CODE REQUESTS ====================

async def create_code_request(
    session: AsyncSession,
    student_id: int,
    session_id: int,
    grade: int,
    code: str
) -> CodeRequest:
    """Создает запись о запросе кода"""
    request = CodeRequest(
        student_id=student_id,
        session_id=session_id,
        grade=grade,
        code=code
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


async def get_reminders_for_request(
    session: AsyncSession,
    request_id: int
) -> List[Reminder]:
    """Получает все напоминания для запроса"""
    result = await session.execute(
        select(Reminder).where(Reminder.request_id == request_id)
    )
    return result.scalars().all()
