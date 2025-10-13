from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from database.database import get_async_session
from database import crud
from utils.auth import generate_multiple_codes
from typing import List, Dict
from pydantic import BaseModel

router = APIRouter(prefix="/api/admin", tags=["Admin"])


class StudentCreate(BaseModel):
    """Модель для создания ученика"""
    full_name: str


class BulkStudentsCreate(BaseModel):
    """Модель для массового создания учеников"""
    students: List[str]  # Список ФИО


@router.post("/students")
async def create_student(
    student_data: StudentCreate,
    session: AsyncSession = Depends(get_async_session)
) -> Dict:
    """
    Создать нового ученика с регистрационным кодом
    """
    # Генерируем регистрационный код
    registration_code = generate_multiple_codes(1)[0]
    
    # Создаем ученика
    student = await crud.create_student(
        session,
        full_name=student_data.full_name,
        registration_code=registration_code
    )
    
    return {
        "id": student.id,
        "full_name": student.full_name,
        "registration_code": student.registration_code,
        "is_registered": student.is_registered
    }


@router.post("/students/bulk")
async def create_students_bulk(
    data: BulkStudentsCreate,
    session: AsyncSession = Depends(get_async_session)
) -> Dict:
    """
    Массовое создание учеников
    """
    # Генерируем коды для всех учеников
    codes = generate_multiple_codes(len(data.students))
    
    created_students = []
    
    for full_name, code in zip(data.students, codes):
        student = await crud.create_student(
            session,
            full_name=full_name.strip(),
            registration_code=code
        )
        created_students.append({
            "id": student.id,
            "full_name": student.full_name,
            "registration_code": student.registration_code
        })
    
    return {
        "success": True,
        "count": len(created_students),
        "students": created_students
    }


@router.get("/students")
async def get_all_students(
    session: AsyncSession = Depends(get_async_session)
) -> List[Dict]:
    """
    Получить список всех учеников
    """
    students = await crud.get_all_students(session)
    
    return [
        {
            "id": s.id,
            "full_name": s.full_name,
            "registration_code": s.registration_code,
            "is_registered": s.is_registered,
            "telegram_id": s.telegram_id,
            "created_at": s.created_at.isoformat(),
            "registered_at": s.registered_at.isoformat() if s.registered_at else None
        }
        for s in students
    ]


@router.get("/students/unregistered")
async def get_unregistered_students(
    session: AsyncSession = Depends(get_async_session)
) -> List[Dict]:
    """
    Получить список незарегистрированных учеников
    """
    students = await crud.get_all_students(session)
    unregistered = [s for s in students if not s.is_registered]
    
    return [
        {
            "id": s.id,
            "full_name": s.full_name,
            "registration_code": s.registration_code,
            "created_at": s.created_at.isoformat()
        }
        for s in unregistered
    ]


@router.post("/students/{student_id}/regenerate-code")
async def regenerate_registration_code(
    student_id: int,
    session: AsyncSession = Depends(get_async_session)
) -> Dict:
    """
    Перегенерировать регистрационный код для ученика
    (полезно если код был потерян или скомпрометирован)
    """
    from sqlalchemy import select, update
    from database.models import Student
    
    # Проверяем существование ученика
    result = await session.execute(
        select(Student).where(Student.id == student_id)
    )
    student = result.scalar_one_or_none()
    
    if not student:
        raise HTTPException(status_code=404, detail="Ученик не найден")
    
    if student.is_registered:
        raise HTTPException(
            status_code=400,
            detail="Нельзя перегенерировать код для зарегистрированного ученика"
        )
    
    # Генерируем новый код
    new_code = generate_multiple_codes(1)[0]
    
    # Обновляем код
    await session.execute(
        update(Student)
        .where(Student.id == student_id)
        .values(registration_code=new_code)
    )
    await session.commit()
    
    return {
        "success": True,
        "student_id": student_id,
        "full_name": student.full_name,
        "new_registration_code": new_code
    }


