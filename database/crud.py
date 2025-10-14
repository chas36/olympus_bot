from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload
from database.models import (
    Student, OlympiadSession, Grade8Code, Grade9Code,
    CodeRequest, Reminder, OlympiadCode, Grade8ReserveCode, moscow_now
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
        student.registered_at = moscow_now()
        await session.commit()
        await session.refresh(student)
    
    return student


async def get_all_students(session: AsyncSession) -> List[Student]:
    """Получает всех учеников"""
    result = await session.execute(select(Student))
    return result.scalars().all()


async def get_student_by_id(
    session: AsyncSession,
    student_id: int
) -> Optional[Student]:
    """Получает ученика по ID"""
    result = await session.execute(
        select(Student).where(Student.id == student_id)
    )
    return result.scalar_one_or_none()


async def delete_student_by_id(
    session: AsyncSession,
    student_id: int
) -> bool:
    """Удаляет ученика по ID"""
    from sqlalchemy import delete

    result = await session.execute(
        delete(Student).where(Student.id == student_id)
    )
    await session.commit()
    return result.rowcount > 0


async def get_students_by_class(
    session: AsyncSession,
    class_number: int
) -> List[Student]:
    """Получает всех учеников определенного класса"""
    result = await session.execute(
        select(Student).where(Student.class_number == class_number)
    )
    return result.scalars().all()


async def delete_students_by_class(
    session: AsyncSession,
    class_number: int
) -> int:
    """Удаляет всех учеников определенного класса"""
    from sqlalchemy import delete, update, select
    from .models import Grade8Code, Grade9Code, CodeRequest, OlympiadCode, Grade8ReserveCode

    # Получаем ID всех студентов в этом классе
    result = await session.execute(
        select(Student.id).where(Student.class_number == class_number)
    )
    student_ids = [row[0] for row in result.fetchall()]

    if not student_ids:
        return 0

    # Удаляем/обновляем связанные записи
    # 1. Удаляем запросы кодов
    await session.execute(
        delete(CodeRequest).where(CodeRequest.student_id.in_(student_ids))
    )

    # 2. Удаляем записи Grade8Code
    await session.execute(
        delete(Grade8Code).where(Grade8Code.student_id.in_(student_ids))
    )

    # 3. Обнуляем assigned_student_id в Grade9Code
    await session.execute(
        update(Grade9Code)
        .where(Grade9Code.assigned_student_id.in_(student_ids))
        .values(assigned_student_id=None, is_used=False, assigned_at=None)
    )

    # 4. Обнуляем student_id в OlympiadCode
    await session.execute(
        update(OlympiadCode)
        .where(OlympiadCode.student_id.in_(student_ids))
        .values(student_id=None, is_assigned=False, assigned_at=None)
    )

    # 5. Обнуляем used_by_student_id в Grade8ReserveCode
    await session.execute(
        update(Grade8ReserveCode)
        .where(Grade8ReserveCode.used_by_student_id.in_(student_ids))
        .values(used_by_student_id=None, is_used=False, used_at=None)
    )

    # 6. Теперь можно безопасно удалить студентов
    result = await session.execute(
        delete(Student).where(Student.class_number == class_number)
    )
    await session.commit()
    return result.rowcount


async def clear_all_students(session: AsyncSession) -> int:
    """Удаляет всех учеников из базы данных"""
    from sqlalchemy import delete

    result = await session.execute(delete(Student))
    await session.commit()
    return result.rowcount


async def get_all_classes(session: AsyncSession) -> List[int]:
    """Получает список всех уникальных классов"""
    result = await session.execute(
        select(Student.class_number)
        .where(Student.class_number.isnot(None))
        .distinct()
        .order_by(Student.class_number)
    )
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


async def get_all_sessions(session: AsyncSession) -> List[OlympiadSession]:
    """Получает все сессии олимпиад"""
    result = await session.execute(
        select(OlympiadSession).order_by(OlympiadSession.date.desc())
    )
    return result.scalars().all()


async def delete_session_by_id(
    session: AsyncSession,
    session_id: int
) -> bool:
    """Удаляет сессию олимпиады по ID (вместе со всеми кодами)"""
    from sqlalchemy import delete

    result = await session.execute(
        delete(OlympiadSession).where(OlympiadSession.id == session_id)
    )
    await session.commit()
    return result.rowcount > 0


async def delete_all_sessions(session: AsyncSession) -> int:
    """Удаляет все сессии олимпиад (вместе со всеми кодами)"""
    from sqlalchemy import delete
    from .models import Grade8Code, Grade9Code, CodeRequest, Reminder

    # Сначала удаляем все связанные записи
    # 1. Удаляем напоминания
    await session.execute(delete(Reminder))

    # 2. Удаляем запросы кодов
    await session.execute(delete(CodeRequest))

    # 3. Удаляем коды 8 класса
    await session.execute(delete(Grade8Code))

    # 4. Удаляем коды 9 класса
    await session.execute(delete(Grade9Code))

    # 5. Теперь можно безопасно удалить все сессии
    # (OlympiadCode и Grade8ReserveCode удалятся автоматически через CASCADE)
    result = await session.execute(delete(OlympiadSession))
    await session.commit()
    return result.rowcount


async def activate_session(
    session: AsyncSession,
    session_id: int
) -> Optional[OlympiadSession]:
    """Активирует сессию (деактивирует все остальные)"""
    # Деактивируем все сессии
    await deactivate_all_sessions(session)

    # Активируем нужную
    result = await session.execute(
        select(OlympiadSession).where(OlympiadSession.id == session_id)
    )
    olympiad_session = result.scalar_one_or_none()

    if olympiad_session:
        olympiad_session.is_active = True
        await session.commit()
        await session.refresh(olympiad_session)

    return olympiad_session


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
        code.issued_at = moscow_now()
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
        code.assigned_at = moscow_now()
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
        request.screenshot_submitted_at = moscow_now()
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


# ==================== UNIVERSAL OLYMPIAD CODES (5-11 grades) ====================

async def get_assigned_code_for_student(
    session: AsyncSession,
    student_id: int,
    session_id: int,
    class_number: int
) -> Optional[OlympiadCode]:
    """
    Получает распределенный код для ученика (Вариант 1)

    Используется когда коды были предварительно распределены скриптом
    """
    result = await session.execute(
        select(OlympiadCode).where(
            and_(
                OlympiadCode.student_id == student_id,
                OlympiadCode.session_id == session_id,
                OlympiadCode.class_number == class_number,
                OlympiadCode.is_assigned == True
            )
        )
    )
    return result.scalar_one_or_none()


async def get_available_code_for_class(
    session: AsyncSession,
    session_id: int,
    class_number: int
) -> Optional[OlympiadCode]:
    """
    Получает первый доступный код для класса (Вариант 2)

    Используется для выдачи кодов по запросу без предварительного распределения
    """
    result = await session.execute(
        select(OlympiadCode).where(
            and_(
                OlympiadCode.session_id == session_id,
                OlympiadCode.class_number == class_number,
                OlympiadCode.is_issued == False
            )
        ).limit(1)
    )
    return result.scalar_one_or_none()


async def mark_code_issued(
    session: AsyncSession,
    code_id: int,
    student_id: Optional[int] = None
):
    """Помечает код как выданный"""
    result = await session.execute(
        select(OlympiadCode).where(OlympiadCode.id == code_id)
    )
    code = result.scalar_one_or_none()

    if code:
        code.is_issued = True
        code.issued_at = moscow_now()
        if student_id and not code.student_id:
            code.student_id = student_id
        await session.commit()


async def count_available_codes_for_class(
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
                OlympiadCode.is_issued == False
            )
        )
    )
    return result.scalar() or 0


