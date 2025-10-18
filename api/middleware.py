"""
Middleware для проверки авторизации API
"""

from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session
import logging

from database.database import SessionLocal
from database.models import Session as DBSession, moscow_now

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware для проверки авторизации пользователей

    Публичные пути (доступны без авторизации):
    - /api/auth/* - эндпоинты авторизации
    - /static/* - статические файлы
    - /login - страница входа
    - /favicon.svg - иконка
    - /health - health check
    - /api/info - информация об API
    - /docs, /redoc, /openapi.json - документация API

    Все остальные пути требуют авторизации
    """

    # Публичные пути, не требующие авторизации
    PUBLIC_PATHS = [
        "/api/auth/",
        "/static/",
        "/login",
        "/favicon.svg",
        "/health",
        "/api/info",
        "/docs",
        "/redoc",
        "/openapi.json",
    ]

    # Точные пути (требуют точного совпадения)
    EXACT_PUBLIC_PATHS = [
        "/",  # Главная страница (сама проверяет авторизацию внутри)
    ]

    async def dispatch(self, request: Request, call_next):
        # Проверяем, является ли путь публичным
        path = request.url.path

        # Разрешаем доступ к публичным путям (startswith)
        if any(path.startswith(public_path) for public_path in self.PUBLIC_PATHS):
            return await call_next(request)

        # Разрешаем доступ к точным путям (exact match)
        if path in self.EXACT_PUBLIC_PATHS:
            return await call_next(request)

        # Проверяем токен сессии
        session_token = request.cookies.get("session_token")

        if not session_token:
            # Если это API запрос, возвращаем 401
            if path.startswith("/api/"):
                raise HTTPException(status_code=401, detail="Не авторизован")
            # Если это веб-страница, редиректим на логин
            return RedirectResponse(url="/login", status_code=302)

        # Проверяем сессию в БД
        db = SessionLocal()
        try:
            db_session = db.query(DBSession).filter(
                DBSession.session_token == session_token,
                DBSession.expires_at > moscow_now()
            ).first()

            if not db_session:
                # Сессия истекла или недействительна
                if path.startswith("/api/"):
                    raise HTTPException(status_code=401, detail="Сессия истекла")
                return RedirectResponse(url="/login", status_code=302)

            # Обновляем время последней активности
            db_session.last_activity = moscow_now()
            db.commit()

            # Добавляем информацию о пользователе в request state
            request.state.user_id = db_session.user_id
            request.state.session_id = db_session.id

            logger.debug(f"Пользователь {db_session.user_id} авторизован для {path}")

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Ошибка при проверке авторизации: {e}")
            if path.startswith("/api/"):
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")
            return RedirectResponse(url="/login", status_code=302)
        finally:
            db.close()

        return await call_next(request)