@router.get("/students/{student_id}")
async def get_student(
    student_id: int,
    session: AsyncSession = Depends(get_async_session)
) -> Dict:
    """
    Получить информацию об ученике по ID
    """
    student = await crud.get_student_by_id(session, student_id)

    if not student:
        raise HTTPException(status_code=404, detail="Ученик не найден")

    return {
        "id": student.id,
        "full_name": student.full_name,
        "class_number": student.class_number,
        "parallel": student.parallel,
        "registration_code": student.registration_code,
        "is_registered": student.is_registered,
        "telegram_id": student.telegram_id,
        "telegram_username": student.telegram_username,
        "created_at": student.created_at.isoformat(),
        "registered_at": student.registered_at.isoformat() if student.registered_at else None
    }


@router.delete("/students/{student_id}")
async def delete_student(
    student_id: int,
    force: bool = False,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Удалить ученика

    Args:
        student_id: ID ученика
        force: Принудительное удаление даже если ученик зарегистрирован
    """
    student = await crud.get_student_by_id(session, student_id)

    if not student:
        raise HTTPException(status_code=404, detail="Ученик не найден")

    if student.is_registered and not force:
        raise HTTPException(
            status_code=400,
            detail="Нельзя удалить зарегистрированного ученика без параметра force=true"
        )

    deleted = await crud.delete_student_by_id(session, student_id)

    if not deleted:
        raise HTTPException(status_code=500, detail="Не удалось удалить ученика")

    return {"success": True, "message": "Ученик удален", "student_id": student_id}


@router.delete("/students")
async def clear_all_students(
    confirm: str = "",
    session: AsyncSession = Depends(get_async_session)
):
    """
    Удалить всех учеников из базы данных

    ВНИМАНИЕ: Это действие необратимо!

    Args:
        confirm: Для подтверждения передайте строку "YES_DELETE_ALL"
    """
    if confirm != "YES_DELETE_ALL":
        raise HTTPException(
            status_code=400,
            detail="Для подтверждения удаления всех учеников передайте параметр confirm=YES_DELETE_ALL"
        )

    count = await crud.clear_all_students(session)

    return {
        "success": True,
        "deleted_count": count,
        "message": f"Удалено учеников: {count}"
    }


@router.get("/classes")
async def get_all_classes(
    session: AsyncSession = Depends(get_async_session)
) -> List[Dict]:
    """
    Получить список всех классов с количеством учеников
    """
    classes = await crud.get_all_classes(session)

    result = []
    for class_num in classes:
        students = await crud.get_students_by_class(session, class_num)
        result.append({
            "class_number": class_num,
            "total_students": len(students),
            "registered": sum(1 for s in students if s.is_registered),
            "unregistered": sum(1 for s in students if not s.is_registered)
        })

    return result


@router.get("/classes/{class_number}/students")
async def get_students_by_class(
    class_number: int,
    session: AsyncSession = Depends(get_async_session)
) -> List[Dict]:
    """
    Получить всех учеников определенного класса
    """
    students = await crud.get_students_by_class(session, class_number)

    return [
        {
            "id": s.id,
            "full_name": s.full_name,
            "class_number": s.class_number,
            "parallel": s.parallel,
            "registration_code": s.registration_code,
            "is_registered": s.is_registered,
            "telegram_id": s.telegram_id,
            "created_at": s.created_at.isoformat(),
            "registered_at": s.registered_at.isoformat() if s.registered_at else None
        }
        for s in students
    ]


@router.delete("/classes/{class_number}")
async def delete_class(
    class_number: int,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Удалить всех учеников определенного класса
    """
    # Проверяем есть ли ученики в этом классе
    students = await crud.get_students_by_class(session, class_number)

    if not students:
        raise HTTPException(status_code=404, detail=f"Класс {class_number} не найден или пуст")

    count = await crud.delete_students_by_class(session, class_number)

    return {
        "success": True,
        "class_number": class_number,
        "deleted_count": count,
        "message": f"Класс {class_number} удален. Удалено учеников: {count}"
    }


@router.post("/generate-codes")
async def generate_registration_codes(count: int = 10) -> Dict:
    """
    Сгенерировать регистрационные коды без привязки к ученикам
    (для печати и раздачи)
    """
    if count < 1 or count > 100:
        raise HTTPException(
            status_code=400,
            detail="Количество кодов должно быть от 1 до 100"
        )
    
    codes = generate_multiple_codes(count)
    
    return {
        "count": count,
        "codes": codes
    }


@router.get("/olympiads")
async def get_all_olympiads(
    session: AsyncSession = Depends(get_async_session)
) -> List[Dict]:
    """
    Получить список всех олимпиад
    """
    sessions = await crud.get_all_sessions(session)

    return [
        {
            "id": s.id,
            "subject": s.subject,
            "class_number": s.class_number,
            "date": s.date.isoformat(),
            "stage": s.stage,
            "is_active": s.is_active,
            "uploaded_file_name": s.uploaded_file_name,
            "upload_time": s.upload_time.isoformat()
        }
        for s in sessions
    ]


@router.delete("/olympiads/{session_id}")
async def delete_olympiad(
    session_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Удалить олимпиаду по ID (вместе со всеми кодами)
    """
    olympiad_session = await crud.get_session_by_id(session, session_id)

    if not olympiad_session:
        raise HTTPException(status_code=404, detail="Олимпиада не найдена")

    deleted = await crud.delete_session_by_id(session, session_id)

    if not deleted:
        raise HTTPException(status_code=500, detail="Не удалось удалить олимпиаду")

    return {
        "success": True,
        "session_id": session_id,
        "subject": olympiad_session.subject,
        "message": f"Олимпиада '{olympiad_session.subject}' удалена"
    }


@router.delete("/olympiads")
async def delete_all_olympiads(
    session: AsyncSession = Depends(get_async_session)
):
    """
    Удалить все олимпиады (вместе со всеми кодами)
    """
    count = await crud.delete_all_sessions(session)

    return {
        "success": True,
        "deleted_count": count,
        "message": f"Удалено олимпиад: {count}"
    }


@router.post("/olympiads/{session_id}/activate")
async def activate_olympiad(
    session_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Активировать олимпиаду (деактивирует все остальные)
    """
    olympiad_session = await crud.activate_session(session, session_id)

    if not olympiad_session:
        raise HTTPException(status_code=404, detail="Олимпиада не найдена")

    return {
        "success": True,
        "session_id": session_id,
        "subject": olympiad_session.subject,
        "is_active": olympiad_session.is_active,
        "message": f"Олимпиада '{olympiad_session.subject}' активирована"
    }


@router.get("/statistics/overview")
async def get_statistics_overview(
    session: AsyncSession = Depends(get_async_session)
) -> Dict:
    """
    Получить общую статистику системы
    """
    all_students = await crud.get_all_students(session)
    registered_students = [s for s in all_students if s.is_registered]
    all_sessions = await crud.get_all_sessions(session)
    active_session = await crud.get_active_session(session)
    classes = await crud.get_all_classes(session)

    # Статистика по классам
    classes_stats = []
    for class_num in classes:
        class_students = await crud.get_students_by_class(session, class_num)
        class_registered = sum(1 for s in class_students if s.is_registered)
        classes_stats.append({
            "class_number": class_num,
            "total": len(class_students),
            "registered": class_registered,
            "unregistered": len(class_students) - class_registered
        })

    return {
        "students": {
            "total": len(all_students),
            "registered": len(registered_students),
            "unregistered": len(all_students) - len(registered_students)
        },
        "olympiads": {
            "total": len(all_sessions),
            "active": 1 if active_session else 0,
            "inactive": len(all_sessions) - (1 if active_session else 0)
        },
        "classes": classes_stats,
        "active_olympiad": {
            "id": active_session.id,
            "subject": active_session.subject,
            "date": active_session.date.isoformat()
        } if active_session else None
    }


@router.get("/statistics/olympiad/{session_id}")
async def get_olympiad_statistics(
    session_id: int,
    session: AsyncSession = Depends(get_async_session)
) -> Dict:
    """
    Получить детальную статистику по олимпиаде
    """
    from sqlalchemy import select, func
    from database.models import Grade8Code, Grade9Code, CodeRequest

    olympiad = await crud.get_session_by_id(session, session_id)

    if not olympiad:
        raise HTTPException(status_code=404, detail="Олимпиада не найдена")

    # Статистика по кодам 8 класса
    grade8_total = await session.execute(
        select(func.count(Grade8Code.id)).where(Grade8Code.session_id == session_id)
    )
    grade8_issued = await session.execute(
        select(func.count(Grade8Code.id)).where(
            Grade8Code.session_id == session_id,
            Grade8Code.is_issued == True
        )
    )

    # Статистика по кодам 9 класса
    grade9_total = await session.execute(
        select(func.count(Grade9Code.id)).where(Grade9Code.session_id == session_id)
    )
    grade9_used = await session.execute(
        select(func.count(Grade9Code.id)).where(
            Grade9Code.session_id == session_id,
            Grade9Code.is_used == True
        )
    )

    # Статистика по запросам
    requests_total = await session.execute(
        select(func.count(CodeRequest.id)).where(CodeRequest.session_id == session_id)
    )
    screenshots = await session.execute(
        select(func.count(CodeRequest.id)).where(
            CodeRequest.session_id == session_id,
            CodeRequest.screenshot_submitted == True
        )
    )

    g8_total = grade8_total.scalar()
    g8_issued = grade8_issued.scalar()
    g9_total = grade9_total.scalar()
    g9_used = grade9_used.scalar()
    req_total = requests_total.scalar()
    scr_count = screenshots.scalar()

    return {
        "olympiad": {
            "id": olympiad.id,
            "subject": olympiad.subject,
            "class_number": olympiad.class_number,
            "date": olympiad.date.isoformat(),
            "stage": olympiad.stage,
            "is_active": olympiad.is_active
        },
        "codes_grade8": {
            "total": g8_total,
            "issued": g8_issued,
            "not_issued": g8_total - g8_issued
        },
        "codes_grade9": {
            "total": g9_total,
            "used": g9_used,
            "available": g9_total - g9_used
        },
        "requests": {
            "total": req_total,
            "with_screenshot": scr_count,
            "without_screenshot": req_total - scr_count,
            "completion_rate": int((scr_count / req_total) * 100) if req_total > 0 else 0
        }
    }


@router.get("/students/registered")
async def get_registered_students(
    session: AsyncSession = Depends(get_async_session)
) -> List[Dict]:
    """
    Получить список зарегистрированных учеников
    """
    all_students = await crud.get_all_students(session)
    students = [s for s in all_students if s.is_registered]

    return [
        {
            "id": s.id,
            "full_name": s.full_name,
            "class_number": s.class_number,
            "parallel": s.parallel,
            "telegram_id": s.telegram_id,
            "registered_at": s.registered_at.isoformat() if s.registered_at else None
        }
        for s in students
    ]


@router.get("/students/unregistered")
async def get_unregistered_students_api(
    session: AsyncSession = Depends(get_async_session)
) -> List[Dict]:
    """
    Получить список незарегистрированных учеников
    """
    all_students = await crud.get_all_students(session)
    students = [s for s in all_students if not s.is_registered]

    return [
        {
            "id": s.id,
            "full_name": s.full_name,
            "class_number": s.class_number,
            "parallel": s.parallel,
            "registration_code": s.registration_code,
            "created_at": s.created_at.isoformat()
        }
        for s in students
    ]


@router.post("/notifications/test")
async def send_test_notification() -> Dict:
    """
    Отправить тестовое уведомление всем администраторам
    """
    from utils.admin_notifications import notify_system_event
    from aiogram import Bot
    import os

    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        raise HTTPException(status_code=500, detail="BOT_TOKEN не настроен")

    bot = Bot(token=bot_token)

    try:
        await notify_system_event(
            bot,
            "Тестовое уведомление",
            "Система уведомлений работает корректно!"
        )
        await bot.session.close()
        return {"success": True, "message": "Уведомление отправлено"}
    except Exception as e:
        await bot.session.close()
        raise HTTPException(status_code=500, detail=f"Ошибка отправки: {str(e)}")


@router.get("/export/students")
async def export_students_csv(
    session: AsyncSession = Depends(get_async_session)
):
    """
    Экспорт списка учеников в CSV формат
    """
    import io
    import csv
    from fastapi.responses import StreamingResponse

    students = await crud.get_all_students(session)

    # Создаем CSV в памяти
    output = io.StringIO()
    writer = csv.writer(output)

    # Заголовки
    writer.writerow([
        "ID", "ФИО", "Регистрационный код",
        "Зарегистрирован", "Telegram ID", "Дата создания"
    ])

    # Данные
    for s in students:
        writer.writerow([
            s.id,
            s.full_name,
            s.registration_code,
            "Да" if s.is_registered else "Нет",
            s.telegram_id or "-",
            s.created_at.strftime("%Y-%m-%d %H:%M:%S")
        ])

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=students.csv"
        }
    )


