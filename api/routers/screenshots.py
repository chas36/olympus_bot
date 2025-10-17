"""
API для работы со скриншотами
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from database.database import SessionLocal
from database.models import CodeRequest, Student, OlympiadSession
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import os

router = APIRouter(prefix="/api/screenshots", tags=["screenshots"])

SCREENSHOTS_FOLDER = os.getenv("SCREENSHOTS_FOLDER", "screenshots")


# Dependency для получения сессии БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class ScreenshotInfo(BaseModel):
    """Информация о скриншоте"""
    id: int
    student_id: int
    student_name: str
    student_class: str
    session_id: int
    subject: str
    olympiad_date: Optional[str]
    screenshot_path: str
    submitted_at: str
    file_exists: bool

    class Config:
        from_attributes = True


class ScreenshotsBySubject(BaseModel):
    """Скриншоты, сгруппированные по предмету"""
    subject: str
    session_id: int
    olympiad_date: Optional[str]
    screenshots: List[ScreenshotInfo]


@router.get("/list", response_model=List[ScreenshotInfo])
async def get_screenshots_list(
    session_id: Optional[int] = None,
    subject: Optional[str] = None,
    class_number: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Получить список всех скриншотов с фильтрацией

    Параметры:
    - session_id: ID сессии олимпиады (опционально)
    - subject: Предмет (опционально)
    - class_number: Класс (опционально)
    """
    query = db.query(CodeRequest).filter(
        CodeRequest.screenshot_submitted == True,
        CodeRequest.screenshot_path.isnot(None)
    ).options(
        joinedload(CodeRequest.student),
        joinedload(CodeRequest.session)
    )

    if session_id:
        query = query.filter(CodeRequest.session_id == session_id)

    if class_number:
        query = query.join(Student).filter(Student.class_number == class_number)

    if subject:
        query = query.join(OlympiadSession).filter(OlympiadSession.subject == subject)

    requests = query.order_by(CodeRequest.screenshot_submitted_at.desc()).all()

    result = []
    for req in requests:
        if not req.student or not req.session:
            continue

        student_class = f"{req.student.class_number}{req.student.parallel}" if req.student.parallel else str(req.student.class_number)

        # Проверяем существование файла
        full_path = os.path.join(SCREENSHOTS_FOLDER, req.screenshot_path)
        file_exists = os.path.exists(full_path)

        result.append(ScreenshotInfo(
            id=req.id,
            student_id=req.student.id,
            student_name=req.student.full_name,
            student_class=student_class,
            session_id=req.session.id,
            subject=req.session.subject,
            olympiad_date=req.session.date.isoformat() if req.session.date else None,
            screenshot_path=req.screenshot_path,
            submitted_at=req.screenshot_submitted_at.isoformat() if req.screenshot_submitted_at else "",
            file_exists=file_exists
        ))

    return result


@router.get("/by-subject", response_model=List[ScreenshotsBySubject])
async def get_screenshots_by_subject(db: Session = Depends(get_db)):
    """
    Получить скриншоты, сгруппированные по предметам
    """
    screenshots = await get_screenshots_list(db=db)

    # Группируем по предмету
    by_subject = {}
    for screenshot in screenshots:
        key = (screenshot.subject, screenshot.session_id)
        if key not in by_subject:
            by_subject[key] = {
                "subject": screenshot.subject,
                "session_id": screenshot.session_id,
                "olympiad_date": screenshot.olympiad_date,
                "screenshots": []
            }
        by_subject[key]["screenshots"].append(screenshot)

    return [ScreenshotsBySubject(**data) for data in by_subject.values()]


@router.get("/view/{request_id}")
async def view_screenshot(request_id: int, db: Session = Depends(get_db)):
    """
    Просмотр скриншота по ID запроса кода
    """
    request = db.query(CodeRequest).filter(
        CodeRequest.id == request_id,
        CodeRequest.screenshot_submitted == True
    ).first()

    if not request or not request.screenshot_path:
        raise HTTPException(status_code=404, detail="Скриншот не найден")

    file_path = os.path.join(SCREENSHOTS_FOLDER, request.screenshot_path)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Файл скриншота не найден на диске")

    return FileResponse(
        file_path,
        media_type="image/jpeg",
        filename=os.path.basename(request.screenshot_path)
    )


@router.get("/stats")
async def get_screenshots_stats(db: Session = Depends(get_db)):
    """
    Получить статистику по скриншотам
    """
    total_submitted = db.query(CodeRequest).filter(
        CodeRequest.screenshot_submitted == True
    ).count()

    total_expected = db.query(CodeRequest).count()

    # Статистика по предметам
    by_subject = db.query(
        OlympiadSession.subject,
        OlympiadSession.id
    ).join(CodeRequest).filter(
        CodeRequest.screenshot_submitted == True
    ).group_by(OlympiadSession.subject, OlympiadSession.id).all()

    subject_stats = {}
    for subject, session_id in by_subject:
        count = db.query(CodeRequest).filter(
            and_(
                CodeRequest.session_id == session_id,
                CodeRequest.screenshot_submitted == True
            )
        ).count()

        if subject not in subject_stats:
            subject_stats[subject] = 0
        subject_stats[subject] += count

    return {
        "total_submitted": total_submitted,
        "total_expected": total_expected,
        "submission_rate": round(total_submitted / total_expected * 100, 2) if total_expected > 0 else 0,
        "by_subject": subject_stats
    }
