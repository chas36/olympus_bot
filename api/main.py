from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import os

# Импортируем новые роутеры
from api.routers import students, codes, monitoring, admin, dashboard, notifications, screenshots, auth
from api.routers.auth import get_current_user, get_db
from database.models import User
from api.middleware import AuthMiddleware

# Создаем приложение
app = FastAPI(
    title="Olympus Bot API v2",
    description="Расширенный API для управления олимпиадами с веб-дашбордом",
    version="2.0.0"
)

# Включение/выключение защиты API (для тестирования можно отключить)
ENABLE_API_AUTH = os.getenv("ENABLE_API_AUTH", "false").lower() == "true"

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth middleware (опциональный, управляется через переменную окружения)
if ENABLE_API_AUTH:
    app.add_middleware(AuthMiddleware)
    print("🔒 API защищен: AuthMiddleware активирован")
else:
    print("⚠️  API НЕ защищен: AuthMiddleware отключен (для включения установите ENABLE_API_AUTH=true)")

# Подключаем роутеры
app.include_router(auth.router)  # Авторизация первой для приоритета
app.include_router(students.router)
app.include_router(codes.router)
app.include_router(monitoring.router)
app.include_router(admin.router)
app.include_router(notifications.router)
app.include_router(screenshots.router)

# Создаем директории если их нет
os.makedirs("admin_panel/static", exist_ok=True)
os.makedirs("admin_panel/templates", exist_ok=True)

# Статические файлы и шаблоны
app.mount("/static", StaticFiles(directory="admin_panel/static"), name="static")
templates = Jinja2Templates(directory="admin_panel/templates")


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Страница авторизации"""
    return templates.TemplateResponse(
        "login.html",
        {"request": request}
    )


@app.get("/")
async def root(request: Request, db: Session = Depends(get_db)):
    """
    Главная страница - полнофункциональная админ-панель v2
    ВРЕМЕННО БЕЗ АВТОРИЗАЦИИ
    """
    # ВРЕМЕННО: авторизация отключена
    # user = get_current_user(request, db)
    # if not user:
    #     return RedirectResponse(url="/login", status_code=302)

    # Отображаем панель управления без проверки авторизации
    return templates.TemplateResponse(
        "dashboard_v2.html",
        {
            "request": request,
            "user": None  # Временно без пользователя
        }
    )


@app.get("/health")
async def health_check():
    """Проверка работоспособности"""
    return {
        "status": "ok",
        "version": "2.0.0",
        "message": "Olympus Bot API v2 is running"
    }


@app.get("/api/info")
async def api_info():
    """Информация об API"""
    return {
        "name": "Olympus Bot API",
        "version": "2.0.0",
        "features": [
            "Управление учениками",
            "Загрузка из Excel и CSV",
            "Автоматическое резервирование кодов 9→8",
            "Мониторинг в реальном времени",
            "Экспорт данных"
        ]
    }


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    
    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        reload=True
    )