@router.get("/export/students/excel")
async def export_students_excel(
    session: AsyncSession = Depends(get_async_session)
):
    """
    Экспорт списка учеников в Excel формат
    """
    from fastapi.responses import StreamingResponse
    from utils.excel_export import ExcelExporter

    students = await crud.get_all_students(session)

    students_data = [
        {
            "id": s.id,
            "full_name": s.full_name,
            "class_number": s.class_number,
            "parallel": s.parallel,
            "registration_code": s.registration_code,
            "is_registered": s.is_registered,
            "telegram_id": s.telegram_id,
            "created_at": s.created_at.isoformat(),
            "registered_at": s.registered_at.isoformat() if s.registered_at else None
        }
        for s in students
    ]

    try:
        excel_file = ExcelExporter.export_students(students_data)

        return StreamingResponse(
            excel_file,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": "attachment; filename=students.xlsx"
            }
        )
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="openpyxl не установлен. Используйте CSV экспорт."
        )


@router.get("/export/olympiads/excel")
async def export_olympiads_excel(
    session: AsyncSession = Depends(get_async_session)
):
    """
    Экспорт списка олимпиад в Excel формат
    """
    from fastapi.responses import StreamingResponse
    from utils.excel_export import ExcelExporter

    sessions = await crud.get_all_sessions(session)

    olympiads_data = [
        {
            "id": s.id,
            "subject": s.subject,
            "class_number": s.class_number,
            "date": s.date.isoformat(),
            "stage": s.stage,
            "is_active": s.is_active,
            "uploaded_file_name": s.uploaded_file_name,
            "upload_time": s.upload_time.isoformat()
        }
        for s in sessions
    ]

    try:
        excel_file = ExcelExporter.export_olympiads(olympiads_data)

        return StreamingResponse(
            excel_file,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": "attachment; filename=olympiads.xlsx"
            }
        )
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="openpyxl не установлен."
        )


