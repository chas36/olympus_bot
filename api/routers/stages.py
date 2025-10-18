"""
API endpoints для управления этапами олимпиад
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from database.database import SessionLocal
from database.models import OlympiadStage
from utils.stage_context import (
    get_all_stages,
    get_active_stage,
    get_stage_by_code,
    activate_stage
)

router = APIRouter(prefix="/api/stages", tags=["stages"])


def get_db():
    """Dependency для получения сессии БД"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Pydantic models
class StageResponse(BaseModel):
    id: int
    name: str
    code: str
    description: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ActivateStageRequest(BaseModel):
    stage_id: int


@router.get("", response_model=List[StageResponse])
async def list_stages(db: Session = Depends(get_db)):
    """
    Получить список всех этапов олимпиад
    """
    stages = get_all_stages(db)
    return stages


@router.get("/active", response_model=Optional[StageResponse])
async def get_active(db: Session = Depends(get_db)):
    """
    Получить активный этап
    """
    stage = get_active_stage(db)
    if not stage:
        raise HTTPException(status_code=404, detail="No active stage found")
    return stage


@router.get("/{code}", response_model=StageResponse)
async def get_stage(code: str, db: Session = Depends(get_db)):
    """
    Получить этап по коду
    """
    stage = get_stage_by_code(db, code)
    if not stage:
        raise HTTPException(status_code=404, detail=f"Stage with code '{code}' not found")
    return stage


@router.post("/{stage_id}/activate")
async def activate(stage_id: int, db: Session = Depends(get_db)):
    """
    Активировать этап (деактивирует все остальные)
    """
    success = activate_stage(db, stage_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Stage with id {stage_id} not found")

    return {"message": "Stage activated successfully", "stage_id": stage_id}


@router.get("/{stage_id}/stats")
async def get_stage_stats(stage_id: int, db: Session = Depends(get_db)):
    """
    Получить статистику по этапу
    """
    from database.models import OlympiadSession, OlympiadCode

    stage = db.query(OlympiadStage).filter(OlympiadStage.id == stage_id).first()
    if not stage:
        raise HTTPException(status_code=404, detail=f"Stage with id {stage_id} not found")

    # Подсчет сессий
    total_sessions = db.query(OlympiadSession).filter(
        OlympiadSession.stage_id == stage_id
    ).count()

    active_sessions = db.query(OlympiadSession).filter(
        OlympiadSession.stage_id == stage_id,
        OlympiadSession.is_active == True
    ).count()

    # Подсчет кодов через сессии
    session_ids = [s.id for s in db.query(OlympiadSession.id).filter(
        OlympiadSession.stage_id == stage_id
    ).all()]

    total_codes = 0
    issued_codes = 0
    if session_ids:
        total_codes = db.query(OlympiadCode).filter(
            OlympiadCode.session_id.in_(session_ids)
        ).count()

        issued_codes = db.query(OlympiadCode).filter(
            OlympiadCode.session_id.in_(session_ids),
            OlympiadCode.is_used == True
        ).count()

    return {
        "stage": StageResponse.from_orm(stage),
        "stats": {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "total_codes": total_codes,
            "issued_codes": issued_codes,
            "available_codes": total_codes - issued_codes
        }
    }
