"""
API роутер для управления настройками уведомлений
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, List
from database.database import get_async_session
from database.models import NotificationSettings, Student

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


class GlobalNotificationSettings(BaseModel):
    """Модель для глобальных настроек уведомлений"""
    notifications_enabled: bool


class StudentNotificationSettings(BaseModel):
    """Модель для настроек уведомлений ученика"""
    student_id: int
    notifications_enabled: bool


class BulkStudentNotificationSettings(BaseModel):
    """Модель для массового изменения настроек уведомлений учеников"""
    student_ids: List[int]
    notifications_enabled: bool


@router.get("/global")
async def get_global_notification_settings(session: AsyncSession = Depends(get_async_session)):
    """
    Получить глобальные настройки уведомлений
    """
    result = await session.execute(select(NotificationSettings))
    settings = result.scalar_one_or_none()

    if not settings:
        # Создаем настройки по умолчанию, если их нет
        settings = NotificationSettings(notifications_enabled=True)
        session.add(settings)
        await session.commit()
        await session.refresh(settings)

    return {
        "notifications_enabled": settings.notifications_enabled
    }


@router.put("/global")
async def update_global_notification_settings(
    settings_update: GlobalNotificationSettings,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Обновить глобальные настройки уведомлений
    """
    result = await session.execute(select(NotificationSettings))
    settings = result.scalar_one_or_none()

    if not settings:
        settings = NotificationSettings(notifications_enabled=settings_update.notifications_enabled)
        session.add(settings)
    else:
        settings.notifications_enabled = settings_update.notifications_enabled

    await session.commit()
    await session.refresh(settings)

    return {
        "message": "Глобальные настройки уведомлений обновлены",
        "notifications_enabled": settings.notifications_enabled
    }


@router.get("/student/{student_id}")
async def get_student_notification_settings(
    student_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Получить настройки уведомлений для конкретного ученика
    """
    result = await session.execute(select(Student).where(Student.id == student_id))
    student = result.scalar_one_or_none()

    if not student:
        raise HTTPException(status_code=404, detail="Ученик не найден")

    return {
        "student_id": student.id,
        "full_name": student.full_name,
        "notifications_enabled": student.notifications_enabled
    }


@router.put("/student/{student_id}")
async def update_student_notification_settings(
    student_id: int,
    settings_update: StudentNotificationSettings,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Обновить настройки уведомлений для конкретного ученика
    """
    result = await session.execute(select(Student).where(Student.id == student_id))
    student = result.scalar_one_or_none()

    if not student:
        raise HTTPException(status_code=404, detail="Ученик не найден")

    student.notifications_enabled = settings_update.notifications_enabled
    await session.commit()
    await session.refresh(student)

    return {
        "message": f"Настройки уведомлений для ученика {student.full_name} обновлены",
        "student_id": student.id,
        "notifications_enabled": student.notifications_enabled
    }


@router.put("/students/bulk")
async def update_bulk_student_notification_settings(
    settings_update: BulkStudentNotificationSettings,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Массово обновить настройки уведомлений для нескольких учеников
    """
    result = await session.execute(select(Student).where(Student.id.in_(settings_update.student_ids)))
    students = result.scalars().all()

    if not students:
        raise HTTPException(status_code=404, detail="Ученики не найдены")

    updated_count = 0
    for student in students:
        student.notifications_enabled = settings_update.notifications_enabled
        updated_count += 1

    await session.commit()

    return {
        "message": f"Настройки уведомлений обновлены для {updated_count} учеников",
        "updated_count": updated_count,
        "notifications_enabled": settings_update.notifications_enabled
    }


@router.put("/students/all")
async def update_all_students_notification_settings(
    notifications_enabled: bool,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Обновить настройки уведомлений для ВСЕХ учеников
    """
    result = await session.execute(select(Student))
    students = result.scalars().all()

    updated_count = 0
    for student in students:
        student.notifications_enabled = notifications_enabled
        updated_count += 1

    await session.commit()

    return {
        "message": f"Настройки уведомлений обновлены для всех {updated_count} учеников",
        "updated_count": updated_count,
        "notifications_enabled": notifications_enabled
    }


@router.get("/students/disabled")
async def get_students_with_disabled_notifications(session: AsyncSession = Depends(get_async_session)):
    """
    Получить список учеников с отключенными уведомлениями
    """
    result = await session.execute(select(Student).where(Student.notifications_enabled == False))
    students = result.scalars().all()

    return {
        "count": len(students),
        "students": [
            {
                "id": student.id,
                "full_name": student.full_name,
                "class_number": student.class_number,
                "parallel": student.parallel,
                "telegram_id": student.telegram_id
            }
            for student in students
        ]
    }
