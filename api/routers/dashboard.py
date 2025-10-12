"""
Роутер для веб-дашборда администратора
"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="", tags=["Dashboard"])

templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """
    Главная страница - дашборд администратора
    """
    return templates.TemplateResponse("dashboard.html", {"request": request})


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_alt(request: Request):
    """
    Альтернативный URL для дашборда
    """
    return templates.TemplateResponse("dashboard.html", {"request": request})
