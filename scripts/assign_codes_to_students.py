"""
Скрипт для автоматического распределения кодов 8 класса по ученикам
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from database.database import AsyncSessionLocal
from database.models import Student, Grade8Code, OlympiadSession
from sqlalchemy import select, and_


async def assign_codes_to_students():
    """Распределить коды 8 класса по ученикам для всех сессий"""

    async with AsyncSessionLocal() as session:
        # Получаем всех учеников
        result = await session.execute(select(Student).where(Student.class_number.isnot(None)))
        students = result.scalars().all()

        print(f"✅ Найдено {len(students)} учеников с указанным классом")

        # Получаем все сессии
        result = await session.execute(select(OlympiadSession))
        sessions = result.scalars().all()

        print(f"✅ Найдено {len(sessions)} сессий олимпиад")

        total_assigned = 0

        for olympiad in sessions:
            # Получаем неназначенные коды 8 класса для этой сессии
            result = await session.execute(
                select(Grade8Code).where(
                    and_(
                        Grade8Code.session_id == olympiad.id,
                        Grade8Code.student_id.is_(None)
                    )
                )
            )
            codes = result.scalars().all()

            if not codes:
                continue

            print(f"\n📚 {olympiad.subject}")
            print(f"   Кодов без привязки: {len(codes)}")

            # Распределяем коды по ученикам
            assigned = 0
            for i, student in enumerate(students):
                if i >= len(codes):
                    break

                codes[i].student_id = student.id
                assigned += 1

            total_assigned += assigned
            print(f"   ✅ Привязано кодов: {assigned}")

        await session.commit()

        print(f"\n{'='*60}")
        print(f"✅ Всего привязано кодов: {total_assigned}")


if __name__ == "__main__":
    asyncio.run(assign_codes_to_students())
