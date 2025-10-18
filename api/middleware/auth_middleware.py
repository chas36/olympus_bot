"""
Middleware для проверки авторизации на API endpoints
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session
import logging

from database.database import SessionLocal
from database.models import Session as DBSession, User, moscow_now

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware для проверки авторизации пользователей

    Защищает все API endpoints кроме:
    - /login
    - /api/auth/*
    - /health
    - /static/*
    """

    # Публичные пути, не требующие авторизации
    PUBLIC_PATHS = [
        "/",  # Главная страница (сама проверяет авторизацию и редиректит на /login)
        "/login",
        "/api/auth/request-login",
        "/api/auth/verify",
        "/api/auth/check",
        "/health",
        "/api/info"
    ]

    # Префиксы путей, не требующие авторизации
    PUBLIC_PREFIXES = [
        "/static/",
        "/api/auth/"
    ]

    async def dispatch(self, request: Request, call_next):
        # Проверяем, является ли путь публичным
        if self.is_public_path(request.url.path):
            return await call_next(request)

        # Проверяем авторизацию для защищенных путей
        db = SessionLocal()
        try:
            session_token = request.cookies.get("session_token")

            if not session_token:
                return self.unauthorized_response("Требуется авторизация")

            # Проверяем сессию
            db_session = db.query(DBSession).filter(
                DBSession.session_token == session_token,
                DBSession.expires_at > moscow_now()
            ).first()

            if not db_session:
                return self.unauthorized_response("Недействительная или истекшая сессия")

            # Получаем пользователя
            user = db.query(User).filter(User.id == db_session.user_id).first()

            if not user or not user.is_active:
                return self.unauthorized_response("Пользователь не активен")

            # Обновляем последнюю активность
            db_session.last_activity = moscow_now()
            db.commit()

            # Добавляем пользователя в state для использования в handlers
            request.state.user = user

            # Логируем доступ (опционально, только для важных операций)
            if request.method in ["POST", "PUT", "DELETE"]:
                logger.info(
                    f"User {user.telegram_id} ({user.role}) accessed {request.method} {request.url.path}"
                )

            response = await call_next(request)
            return response

        except Exception as e:
            logger.error(f"Auth middleware error: {e}")
            return self.unauthorized_response("Ошибка проверки авторизации")

        finally:
            db.close()

    def is_public_path(self, path: str) -> bool:
        """Проверка, является ли путь публичным"""
        # Проверяем точные совпадения
        if path in self.PUBLIC_PATHS:
            return True

        # Проверяем префиксы
        for prefix in self.PUBLIC_PREFIXES:
            if path.startswith(prefix):
                return True

        return False

    def unauthorized_response(self, message: str) -> JSONResponse:
        """Возвращает ответ 401 Unauthorized"""
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": message}
        )
