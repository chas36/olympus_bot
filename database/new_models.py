"""
Новые модели для универсальной системы кодов (5-11 классы)

Заменяют Grade8Code и Grade9Code на универсальную модель OlympiadCode
"""
from datetime import datetime
from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from database.models import Base


class OlympiadCode(Base):
    """
    Универсальная таблица кодов для всех классов (5-11)

    Поддерживает два режима работы:
    1. Предварительное распределение (is_assigned) - Вариант 1
    2. Выдача по запросу (is_issued) - Вариант 2
    """
    __tablename__ = "olympiad_codes"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("olympiad_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    class_number = Column(Integer, nullable=False, index=True)  # 5-11
    code = Column(String(100), nullable=False, index=True)

    # Распределение (Вариант 1: скрипт)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="SET NULL"), nullable=True, index=True)
    is_assigned = Column(Boolean, default=False, index=True)  # Распределен скриптом
    assigned_at = Column(DateTime, nullable=True)

    # Выдача (Вариант 2: по запросу)
    is_issued = Column(Boolean, default=False)  # Выдан ученику через бота
    issued_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    session = relationship("OlympiadSession", back_populates="universal_codes")
    student = relationship("Student", back_populates="assigned_codes")

    # Constraints
    __table_args__ = (
        CheckConstraint('class_number >= 5 AND class_number <= 11', name='valid_class_number'),
    )

    def __repr__(self):
        return f"<OlympiadCode(id={self.id}, class={self.class_number}, code='{self.code}', assigned={self.is_assigned}, issued={self.is_issued})>"


class Grade8ReserveCode(Base):
    """
    Дополнительные коды из пула 9 класса для 8-классников

    Эти коды:
    - Берутся из нераспределенных кодов 9 класса
    - Распределяются по 8 классам (8А, 8Б и т.д.)
    - Не персонализированы (общий пул класса)
    - Выдаются по запросу любому ученику класса
    """
    __tablename__ = "grade8_reserve_codes"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("olympiad_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    class_parallel = Column(String(10), nullable=False, index=True)  # "8А", "8Б", "8В" и т.д.
    code = Column(String(100), nullable=False)

    is_used = Column(Boolean, default=False, index=True)
    used_by_student_id = Column(Integer, ForeignKey("students.id", ondelete="SET NULL"), nullable=True)
    used_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    session = relationship("OlympiadSession", back_populates="grade8_reserve_codes")
    used_by = relationship("Student", back_populates="used_reserve_codes")

    def __repr__(self):
        return f"<Grade8ReserveCode(id={self.id}, class={self.class_parallel}, code='{self.code}', used={self.is_used})>"


# Добавить к существующим моделям в database/models.py:

"""
В Student добавить:
    assigned_codes = relationship("OlympiadCode", back_populates="student")
    used_reserve_codes = relationship("Grade8ReserveCode", back_populates="used_by")

В OlympiadSession добавить:
    universal_codes = relationship("OlympiadCode", back_populates="session", cascade="all, delete-orphan")
    grade8_reserve_codes = relationship("Grade8ReserveCode", back_populates="session", cascade="all, delete-orphan")
"""
