from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from database.database import get_async_session
from database.models import (
    Student, OlympiadSession, Grade8Code, Grade9Code,
    CodeRequest, Reminder, OlympiadCode, OlympiadStage
)

router = APIRouter(prefix="/api/monitoring", tags=["Monitoring"])


@router.get("/dashboard")
async def get_dashboard_stats(
    session: AsyncSession = Depends(get_async_session)
):
    """Статистика для дашборда"""

    # Активный этап
    result = await session.execute(
        select(OlympiadStage).where(OlympiadStage.is_active == True)
    )
    active_stage = result.scalar_one_or_none()

    active_stage_data = None
    if active_stage:
        active_stage_data = {
            "id": active_stage.id,
            "name": active_stage.name,
            "code": active_stage.code,
            "description": active_stage.description
        }

    # Ученики
    result = await session.execute(select(func.count(Student.id)))
    total_students = result.scalar()

    result = await session.execute(
        select(func.count(Student.id)).where(Student.is_registered == True)
    )
    registered_students = result.scalar()

    # Активная сессия
    result = await session.execute(
        select(OlympiadSession).where(OlympiadSession.is_active == True)
    )
    active_session = result.scalar_one_or_none()

    active_session_data = None
    if active_session:
        # Статистика по активной сессии (используем универсальную таблицу)
        result = await session.execute(
            select(func.count(OlympiadCode.id)).where(
                OlympiadCode.session_id == active_session.id
            )
        )
        total_codes = result.scalar()

        result = await session.execute(
            select(func.count(OlympiadCode.id)).where(
                and_(
                    OlympiadCode.session_id == active_session.id,
                    OlympiadCode.is_issued == True
                )
            )
        )
        issued_codes = result.scalar()

        result = await session.execute(
            select(func.count(CodeRequest.id)).where(
                and_(
                    CodeRequest.session_id == active_session.id,
                    CodeRequest.screenshot_submitted == True
                )
            )
        )
        screenshots = result.scalar()

        active_session_data = {
            "id": active_session.id,
            "subject": active_session.subject,
            "date": active_session.date.isoformat(),
            "total_codes": total_codes,
            "issued_codes": issued_codes,
            "screenshots": screenshots
        }

    # Всего сессий
    result = await session.execute(select(func.count(OlympiadSession.id)))
    total_sessions = result.scalar()

    return {
        "active_stage": active_stage_data,
        "students": {
            "total": total_students,
            "registered": registered_students,
            "not_registered": total_students - registered_students
        },
        "active_session": active_session_data,
        "total_sessions": total_sessions
    }


