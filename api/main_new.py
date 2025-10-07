from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

# Импортируем новые роутеры
from api.routers import students, codes, monitoring
import os

# Создаем приложение FastAPI
app = FastAPI(
    title="Olympus Bot API v2",
    description="Обновленный API для управления олимпиадами с поддержкой всех классов (4-11)",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем новые роутеры
app.include_router(students.router)
app.include_router(codes.router)
app.include_router(monitoring.router)

# Настройка шаблонов и статики
templates = Jinja2Templates(directory="admin_panel/templates")

# Создаем статические папки если их нет
os.makedirs("admin_panel/static", exist_ok=True)
os.makedirs("screenshots", exist_ok=True)

app.mount("/static", StaticFiles(directory="admin_panel/static"), name="static")
app.mount("/screenshots", StaticFiles(directory="screenshots"), name="screenshots")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Главная страница - обновленная админ-панель"""
    return templates.TemplateResponse(
        "dashboard_v2.html",
        {"request": request}
    )


@app.get("/health")
async def health_check():
    """Проверка работоспособности API"""
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
            "Поддержка классов 4-11",
            "Многопредметность",
            "Два режима распределения кодов",
            "Резервирование кодов 9 класса для 8 классов",
            "Управление учениками (CRUD, перевод классов)",
            "Загрузка из Excel и CSV",
            "Экспорт по классам и архивами"
        ],
        "endpoints": {
            "students": "/admin/students",
            "codes": "/admin/codes",
            "monitoring": "/monitoring",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    
    uvicorn.run(
        "api.main_new:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )