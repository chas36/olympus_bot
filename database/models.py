from datetime import datetime, timezone, timedelta
from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

# Московский часовой пояс (UTC+3)
MOSCOW_TZ = timezone(timedelta(hours=3))

def moscow_now():
    """Возвращает текущее время в московском часовом поясе (naive datetime для совместимости с БД)"""
    # Возвращаем naive datetime в московском времени
    return datetime.now(MOSCOW_TZ).replace(tzinfo=None)


class OlympiadStage(Base):
    """Модель этапа олимпиады (школьный, муниципальный и т.д.)"""
    __tablename__ = "olympiad_stages"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)  # "Школьный этап", "Муниципальный этап"
    code = Column(String(50), unique=True, nullable=False, index=True)  # "school", "municipal"
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=False)  # Активен ли этап в данный момент
    created_at = Column(DateTime, default=moscow_now)

    # Relationships
    sessions = relationship("OlympiadSession", back_populates="stage_ref")

    def __repr__(self):
        return f"<OlympiadStage(id={self.id}, name='{self.name}', code='{self.code}', active={self.is_active})>"


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
    notifications_enabled = Column(Boolean, default=True)  # Включены ли уведомления для ученика
    created_at = Column(DateTime, default=moscow_now)
    registered_at = Column(DateTime, nullable=True)

    # Relationships
    grade8_codes = relationship("Grade8Code", back_populates="student")
    code_requests = relationship("CodeRequest", back_populates="student")
    assigned_grade9_codes = relationship("Grade9Code", back_populates="assigned_student")
    # Universal codes system (5-11 grades)
    assigned_codes = relationship("OlympiadCode", back_populates="student")
    used_reserve_codes = relationship("Grade8ReserveCode", back_populates="used_by")

    def __repr__(self):
        return f"<Student(id={self.id}, name='{self.full_name}', class={self.class_number}{self.parallel or ''}, registered={self.is_registered})>"


class OlympiadSession(Base):
    """Модель сессии олимпиады для конкретного класса"""
    __tablename__ = "olympiad_sessions"

    id = Column(Integer, primary_key=True, index=True)
    subject = Column(String(100), nullable=False, index=True)  # Название предмета
    class_number = Column(Integer, nullable=True, index=True)  # Класс (4-11), может быть NULL если коды для разных классов
    date = Column(DateTime, nullable=False, index=True)  # Дата проведения из CSV
    stage = Column(String(50), nullable=True)  # Этап (DEPRECATED: использовать stage_id)
    stage_id = Column(Integer, ForeignKey("olympiad_stages.id"), nullable=True, index=True)  # Ссылка на этап
    upload_time = Column(DateTime, default=moscow_now)
    is_active = Column(Boolean, default=False)  # По умолчанию неактивна
    uploaded_file_name = Column(String(255), nullable=True)
    notification_sent = Column(Boolean, default=False)  # Отправлено ли уведомление об активации
    notification_scheduled_for = Column(DateTime, nullable=True)  # Время запланированной отправки уведомления

    # Relationships
    stage_ref = relationship("OlympiadStage", back_populates="sessions")
    grade8_codes = relationship("Grade8Code", back_populates="session", cascade="all, delete-orphan")
    grade9_codes = relationship("Grade9Code", back_populates="session", cascade="all, delete-orphan")
    code_requests = relationship("CodeRequest", back_populates="session")
    # Universal codes system (5-11 grades)
    universal_codes = relationship("OlympiadCode", back_populates="session", cascade="all, delete-orphan")
    grade8_reserve_codes = relationship("Grade8ReserveCode", back_populates="session", cascade="all, delete-orphan")

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
    requested_at = Column(DateTime, default=moscow_now)
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
    sent_at = Column(DateTime, default=moscow_now)
    reminder_type = Column(String(50), default="screenshot")  # Тип напоминания

    # Relationships
    request = relationship("CodeRequest", back_populates="reminders")

    def __repr__(self):
        return f"<Reminder(id={self.id}, sent_at={self.sent_at})>"


# ====================================================================
# Universal Codes System (5-11 grades)
# ====================================================================


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

    created_at = Column(DateTime, default=moscow_now)

    # Relationships
    session = relationship("OlympiadSession", back_populates="universal_codes")
    student = relationship("Student", back_populates="assigned_codes")

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

    created_at = Column(DateTime, default=moscow_now)

    # Relationships
    session = relationship("OlympiadSession", back_populates="grade8_reserve_codes")
    used_by = relationship("Student", back_populates="used_reserve_codes")

    def __repr__(self):
        return f"<Grade8ReserveCode(id={self.id}, class={self.class_parallel}, code='{self.code}', used={self.is_used})>"


class NotificationSettings(Base):
    """Глобальные настройки уведомлений системы"""
    __tablename__ = "notification_settings"

    id = Column(Integer, primary_key=True, index=True)
    notifications_enabled = Column(Boolean, default=True)  # Глобальное включение/выключение уведомлений
    olympiad_notifications_enabled = Column(Boolean, default=True)  # Уведомления об активации олимпиад
    updated_at = Column(DateTime, default=moscow_now, onupdate=moscow_now)

    def __repr__(self):
        return f"<NotificationSettings(id={self.id}, enabled={self.notifications_enabled}, olympiad_notif={self.olympiad_notifications_enabled})>"


# ====================================================================
# Authentication System
# ====================================================================


class User(Base):
    """Пользователи системы (администраторы, учителя)"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String(50), unique=True, nullable=False, index=True)
    username = Column(String(100), nullable=True)  # Telegram username
    full_name = Column(String(200), nullable=True)  # Полное имя из Telegram
    role = Column(String(50), default='viewer', nullable=False)  # admin, teacher, viewer
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=moscow_now)
    last_login = Column(DateTime, nullable=True)

    # Relationships
    auth_tokens = relationship("AuthToken", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, telegram_id='{self.telegram_id}', role='{self.role}', active={self.is_active})>"


class AuthToken(Base):
    """Временные токены авторизации (одноразовые ссылки)"""
    __tablename__ = "auth_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token = Column(String(100), unique=True, nullable=False, index=True)  # Уникальный токен
    expires_at = Column(DateTime, nullable=False, index=True)  # Время истечения (15 минут)
    is_used = Column(Boolean, default=False)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=moscow_now)

    # Relationships
    user = relationship("User", back_populates="auth_tokens")

    def __repr__(self):
        return f"<AuthToken(id={self.id}, token='{self.token[:8]}...', used={self.is_used}, expires={self.expires_at})>"


class Session(Base):
    """Пользовательские сессии (после авторизации)"""
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_token = Column(String(100), unique=True, nullable=False, index=True)  # JWT или случайная строка
    expires_at = Column(DateTime, nullable=False, index=True)  # Время истечения (7 дней)
    last_activity = Column(DateTime, default=moscow_now)
    created_at = Column(DateTime, default=moscow_now)
    user_agent = Column(String(500), nullable=True)  # Для безопасности
    ip_address = Column(String(50), nullable=True)  # Для безопасности

    # Relationships
    user = relationship("User", back_populates="sessions")

    def __repr__(self):
        return f"<Session(id={self.id}, user_id={self.user_id}, expires={self.expires_at})>"
