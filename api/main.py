from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from api.routers import upload, monitoring, admin
import os

# Создаем приложение FastAPI
app = FastAPI(
    title="Olympus Bot API",
    description="API для управления олимпиадами",
    version="1.0.0"
)

# CORS middleware для возможности обращения из браузера
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутеры
app.include_router(upload.router)
app.include_router(monitoring.router)
app.include_router(admin.router)

# Настройка шаблонов и статики
templates = Jinja2Templates(directory="admin_panel/templates")
app.mount("/static", StaticFiles(directory="admin_panel/static"), name="static")

# Создаем папки если их нет
os.makedirs("admin_panel/templates", exist_ok=True)
os.makedirs("admin_panel/static", exist_ok=True)


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Главная страница"""
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request}
    )


@app.get("/health")
async def health_check():
    """Проверка работоспособности API"""
    return {"status": "ok", "message": "API is running"}


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    
    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )
