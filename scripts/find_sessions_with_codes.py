"""
Найти сессии с кодами
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from database.database import AsyncSessionLocal
from database.models import Grade8Code, Grade9Code, OlympiadSession
from sqlalchemy import select, func


async def find_sessions_with_codes():
    """Найти сессии, у которых есть коды"""

    async with AsyncSessionLocal() as session:
        # Получаем все сессии
        result = await session.execute(
            select(OlympiadSession).order_by(OlympiadSession.id.desc()).limit(10)
        )
        sessions = result.scalars().all()

        print(f"✅ Последние 10 сессий:\n")

        for olympiad in sessions:
            # Считаем коды 8 класса
            result = await session.execute(
                select(func.count(Grade8Code.id)).where(Grade8Code.session_id == olympiad.id)
            )
            grade8_count = result.scalar()

            # Считаем коды 9 класса
            result = await session.execute(
                select(func.count(Grade9Code.id)).where(Grade9Code.session_id == olympiad.id)
            )
            grade9_count = result.scalar()

            active_mark = "🟢 АКТИВНА" if olympiad.is_active else ""
            codes_mark = "✅" if (grade8_count > 0 or grade9_count > 0) else "❌"

            print(f"{codes_mark} ID {olympiad.id}: {olympiad.subject} {active_mark}")
            print(f"   Кодов 8 класса: {grade8_count}, Кодов 9 класса: {grade9_count}")
            print()


if __name__ == "__main__":
    asyncio.run(find_sessions_with_codes())
