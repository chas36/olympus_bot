"""
Скрипт миграции данных из старой структуры БД в новую

Старая структура:
- Students (без class_number)
- Grade8Code, Grade9Code (раздельные таблицы)

Новая структура:
- Students (с class_number)
- OlympiadCode (унифицированная таблица)
- Поддержка классов 4-11

Использование:
    python scripts/migrate_to_new_structure.py
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import text
from database.database import AsyncSessionLocal, init_db
from database.models import Student, OlympiadSession, OlympiadCode, DistributionMode


async def migrate_students():
    """
    Миграция учеников:
    - Определяем класс по кодам Grade8/Grade9
    - Если класс не определен, ставим по умолчанию 8
    """
    print("\n" + "=" * 60)
    print("📚 МИГРАЦИЯ УЧЕНИКОВ")
    print("=" * 60)
    
    async with AsyncSessionLocal() as session:
        # Проверяем наличие старых таблиц
        result = await session.execute(
            text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'grade8_codes'
                )
            """)
        )
        has_old_structure = result.scalar()
        
        if not has_old_structure:
            print("ℹ️  Старая структура не найдена, миграция не требуется")
            return
        
        # Получаем всех учеников
        result = await session.execute(text("SELECT * FROM students"))
        old_students = result.fetchall()
        
        print(f"\nНайдено учеников: {len(old_students)}")
        
        migrated = 0
        
        for old_student in old_students:
            student_id = old_student[0]  # id
            
            # Проверяем, есть ли у ученика коды 8 класса
            result = await session.execute(
                text("SELECT COUNT(*) FROM grade8_codes WHERE student_id = :sid"),
                {"sid": student_id}
            )
            has_grade8 = result.scalar() > 0
            
            # Определяем класс
            class_number = 8 if has_grade8 else 9
            
            # Обновляем ученика
            await session.execute(
                text("""
                    UPDATE students 
                    SET class_number = :class_num,
                        updated_at = NOW()
                    WHERE id = :sid
                """),
                {"class_num": class_number, "sid": student_id}
            )
            
            migrated += 1
        
        await session.commit()
        print(f"✅ Мигрировано учеников: {migrated}")


