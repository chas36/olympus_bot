"""
Скрипт для массового добавления учеников из текстового файла

Использование:
    python scripts/add_students_from_file.py students.txt

Формат файла students.txt (каждый ученик на новой строке):
    Иванов Иван Иванович
    Петров Петр Петрович
    Сидорова Анна Сергеевна
"""

import asyncio
import sys
import os

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.database import AsyncSessionLocal, init_db
from database import crud
from utils.auth import generate_multiple_codes


async def add_students_from_file(filename: str):
    """Добавляет учеников из файла"""
    
    # Проверяем существование файла
    if not os.path.exists(filename):
        print(f"❌ Файл {filename} не найден!")
        return
    
    # Читаем файл
    with open(filename, 'r', encoding='utf-8') as f:
        students = [line.strip() for line in f if line.strip()]
    
    if not students:
        print("❌ Файл пустой!")
        return
    
    print(f"📋 Найдено учеников: {len(students)}")
    print("\nУченики:")
    for i, student in enumerate(students, 1):
        print(f"  {i}. {student}")
    
    # Подтверждение
    confirm = input(f"\nДобавить {len(students)} учеников? (yes/no): ")
    if confirm.lower() not in ['yes', 'y', 'да', 'д']:
        print("❌ Отменено")
        return
    
    # Инициализируем БД
    await init_db()
    
    # Генерируем коды
    print("\n🔑 Генерация регистрационных кодов...")
    codes = generate_multiple_codes(len(students))
    
    # Добавляем учеников
    print("\n📝 Добавление учеников в базу данных...")
    
    results = []
    async with AsyncSessionLocal() as session:
        for student_name, code in zip(students, codes):
            try:
                student = await crud.create_student(
                    session,
                    full_name=student_name,
                    registration_code=code
                )
                results.append({
                    'name': student.full_name,
                    'code': student.registration_code,
                    'success': True
                })
                print(f"  ✅ {student.full_name}")
            except Exception as e:
                results.append({
                    'name': student_name,
                    'code': code,
                    'success': False,
                    'error': str(e)
                })
                print(f"  ❌ {student_name}: {e}")
    
    # Итоговая статистика
    success_count = sum(1 for r in results if r['success'])
    print(f"\n✅ Успешно добавлено: {success_count}/{len(students)}")
    
    # Сохраняем коды в файл
    output_filename = f"registration_codes_{os.path.basename(filename)}"
    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write("ФИО | Регистрационный код\n")
        f.write("-" * 70 + "\n")
        for result in results:
            if result['success']:
                f.write(f"{result['name']} | {result['code']}\n")
    
    print(f"\n📄 Коды сохранены в файл: {output_filename}")
    print("\n⚠️  Раздайте эти коды ученикам для регистрации в боте!")


async def main():
    if len(sys.argv) < 2:
        print("Использование: python scripts/add_students_from_file.py <файл_с_учениками.txt>")
        print("\nФормат файла: каждый ученик на новой строке")
        print("Пример:")
        print("  Иванов Иван Иванович")
        print("  Петров Петр Петрович")
        return
    
    filename = sys.argv[1]
    await add_students_from_file(filename)


if __name__ == "__main__":
    asyncio.run(main())
