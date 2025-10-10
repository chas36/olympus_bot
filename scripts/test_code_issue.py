"""
Скрипт для проверки выдачи кодов ученикам
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from database.database import AsyncSessionLocal
from database.models import Student, Grade8Code, OlympiadSession
from database import crud
from sqlalchemy import select


async def test_code_issue():
    """Проверить выдачу кодов зарегистрированным ученикам"""

    async with AsyncSessionLocal() as session:
        # Получаем зарегистрированных учеников
        result = await session.execute(
            select(Student).where(Student.is_registered == True)
        )
        students = result.scalars().all()

        print(f"✅ Найдено зарегистрированных учеников: {len(students)}")

        for student in students:
            print(f"\n👤 {student.full_name}")
            print(f"   Класс: {student.class_number}{student.parallel or ''}")
            print(f"   Telegram ID: {student.telegram_id}")

        # Получаем активную сессию
        active_session = await crud.get_active_session(session)

        if not active_session:
            print("\n❌ Нет активной сессии!")
            return

        print(f"\n📚 Активная сессия: {active_session.subject} (ID: {active_session.id})")

        # Проверяем коды для каждого ученика
        for student in students:
            print(f"\n👤 Проверка кодов для: {student.full_name}")

            # Для 8 класса
            if student.class_number == 8:
                print(f"   Класс 8 - будут показаны кнопки выбора")

                # Проверяем код 8 класса
                grade8_code = await crud.get_grade8_code_for_student(
                    session, student.id, active_session.id
                )

                if grade8_code:
                    print(f"   ✅ Код 8 класса найден: {grade8_code.code}")
                else:
                    print(f"   ❌ Код 8 класса НЕ найден!")

                # Проверяем доступность кодов 9 класса
                grade9_count = await crud.count_available_grade9_codes(
                    session, active_session.id
                )
                print(f"   Доступно кодов 9 класса: {grade9_count}")

            else:
                # Для остальных классов
                print(f"   Класс {student.class_number} - код будет выдан сразу")

                # Проверяем код
                grade8_code = await crud.get_grade8_code_for_student(
                    session, student.id, active_session.id
                )

                if grade8_code:
                    print(f"   ✅ Код найден: {grade8_code.code}")
                else:
                    print(f"   ❌ Код НЕ найден!")


if __name__ == "__main__":
    asyncio.run(test_code_issue())
