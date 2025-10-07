from datetime import datetime
from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship, declarative_base
import enum

Base = declarative_base()


class DistributionMode(enum.Enum):
    """Режим распределения кодов"""
    PRE_DISTRIBUTED = "pre_distributed"  # Коды распределены заранее
    ON_DEMAND = "on_demand"  # Коды выдаются по запросу


class Student(Base):
    """Модель ученика"""
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(255), nullable=False, index=True)
    class_number = Column(Integer, nullable=False, index=True)  # 4-11
    telegram_id = Column(String(50), unique=True, nullable=True, index=True)
    registration_code = Column(String(50), unique=True, nullable=False, index=True)
    is_registered = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)  # Для "архивных" учеников
    created_at = Column(DateTime, default=datetime.utcnow)
    registered_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    codes = relationship("OlympiadCode", back_populates="student")
    code_requests = relationship("CodeRequest", back_populates="student")
    history = relationship("StudentHistory", back_populates="student")

    def __repr__(self):
        return f"<Student(id={self.id}, name='{self.full_name}', class={self.class_number})>"


class StudentHistory(Base):
    """История изменений ученика"""
    __tablename__ = "student_history"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    action = Column(String(50), nullable=False)  # created, updated, class_changed, deleted
    old_data = Column(Text, nullable=True)  # JSON со старыми данными
    new_data = Column(Text, nullable=True)  # JSON с новыми данными
    timestamp = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="history")


class OlympiadSession(Base):
    """Модель сессии олимпиады (один предмет в один день)"""
    __tablename__ = "olympiad_sessions"

    id = Column(Integer, primary_key=True, index=True)
    subject = Column(String(100), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)
    distribution_mode = Column(
        Enum(DistributionMode), 
        default=DistributionMode.ON_DEMAND,
        nullable=False
    )
    is_active = Column(Boolean, default=True)
    upload_time = Column(DateTime, default=datetime.utcnow)
    uploaded_file_name = Column(String(255), nullable=True)
    
    # Relationships
    codes = relationship("OlympiadCode", back_populates="session", cascade="all, delete-orphan")
    code_requests = relationship("CodeRequest", back_populates="session")

    def __repr__(self):
        return f"<OlympiadSession(id={self.id}, subject='{self.subject}', mode={self.distribution_mode.value})>"


class OlympiadCode(Base):
    """Универсальная таблица кодов для всех классов"""
    __tablename__ = "olympiad_codes"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("olympiad_sessions.id"), nullable=False)
    class_number = Column(Integer, nullable=False, index=True)  # 4-11
    code = Column(String(200), nullable=False, index=True)
    
    # Распределение
    student_id = Column(Integer, ForeignKey("students.id"), nullable=True)
    is_assigned = Column(Boolean, default=False)
    assigned_at = Column(DateTime, nullable=True)
    
    # Резервирование (для кодов 9 класса, используемых 8 классами)
    is_reserve = Column(Boolean, default=False)
    reserved_for_class = Column(Integer, nullable=True)  # Для какого класса зарезервирован
    
    # Использование
    is_issued = Column(Boolean, default=False)
    issued_at = Column(DateTime, nullable=True)

    # Relationships
    session = relationship("OlympiadSession", back_populates="codes")
    student = relationship("Student", back_populates="codes")

    def __repr__(self):
        return f"<OlympiadCode(id={self.id}, class={self.class_number}, assigned={self.is_assigned})>"


class CodeRequest(Base):
    """История запросов кодов учениками"""
    __tablename__ = "code_requests"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    session_id = Column(Integer, ForeignKey("olympiad_sessions.id"), nullable=False)
    code_id = Column(Integer, ForeignKey("olympiad_codes.id"), nullable=True)
    
    requested_at = Column(DateTime, default=datetime.utcnow)
    
    # Скриншот
    screenshot_submitted = Column(Boolean, default=False)
    screenshot_path = Column(String(500), nullable=True)
    screenshot_submitted_at = Column(DateTime, nullable=True)

    # Relationships
    student = relationship("Student", back_populates="code_requests")
    session = relationship("OlympiadSession", back_populates="code_requests")
    code = relationship("OlympiadCode")
    reminders = relationship("Reminder", back_populates="request", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<CodeRequest(id={self.id}, student_id={self.student_id})>"


class Reminder(Base):
    """История отправленных напоминаний"""
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("code_requests.id"), nullable=False)
    sent_at = Column(DateTime, default=datetime.utcnow)
    reminder_type = Column(String(50), default="screenshot")

    request = relationship("CodeRequest", back_populates="reminders")

    def __repr__(self):
        return f"<Reminder(id={self.id}, sent_at={self.sent_at})>"