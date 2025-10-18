"""
Утилиты для работы с этапами олимпиад
"""

from sqlalchemy.orm import Session
from database.models import OlympiadStage, OlympiadSession
from typing import Optional
import os


def get_active_stage(db: Session) -> Optional[OlympiadStage]:
    """
    Получить активный этап олимпиады

    Args:
        db: Сессия базы данных

    Returns:
        OlympiadStage: Активный этап или None
    """
    return db.query(OlympiadStage).filter(
        OlympiadStage.is_active == True
    ).first()


def get_stage_by_code(db: Session, code: str) -> Optional[OlympiadStage]:
    """
    Получить этап по коду

    Args:
        db: Сессия базы данных
        code: Код этапа (school, municipal и т.д.)

    Returns:
        OlympiadStage: Этап или None
    """
    return db.query(OlympiadStage).filter(
        OlympiadStage.code == code
    ).first()


def get_all_stages(db: Session) -> list[OlympiadStage]:
    """
    Получить все этапы

    Args:
        db: Сессия базы данных

    Returns:
        list[OlympiadStage]: Список всех этапов
    """
    return db.query(OlympiadStage).order_by(OlympiadStage.id).all()


def activate_stage(db: Session, stage_id: int) -> bool:
    """
    Активировать этап (деактивирует все остальные)

    Args:
        db: Сессия базы данных
        stage_id: ID этапа для активации

    Returns:
        bool: True если успешно, False если этап не найден
    """
    # Деактивируем все этапы
    db.query(OlympiadStage).update({OlympiadStage.is_active: False})

    # Активируем выбранный этап
    stage = db.query(OlympiadStage).filter(OlympiadStage.id == stage_id).first()
    if not stage:
        return False

    stage.is_active = True
    db.commit()
    return True


def get_active_session_for_stage(db: Session, stage_id: int) -> Optional[OlympiadSession]:
    """
    Получить активную сессию для указанного этапа

    Args:
        db: Сессия базы данных
        stage_id: ID этапа

    Returns:
        OlympiadSession: Активная сессия или None
    """
    return db.query(OlympiadSession).filter(
        OlympiadSession.stage_id == stage_id,
        OlympiadSession.is_active == True
    ).first()


class StageContext:
    """
    Контекст этапа олимпиады для удобной работы
    """

    def __init__(self, db: Session, stage_code: Optional[str] = None):
        """
        Инициализация контекста этапа

        Args:
            db: Сессия базы данных
            stage_code: Код этапа (если None, используется активный этап)
        """
        self.db = db

        if stage_code:
            self.stage = get_stage_by_code(db, stage_code)
        else:
            self.stage = get_active_stage(db)

        if not self.stage:
            raise ValueError(f"Stage not found: {stage_code or 'active stage'}")

    def get_active_session(self) -> Optional[OlympiadSession]:
        """Получить активную сессию для текущего этапа"""
        return get_active_session_for_stage(self.db, self.stage.id)

    def get_all_sessions(self) -> list[OlympiadSession]:
        """Получить все сессии для текущего этапа"""
        return self.db.query(OlympiadSession).filter(
            OlympiadSession.stage_id == self.stage.id
        ).all()

    def is_active(self) -> bool:
        """Проверить, активен ли текущий этап"""
        return self.stage.is_active

    @property
    def code(self) -> str:
        """Код этапа"""
        return self.stage.code

    @property
    def name(self) -> str:
        """Название этапа"""
        return self.stage.name
