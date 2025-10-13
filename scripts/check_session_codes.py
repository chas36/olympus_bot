"""
Проверка кодов для конкретной сессии
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from database.database import AsyncSessionLocal
from database.models import Grade8Code, Grade9Code, OlympiadSession
from sqlalchemy import select, and_, func


async def check_session_codes(session_id: int):
    """Проверить коды для сессии"""

    async with AsyncSessionLocal() as session:
        # Получаем сессию
        result = await session.execute(
            select(OlympiadSession).where(OlympiadSession.id == session_id)
        )
        olympiad = result.scalar_one_or_none()

        if not olympiad:
            print(f"❌ Сессия {session_id} не найдена!")
            return

        print(f"📚 Сессия: {olympiad.subject}")
        print(f"   ID: {olympiad.id}")
        print(f"   Активна: {olympiad.is_active}")
        print(f"   Дата: {olympiad.date}")

        # Коды 8 класса
        result = await session.execute(
            select(func.count(Grade8Code.id)).where(Grade8Code.session_id == session_id)
        )
        total_grade8 = result.scalar()

        result = await session.execute(
            select(func.count(Grade8Code.id)).where(
                and_(
                    Grade8Code.session_id == session_id,
                    Grade8Code.student_id.isnot(None)
                )
            )
        )
        assigned_grade8 = result.scalar()

        print(f"\n🔢 Коды 8 класса:")
        print(f"   Всего: {total_grade8}")
        print(f"   Привязано к ученикам: {assigned_grade8}")
        print(f"   Без привязки: {total_grade8 - assigned_grade8}")

        # Коды 9 класса
        result = await session.execute(
            select(func.count(Grade9Code.id)).where(Grade9Code.session_id == session_id)
        )
        total_grade9 = result.scalar()

        result = await session.execute(
            select(func.count(Grade9Code.id)).where(
                and_(
                    Grade9Code.session_id == session_id,
                    Grade9Code.is_used == False
                )
            )
        )
        available_grade9 = result.scalar()

        print(f"\n🔢 Коды 9 класса:")
        print(f"   Всего: {total_grade9}")
        print(f"   Доступно (не использовано): {available_grade9}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python check_session_codes.py <session_id>")
        sys.exit(1)

    session_id = int(sys.argv[1])
    asyncio.run(check_session_codes(session_id))
