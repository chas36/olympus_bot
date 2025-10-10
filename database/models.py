from datetime import datetime
from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class Student(Base):
    """Модель ученика"""
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(255), nullable=False, index=True)
    telegram_id = Column(String(50), unique=True, nullable=True, index=True)
    registration_code = Column(String(50), unique=True, nullable=False, index=True)
    is_registered = Column(Boolean, default=False)
    class_number = Column(Integer, nullable=True, index=True)  # Номер класса (4-11)
    parallel = Column(String(10), nullable=True)  # Параллель (А, Б, Т1, Т2, и т.д.)
    created_at = Column(DateTime, default=datetime.utcnow)
    registered_at = Column(DateTime, nullable=True)

    # Relationships
    grade8_codes = relationship("Grade8Code", back_populates="student")
    code_requests = relationship("CodeRequest", back_populates="student")
    assigned_grade9_codes = relationship("Grade9Code", back_populates="assigned_student")

    def __repr__(self):
        return f"<Student(id={self.id}, name='{self.full_name}', class={self.class_number}{self.parallel or ''}, registered={self.is_registered})>"


class OlympiadSession(Base):
    """Модель сессии олимпиады для конкретного класса"""
    __tablename__ = "olympiad_sessions"

    id = Column(Integer, primary_key=True, index=True)
    subject = Column(String(100), nullable=False, index=True)  # Название предмета
    class_number = Column(Integer, nullable=False, index=True)  # Класс (4-11)
    date = Column(DateTime, nullable=False, index=True)  # Дата проведения из CSV
    stage = Column(String(50), nullable=True)  # Этап (школьный, муниципальный, и т.д.)
    upload_time = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=False)  # По умолчанию неактивна
    uploaded_file_name = Column(String(255), nullable=True)

    # Relationships
    grade8_codes = relationship("Grade8Code", back_populates="session", cascade="all, delete-orphan")
    grade9_codes = relationship("Grade9Code", back_populates="session", cascade="all, delete-orphan")
    code_requests = relationship("CodeRequest", back_populates="session")

    def __repr__(self):
        return f"<OlympiadSession(id={self.id}, subject='{self.subject}', date={self.date}, stage='{self.stage}')>"


class Grade8Code(Base):
    """Коды для 8 класса (именные)"""
    __tablename__ = "grade8_codes"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=True)  # Изменили False на True
    session_id = Column(Integer, ForeignKey("olympiad_sessions.id"), nullable=False)
    code = Column(String(100), nullable=False, index=True)
    is_issued = Column(Boolean, default=False)
    issued_at = Column(DateTime, nullable=True)

    # Relationships
    student = relationship("Student", back_populates="grade8_codes")
    session = relationship("OlympiadSession", back_populates="grade8_codes")

    def __repr__(self):
        return f"<Grade8Code(id={self.id}, code='{self.code}', issued={self.is_issued})>"


class Grade9Code(Base):
    """Коды для 9 класса (пул кодов)"""
    __tablename__ = "grade9_codes"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("olympiad_sessions.id"), nullable=False)
    code = Column(String(100), nullable=False, index=True)
    assigned_student_id = Column(Integer, ForeignKey("students.id"), nullable=True)
    is_used = Column(Boolean, default=False)
    assigned_at = Column(DateTime, nullable=True)

    # Relationships
    session = relationship("OlympiadSession", back_populates="grade9_codes")
    assigned_student = relationship("Student", back_populates="assigned_grade9_codes")

    def __repr__(self):
        return f"<Grade9Code(id={self.id}, code='{self.code}', used={self.is_used})>"


class CodeRequest(Base):
    """История запросов кодов учениками"""
    __tablename__ = "code_requests"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=True)  # Изменили False на True
    session_id = Column(Integer, ForeignKey("olympiad_sessions.id"), nullable=False)
    grade = Column(Integer, nullable=False)  # 8 или 9
    code = Column(String(100), nullable=False)  # Копия кода для истории
    requested_at = Column(DateTime, default=datetime.utcnow)
    screenshot_submitted = Column(Boolean, default=False)
    screenshot_path = Column(String(500), nullable=True)
    screenshot_submitted_at = Column(DateTime, nullable=True)

    # Relationships
    student = relationship("Student", back_populates="code_requests")
    session = relationship("OlympiadSession", back_populates="code_requests")
    reminders = relationship("Reminder", back_populates="request", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<CodeRequest(id={self.id}, grade={self.grade}, screenshot={self.screenshot_submitted})>"


class Reminder(Base):
    """История отправленных напоминаний"""
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("code_requests.id"), nullable=False)
    sent_at = Column(DateTime, default=datetime.utcnow)
    reminder_type = Column(String(50), default="screenshot")  # Тип напоминания

    # Relationships
    request = relationship("CodeRequest", back_populates="reminders")

    def __repr__(self):
        return f"<Reminder(id={self.id}, sent_at={self.sent_at})>"
