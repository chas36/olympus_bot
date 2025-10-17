"""
API endpoints для системы авторизации через Telegram
"""

from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
import secrets
import logging
import os

from database.database import SessionLocal
from database.models import User, AuthToken, Session as DBSession, moscow_now

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["authentication"])

BOT_USERNAME = os.getenv("BOT_USERNAME", "YourBotUsername")


def get_db():
    """Dependency для получения сессии БД"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Pydantic models
class LoginRequest(BaseModel):
    telegram_id: str


class LoginRequestResponse(BaseModel):
    token: str
    expires_at: str
    bot_link: str


class VerifyTokenRequest(BaseModel):
    token: str


class VerifyTokenResponse(BaseModel):
    session_token: str
    user: dict
    expires_at: str


class UserResponse(BaseModel):
    id: int
    telegram_id: str
    username: Optional[str]
    full_name: Optional[str]
    role: str
    is_active: bool


# Helper functions
def generate_token(length: int = 32) -> str:
    """Генерация случайного токена"""
    return secrets.token_urlsafe(length)


def get_current_user(request: Request, db: Session = Depends(get_db)) -> Optional[User]:
    """Получить текущего пользователя из сессии"""
    session_token = request.cookies.get("session_token")

    if not session_token:
        return None

    # Найти сессию
    db_session = db.query(DBSession).filter(
        DBSession.session_token == session_token,
        DBSession.expires_at > moscow_now()
    ).first()

    if not db_session:
        return None

    # Обновить последнюю активность
    db_session.last_activity = moscow_now()
    db.commit()

    # Получить пользователя
    user = db.query(User).filter(User.id == db_session.user_id).first()

    return user if user and user.is_active else None


def require_auth(request: Request, db: Session = Depends(get_db)) -> User:
    """Middleware для проверки авторизации (обязательная)"""
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется авторизация"
        )
    return user


# API Endpoints

@router.post("/request-login", response_model=LoginRequestResponse)
async def request_login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Генерация токена авторизации для пользователя

    Этот endpoint вызывается веб-панелью для создания ссылки авторизации.
    Пользователь должен перейти по этой ссылке в Telegram боте.
    """

    # Проверяем, существует ли пользователь
    user = db.query(User).filter(User.telegram_id == request.telegram_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден. Обратитесь к администратору."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Пользователь деактивирован"
        )

    # Генерируем токен
    token = generate_token()
    expires_at = moscow_now() + timedelta(minutes=15)

    # Сохраняем в БД
    auth_token = AuthToken(
        user_id=user.id,
        token=token,
        expires_at=expires_at
    )
    db.add(auth_token)
    db.commit()

    logger.info(f"Создан токен авторизации для пользователя {user.telegram_id}")

    return LoginRequestResponse(
        token=token,
        expires_at=expires_at.isoformat(),
        bot_link=f"https://t.me/{BOT_USERNAME}?start=auth_{token}"
    )


@router.post("/verify", response_model=VerifyTokenResponse)
async def verify_token(
    request: Request,
    verify_request: VerifyTokenRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Проверка токена авторизации и создание сессии

    Вызывается ботом после того, как пользователь подтвердил авторизацию.
    """

    # Ищем токен
    auth_token = db.query(AuthToken).filter(
        AuthToken.token == verify_request.token,
        AuthToken.is_used == False,
        AuthToken.expires_at > moscow_now()
    ).first()

    if not auth_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный или истекший токен"
        )

    # Помечаем токен как использованный
    auth_token.is_used = True
    auth_token.used_at = moscow_now()

    # Получаем пользователя
    user = db.query(User).filter(User.id == auth_token.user_id).first()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Пользователь не активен"
        )

    # Создаем сессию
    session_token = generate_token(64)
    expires_at = moscow_now() + timedelta(days=7)

    db_session = DBSession(
        user_id=user.id,
        session_token=session_token,
        expires_at=expires_at,
        user_agent=request.headers.get("User-Agent"),
        ip_address=request.client.host if request.client else None
    )
    db.add(db_session)

    # Обновляем время последнего входа
    user.last_login = moscow_now()

    db.commit()

    logger.info(f"Создана сессия для пользователя {user.telegram_id}")

    # Устанавливаем cookie с сессией
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        max_age=7 * 24 * 60 * 60,  # 7 дней
        samesite="lax"
    )

    return VerifyTokenResponse(
        session_token=session_token,
        user={
            "id": user.id,
            "telegram_id": user.telegram_id,
            "username": user.username,
            "full_name": user.full_name,
            "role": user.role
        },
        expires_at=expires_at.isoformat()
    )


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(require_auth)):
    """
    Получить информацию о текущем пользователе
    """
    return UserResponse(
        id=user.id,
        telegram_id=user.telegram_id,
        username=user.username,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active
    )


@router.post("/logout")
async def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    """
    Выход из системы (удаление сессии)
    """
    session_token = request.cookies.get("session_token")

    if session_token:
        # Удаляем сессию из БД
        db.query(DBSession).filter(DBSession.session_token == session_token).delete()
        db.commit()

        # Удаляем cookie
        response.delete_cookie("session_token")

        logger.info("Пользователь вышел из системы")

    return {"message": "Выход выполнен успешно"}


@router.get("/check")
async def check_auth(user: Optional[User] = Depends(get_current_user)):
    """
    Проверить авторизацию (без ошибки если не авторизован)
    """
    if user:
        return {
            "authenticated": True,
            "user": {
                "id": user.id,
                "telegram_id": user.telegram_id,
                "username": user.username,
                "full_name": user.full_name,
                "role": user.role
            }
        }
    else:
        return {"authenticated": False}