@router.get("/export/statistics/excel")
async def export_statistics_excel(
    session: AsyncSession = Depends(get_async_session)
):
    """
    Экспорт статистики в Excel формат
    """
    from fastapi.responses import StreamingResponse
    from utils.excel_export import ExcelExporter

    all_students = await crud.get_all_students(session)
    registered = [s for s in all_students if s.is_registered]
    all_sessions = await crud.get_all_sessions(session)
    classes = await crud.get_all_classes(session)

    # Собираем статистику по классам
    classes_stats = []
    for class_num in classes:
        class_students = await crud.get_students_by_class(session, class_num)
        class_registered = sum(1 for s in class_students if s.is_registered)
        classes_stats.append({
            "class_number": class_num,
            "total": len(class_students),
            "registered": class_registered
        })

    stats = {
        "general": {
            "Всего учеников": len(all_students),
            "Зарегистрировано": len(registered),
            "Не зарегистрировано": len(all_students) - len(registered),
            "Всего олимпиад": len(all_sessions),
            "Активных олимпиад": sum(1 for s in all_sessions if s.is_active)
        },
        "classes": classes_stats
    }

    try:
        excel_file = ExcelExporter.export_statistics(stats)

        return StreamingResponse(
            excel_file,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": "attachment; filename=statistics.xlsx"
            }
        )
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="openpyxl не установлен."
        )