async def migrate_codes():
    """
    Миграция кодов:
    - Переносим Grade8Code и Grade9Code в OlympiadCode
    - Сохраняем всю информацию о распределении
    """
    print("\n" + "=" * 60)
    print("🔑 МИГРАЦИЯ КОДОВ")
    print("=" * 60)
    
    async with AsyncSessionLocal() as session:
        # Проверяем наличие старых таблиц
        result = await session.execute(
            text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'grade8_codes'
                )
            """)
        )
        has_old_structure = result.scalar()
        
        if not has_old_structure:
            print("ℹ️  Старая структура не найдена, миграция не требуется")
            return
        
        # Миграция Grade8Code
        print("\n📖 Миграция кодов 8 класса...")
        result = await session.execute(text("SELECT * FROM grade8_codes"))
        grade8_codes = result.fetchall()
        
        migrated_g8 = 0
        for code_data in grade8_codes:
            await session.execute(
                text("""
                    INSERT INTO olympiad_codes 
                    (session_id, class_number, code, student_id, is_assigned, 
                     assigned_at, is_reserve, is_issued, issued_at)
                    VALUES 
                    (:session_id, 8, :code, :student_id, true,
                     :issued_at, false, :is_issued, :issued_at)
                """),
                {
                    "session_id": code_data[2],  # session_id
                    "code": code_data[3],         # code
                    "student_id": code_data[1],   # student_id
                    "is_issued": code_data[4],    # is_issued
                    "issued_at": code_data[5]     # issued_at
                }
            )
            migrated_g8 += 1
        
        print(f"  ✅ Мигрировано кодов 8 класса: {migrated_g8}")
        
        # Миграция Grade9Code
        print("\n📖 Миграция кодов 9 класса...")
        result = await session.execute(text("SELECT * FROM grade9_codes"))
        grade9_codes = result.fetchall()
        
        migrated_g9 = 0
        for code_data in grade9_codes:
            await session.execute(
                text("""
                    INSERT INTO olympiad_codes 
                    (session_id, class_number, code, student_id, is_assigned, 
                     assigned_at, is_reserve, is_issued, issued_at)
                    VALUES 
                    (:session_id, 9, :code, :student_id, :is_assigned,
                     :assigned_at, false, false, NULL)
                """),
                {
                    "session_id": code_data[1],      # session_id
                    "code": code_data[2],            # code
                    "student_id": code_data[3],      # assigned_student_id
                    "is_assigned": code_data[4],     # is_used
                    "assigned_at": code_data[5]      # assigned_at
                }
            )
            migrated_g9 += 1
        
        print(f"  ✅ Мигрировано кодов 9 класса: {migrated_g9}")
        
        await session.commit()
        print(f"\n✅ Всего мигрировано кодов: {migrated_g8 + migrated_g9}")


async def migrate_code_requests():
    """
    Миграция запросов кодов:
    - Обновляем связи с новой структурой кодов
    """
    print("\n" + "=" * 60)
    print("📝 МИГРАЦИЯ ЗАПРОСОВ КОДОВ")
    print("=" * 60)
    
    async with AsyncSessionLocal() as session:
        # Получаем все запросы
        result = await session.execute(text("SELECT * FROM code_requests"))
        requests = result.fetchall()
        
        print(f"\nНайдено запросов: {len(requests)}")
        
        updated = 0
        
        for request in requests:
            request_id = request[0]
            student_id = request[1]
            session_id = request[2]
            grade = request[3]
            old_code = request[4]
            
            # Находим соответствующий код в новой таблице
            result = await session.execute(
                text("""
                    SELECT id FROM olympiad_codes
                    WHERE session_id = :sid 
                    AND student_id = :stud_id
                    AND class_number = :grade
                    AND code = :code
                    LIMIT 1
                """),
                {
                    "sid": session_id,
                    "stud_id": student_id,
                    "grade": grade,
                    "code": old_code
                }
            )
            code_id = result.scalar()
            
            if code_id:
                # Обновляем запрос
                await session.execute(
                    text("""
                        UPDATE code_requests
                        SET code_id = :code_id
                        WHERE id = :req_id
                    """),
                    {"code_id": code_id, "req_id": request_id}
                )
                updated += 1
        
        await session.commit()
        print(f"✅ Обновлено запросов: {updated}")


async def update_sessions_mode():
    """
    Обновляет режим распределения для существующих сессий
    По умолчанию ставим on_demand
    """
    print("\n" + "=" * 60)
    print("⚙️  ОБНОВЛЕНИЕ РЕЖИМА СЕССИЙ")
    print("=" * 60)
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            text("""
                UPDATE olympiad_sessions
                SET distribution_mode = 'on_demand'
                WHERE distribution_mode IS NULL
                RETURNING id, subject
            """)
        )
        updated = result.fetchall()
        
        await session.commit()
        
        print(f"✅ Обновлено сессий: {len(updated)}")
        for sess in updated:
            print(f"  - {sess[1]} (ID: {sess[0]})")


async def cleanup_old_tables():
    """
    Опционально удаляет старые таблицы после успешной миграции
    """
    print("\n" + "=" * 60)
    print("🗑️  ОЧИСТКА СТАРЫХ ТАБЛИЦ")
    print("=" * 60)
    
    confirm = input("\n⚠️  Удалить старые таблицы? (yes/no): ")
    
    if confirm.lower() not in ['yes', 'y']:
        print("❌ Очистка отменена")
        return
    
    async with AsyncSessionLocal() as session:
        # Удаляем старые таблицы
        await session.execute(text("DROP TABLE IF EXISTS grade8_codes CASCADE"))
        await session.execute(text("DROP TABLE IF EXISTS grade9_codes CASCADE"))
        
        await session.commit()
        
        print("✅ Старые таблицы удалены")


async def main():
    print("\n" + "=" * 60)
    print("🔄 МИГРАЦИЯ ДАННЫХ OLYMPUS BOT")
    print("=" * 60)
    print("\nЭтот скрипт мигрирует данные из старой структуры БД в новую")
    print("Перед началом убедитесь, что у вас есть BACKUP базы данных!")
    print("")
    
    confirm = input("Продолжить? (yes/no): ")
    
    if confirm.lower() not in ['yes', 'y', 'да', 'д']:
        print("\n❌ Миграция отменена")
        return
    
    # Инициализируем новую структуру
    print("\n🔄 Инициализация новой структуры БД...")
    await init_db()
    
    # Выполняем миграцию
    await migrate_students()
    await migrate_codes()
    await migrate_code_requests()
    await update_sessions_mode()
    
    # Опционально удаляем старые таблицы
    await cleanup_old_tables()
    
    print("\n" + "=" * 60)
    print("✅ МИГРАЦИЯ ЗАВЕРШЕНА")
    print("=" * 60)
    print("\nРекомендации:")
    print("1. Проверьте корректность данных")
    print("2. Протестируйте основные функции")
    print("3. Если все работает, можно удалить бэкап")
    print("")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n❌ Прервано пользователем")
    except Exception as e:
        print(f"\n\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()