async def get_available_reserve_code_for_grade8(
    session: AsyncSession,
    session_id: int,
    class_parallel: str
) -> Optional[Grade8ReserveCode]:
    """
    Получает доступный резервный код для 8 класса

    Args:
        class_parallel: например "8А", "8Б", "8В"
    """
    result = await session.execute(
        select(Grade8ReserveCode).where(
            and_(
                Grade8ReserveCode.session_id == session_id,
                Grade8ReserveCode.class_parallel == class_parallel,
                Grade8ReserveCode.is_used == False
            )
        ).limit(1)
    )
    return result.scalar_one_or_none()


async def mark_reserve_code_used(
    session: AsyncSession,
    code_id: int,
    student_id: int
):
    """Помечает резервный код как использованный"""
    result = await session.execute(
        select(Grade8ReserveCode).where(Grade8ReserveCode.id == code_id)
    )
    code = result.scalar_one_or_none()

    if code:
        code.is_used = True
        code.used_by_student_id = student_id
        code.used_at = moscow_now()
        await session.commit()


async def count_available_reserve_codes_for_grade8(
    session: AsyncSession,
    session_id: int,
    class_parallel: str
) -> int:
    """Считает доступные резервные коды для параллели 8 класса"""
    result = await session.execute(
        select(func.count(Grade8ReserveCode.id)).where(
            and_(
                Grade8ReserveCode.session_id == session_id,
                Grade8ReserveCode.class_parallel == class_parallel,
                Grade8ReserveCode.is_used == False
            )
        )
    )
    return result.scalar() or 0
