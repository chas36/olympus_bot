"""
Скрипт для обновления классов существующих учеников из Excel файла
"""
import asyncio
import sys
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.database import AsyncSessionLocal
from database.models import Student
from parser.excel_parser import parse_students_excel
from sqlalchemy import select


async def update_student_classes(excel_path: str):
    """Обновить классы учеников из Excel файла"""

    # Парсим Excel
    print(f"📖 Парсинг файла: {excel_path}")
    students_data, validation = parse_students_excel(excel_path)

    print(f"✅ Найдено {len(students_data)} учеников в файле")
    print(f"📊 Распределение по классам:")
    for class_num in sorted(validation["class_distribution"].keys()):
        count = validation["class_distribution"][class_num]
        print(f"   {class_num} класс: {count} учеников")

    # Обновляем в БД
    async with AsyncSessionLocal() as session:
        updated = 0
        not_found = 0

        for student_data in students_data:
            # Ищем ученика по ФИО
            result = await session.execute(
                select(Student).where(Student.full_name == student_data["full_name"])
            )
            student = result.scalar_one_or_none()

            if student:
                # Обновляем класс и параллель
                student.class_number = student_data.get("class_number")
                student.parallel = student_data.get("parallel")
                updated += 1
            else:
                not_found += 1
                print(f"⚠️  Ученик не найден в БД: {student_data['full_name']}")

        await session.commit()

        print(f"\n✅ Обновлено: {updated} учеников")
        print(f"❌ Не найдено в БД: {not_found} учеников")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python scripts/update_student_classes.py <файл.xlsx>")
        sys.exit(1)

    excel_path = sys.argv[1]

    if not Path(excel_path).exists():
        print(f"❌ Файл не найден: {excel_path}")
        sys.exit(1)

    asyncio.run(update_student_classes(excel_path))