@router.get("/sessions/{session_id}/details")
async def get_session_details(
    session_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    """Детальная информация о сессии"""
    
    # Получаем сессию
    result = await session.execute(
        select(OlympiadSession).where(OlympiadSession.id == session_id)
    )
    olympiad = result.scalar_one_or_none()
    
    if not olympiad:
        return {"error": "Сессия не найдена"}
    
    # Коды 8 класса
    result = await session.execute(
        select(Grade8Code).where(Grade8Code.session_id == session_id)
    )
    codes8 = result.scalars().all()
    
    assigned = len([c for c in codes8 if c.student_id])
    issued = len([c for c in codes8 if c.is_issued])
    
    # Запросы
    result = await session.execute(
        select(CodeRequest).where(CodeRequest.session_id == session_id)
    )
    requests = result.scalars().all()
    
    with_screenshot = len([r for r in requests if r.screenshot_submitted])
    
    return {
        "session": {
            "id": olympiad.id,
            "subject": olympiad.subject,
            "date": olympiad.date.isoformat(),
            "is_active": olympiad.is_active
        },
        "codes": {
            "total": len(codes8),
            "assigned": assigned,
            "unassigned": len(codes8) - assigned,
            "issued": issued
        },
        "requests": {
            "total": len(requests),
            "with_screenshot": with_screenshot,
            "without_screenshot": len(requests) - with_screenshot
        }
    }


@router.get("/students/without-codes")
async def get_students_without_codes(
    session: AsyncSession = Depends(get_async_session)
):
    """Ученики без назначенных кодов"""
    
    # Получаем активную сессию
    result = await session.execute(
        select(OlympiadSession).where(OlympiadSession.is_active == True)
    )
    active_session = result.scalar_one_or_none()
    
    if not active_session:
        return {"message": "Нет активной сессии", "students": []}
    
    # Все зарегистрированные ученики
    result = await session.execute(
        select(Student).where(Student.is_registered == True)
    )
    all_students = result.scalars().all()
    
    # Ученики с кодами
    result = await session.execute(
        select(Grade8Code.student_id).where(
            and_(
                Grade8Code.session_id == active_session.id,
                Grade8Code.student_id != None
            )
        )
    )
    students_with_codes = {row[0] for row in result.fetchall()}
    
    # Без кодов
    students_without = [
        {
            "id": s.id,
            "full_name": s.full_name,
            "telegram_id": s.telegram_id
        }
        for s in all_students
        if s.id not in students_with_codes
    ]
    
    return {
        "session": active_session.subject,
        "count": len(students_without),
        "students": students_without
    }


@router.get("/recent-activity")
async def get_recent_activity(
    limit: int = 20,
    session: AsyncSession = Depends(get_async_session)
):
    """Последняя активность"""

    # Последние запросы кодов
    result = await session.execute(
        select(CodeRequest)
        .order_by(CodeRequest.requested_at.desc())
        .limit(limit)
    )
    requests = result.scalars().all()

    activity = []
    for req in requests:
        student = await session.get(Student, req.student_id)
        olympiad = await session.get(OlympiadSession, req.session_id)

        activity.append({
            "type": "code_request",
            "student": student.full_name if student else "Неизвестен",
            "subject": olympiad.subject if olympiad else "Неизвестен",
            "timestamp": req.requested_at.isoformat() if req.requested_at else None,
            "screenshot": req.screenshot_submitted
        })

    return {"activity": activity}


@router.get("/all-sessions")
async def get_all_sessions_stats(
    session: AsyncSession = Depends(get_async_session)
):
    """Статистика по всем олимпиадам"""

    # Получаем все сессии
    result = await session.execute(
        select(OlympiadSession).order_by(OlympiadSession.date.desc())
    )
    sessions = result.scalars().all()

    sessions_data = []
    for sess in sessions:
        # Подсчитываем коды для этой сессии
        result = await session.execute(
            select(func.count(OlympiadCode.id)).where(
                OlympiadCode.session_id == sess.id
            )
        )
        total_codes = result.scalar() or 0

        # Подсчитываем выданные коды
        result = await session.execute(
            select(func.count(OlympiadCode.id)).where(
                and_(
                    OlympiadCode.session_id == sess.id,
                    OlympiadCode.is_issued == True
                )
            )
        )
        issued_codes = result.scalar() or 0

        # Подсчитываем запросы кодов
        result = await session.execute(
            select(func.count(CodeRequest.id)).where(
                CodeRequest.session_id == sess.id
            )
        )
        code_requests = result.scalar() or 0

        # Подсчитываем скриншоты
        result = await session.execute(
            select(func.count(CodeRequest.id)).where(
                and_(
                    CodeRequest.session_id == sess.id,
                    CodeRequest.screenshot_submitted == True
                )
            )
        )
        screenshots = result.scalar() or 0

        sessions_data.append({
            "id": sess.id,
            "subject": sess.subject,
            "date": sess.date.isoformat(),
            "stage": sess.stage,
            "class_number": sess.class_number,
            "is_active": sess.is_active,
            "total_codes": total_codes,
            "issued_codes": issued_codes,
            "code_requests": code_requests,
            "screenshots": screenshots
        })

    return {"sessions": sessions_data}


@router.get("/active-session/participants")
async def get_active_session_participants(
    session: AsyncSession = Depends(get_async_session)
):
    """Получить участников текущей активной олимпиады с их статусами"""

    # Получаем активную сессию
    result = await session.execute(
        select(OlympiadSession).where(OlympiadSession.is_active == True)
    )
    active_session = result.scalar_one_or_none()

    if not active_session:
        return {
            "session": None,
            "participants": []
        }

    # Получаем всех учеников, которые запросили код для этой сессии
    result = await session.execute(
        select(CodeRequest)
        .where(CodeRequest.session_id == active_session.id)
        .order_by(CodeRequest.requested_at.desc())
    )
    requests = result.scalars().all()

    participants = []
    seen_students = set()

    for req in requests:
        if req.student_id in seen_students:
            continue
        seen_students.add(req.student_id)

        student = await session.get(Student, req.student_id)
        if not student:
            continue

        participants.append({
            "student_id": student.id,
            "full_name": student.full_name,
            "class_display": f"{student.class_number}{student.parallel or ''}" if student.class_number else "-",
            "requested_at": req.requested_at.isoformat() if req.requested_at else None,
            "code": req.code,
            "screenshot_submitted": req.screenshot_submitted,
            "screenshot_submitted_at": req.screenshot_submitted_at.isoformat() if req.screenshot_submitted_at else None
        })

    return {
        "session": {
            "id": active_session.id,
            "subject": active_session.subject,
            "date": active_session.date.isoformat(),
            "stage": active_session.stage
        },
        "participants": participants,
        "total_participants": len(participants)
    }