from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import os

# Импортируем новые роутеры
from api.routers import students, codes, monitoring, admin, dashboard, notifications

# Создаем приложение
app = FastAPI(
    title="Olympus Bot API v2",
    description="Расширенный API для управления олимпиадами с веб-дашбордом",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутеры
app.include_router(students.router)
app.include_router(codes.router)
app.include_router(monitoring.router)
app.include_router(admin.router)
app.include_router(notifications.router)

# Создаем директории если их нет
os.makedirs("admin_panel/static", exist_ok=True)
os.makedirs("admin_panel/templates", exist_ok=True)

# Статические файлы и шаблоны
app.mount("/static", StaticFiles(directory="admin_panel/static"), name="static")
templates = Jinja2Templates(directory="admin_panel/templates")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Главная страница - полнофункциональная админ-панель v2"""
    return templates.TemplateResponse(
        "dashboard_v2.html",
        {"request": request}
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