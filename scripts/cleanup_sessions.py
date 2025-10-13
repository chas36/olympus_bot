"""
Очистка всех сессий и кодов
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from database.database import AsyncSessionLocal
from database.models import OlympiadSession, Grade8Code, Grade9Code, CodeRequest
from sqlalchemy import select


async def cleanup():
    """Удалить все сессии и коды"""

    response = input("⚠️  Это удалит ВСЕ сессии, коды и запросы кодов. Продолжить? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("❌ Отменено")
        return

    async with AsyncSessionLocal() as session:
        # Удаляем запросы кодов
        result = await session.execute(select(CodeRequest))
        requests = result.scalars().all()
        for req in requests:
            await session.delete(req)
        print(f"✅ Удалено запросов кодов: {len(requests)}")

        # Удаляем коды 8 класса
        result = await session.execute(select(Grade8Code))
        codes8 = result.scalars().all()
        for code in codes8:
            await session.delete(code)
        print(f"✅ Удалено кодов 8 класса: {len(codes8)}")

        # Удаляем коды 9 класса
        result = await session.execute(select(Grade9Code))
        codes9 = result.scalars().all()
        for code in codes9:
            await session.delete(code)
        print(f"✅ Удалено кодов 9 класса: {len(codes9)}")

        # Удаляем сессии
        result = await session.execute(select(OlympiadSession))
        sessions = result.scalars().all()
        for s in sessions:
            await session.delete(s)
        print(f"✅ Удалено сессий: {len(sessions)}")

        await session.commit()
        print("\n✅ Очистка завершена!")


if __name__ == "__main__":
    asyncio.run(cleanup())
