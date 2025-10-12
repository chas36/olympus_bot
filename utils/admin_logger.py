"""
Модуль для логирования действий администраторов
"""
from datetime import datetime
from loguru import logger
import json


class AdminActionLogger:
    """Класс для логирования действий администраторов"""

    @staticmethod
    def log_action(admin_id: int, admin_name: str, action: str, details: dict = None):
        """
        Логирует действие администратора

        Args:
            admin_id: Telegram ID администратора
            admin_name: Имя администратора
            action: Название действия
            details: Дополнительные детали действия
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "admin_id": admin_id,
            "admin_name": admin_name,
            "action": action,
            "details": details or {}
        }

        logger.info(
            f"[ADMIN ACTION] {admin_name} (ID: {admin_id}) | {action} | "
            f"Details: {json.dumps(details, ensure_ascii=False) if details else 'None'}"
        )

        return log_entry

    @staticmethod
    def log_student_action(admin_id: int, admin_name: str, action: str, student_id: int = None, student_name: str = None):
        """Логирует действие с учеником"""
        details = {}
        if student_id:
            details["student_id"] = student_id
        if student_name:
            details["student_name"] = student_name

        AdminActionLogger.log_action(admin_id, admin_name, action, details)

    @staticmethod
    def log_class_action(admin_id: int, admin_name: str, action: str, class_number: int, students_count: int = None):
        """Логирует действие с классом"""
        details = {
            "class_number": class_number
        }
        if students_count is not None:
            details["students_count"] = students_count

        AdminActionLogger.log_action(admin_id, admin_name, action, details)

    @staticmethod
    def log_olympiad_action(admin_id: int, admin_name: str, action: str, olympiad_id: int = None, olympiad_name: str = None):
        """Логирует действие с олимпиадой"""
        details = {}
        if olympiad_id:
            details["olympiad_id"] = olympiad_id
        if olympiad_name:
            details["olympiad_name"] = olympiad_name

        AdminActionLogger.log_action(admin_id, admin_name, action, details)

    @staticmethod
    def log_export(admin_id: int, admin_name: str, export_type: str, records_count: int = None):
        """Логирует экспорт данных"""
        details = {
            "export_type": export_type
        }
        if records_count is not None:
            details["records_count"] = records_count

        AdminActionLogger.log_action(admin_id, admin_name, f"export_{export_type}", details)
