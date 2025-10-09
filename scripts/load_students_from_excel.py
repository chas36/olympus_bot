#!/usr/bin/env python3
"""
Скрипт для загрузки учеников из Excel в существующую БД
"""

import sys
import asyncio
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from parser.excel_parser import parse_students_excel
from database.database import AsyncSessionLocal
from database.models import Student
from utils.auth import generate_multiple_codes


async def load_students(excel_file: str):
    """Загружает учеников из Excel"""
    print(f"\n📚 Загрузка учеников из {excel_file}")
    print("=" * 60)
    
    # Парсим Excel
    students, validation = parse_students_excel(excel_file)
    
    print(f"\n✅ Распарсено: {len(students)} учеников")
    print(f"\n📊 Распределение по классам:")
    for class_num in sorted(validation["class_distribution"].keys()):
        count = validation["class_distribution"][class_num]
        print(f"  {class_num} класс: {count} учеников")
    
    # Предупреждения
    if validation["duplicates"]:
        print(f"\n⚠️  Найдено дубликатов: {len(validation['duplicates'])}")
        for dup in validation["duplicates"][:3]:
            print(f"  - {dup['name']}")
    
    if validation["invalid_names"]:
        print(f"\n⚠️  Подозрительные имена: {len(validation['invalid_names'])}")
        for inv in validation["invalid_names"][:3]:
            print(f"  - {inv['name']}")
    
    # Подтверждение
    response = input(f"\n❓ Загрузить {len(students)} учеников в БД? (yes/no): ")
    if response.lower() not in ['yes', 'y', 'да', 'д']:
        print("❌ Отменено")
        return
    
    # Генерируем коды регистрации
    print("\n�� Генерация кодов регистрации...")
    reg_codes = generate_multiple_codes(len(students))
    
    # Загружаем в БД
    async with AsyncSessionLocal() as session:
        created_count = 0
        skipped_count = 0
        
        for student_data, reg_code in zip(students, reg_codes):
            # Проверяем, нет ли уже такого ученика
            from sqlalchemy import select
            result = await session.execute(
                select(Student).where(Student.full_name == student_data["full_name"])
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                print(f"  ⏭️  Пропуск: {student_data['full_name']} (уже существует)")
                skipped_count += 1
                continue
            
            # Создаем ученика
            student = Student(
                full_name=student_data["full_name"],
                registration_code=reg_code,
                is_registered=False
            )
            session.add(student)
            created_count += 1
            
            if created_count % 50 == 0:
                print(f"  ✅ Загружено: {created_count}")
        
        await session.commit()
        
        print(f"\n{'='*60}")
        print(f"✅ Загрузка завершена!")
        print(f"  Создано: {created_count}")
        print(f"  Пропущено: {skipped_count}")
        print(f"{'='*60}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python load_students_from_excel.py <файл.xlsx>")
        sys.exit(1)
    
    asyncio.run(load_students(sys.argv[1]))
