"""
Загрузка всех CSV файлов кодов с привязкой к классам
Файлы должны называться: sch771584_4.csv, sch771584_5.csv, ..., sch771584_11.csv
"""
import asyncio
import sys
import re
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from parser.csv_parser import parse_codes_csv
from database.database import AsyncSessionLocal
from database.models import OlympiadSession, Grade8Code, Grade9Code, Student
from sqlalchemy import select


async def load_csv_for_class(csv_file: str, class_number: int):
    """Загрузить CSV файл для конкретного класса"""

    print(f"\n📚 Загрузка кодов для {class_number} класса из {csv_file}")
    print("=" * 70)

    # Парсим CSV
    results = parse_codes_csv(csv_file, encoding='windows-1251')

    if not results:
        print(f"❌ Не удалось распарсить файл {csv_file}")
        return 0

    print(f"✅ Найдено предметов: {len(results)}")

    session_count = 0

    async with AsyncSessionLocal() as session:
        # Получаем всех учеников этого класса
        result = await session.execute(
            select(Student).where(Student.class_number == class_number)
        )
        students = result.scalars().all()

        print(f"👥 Учеников {class_number} класса: {len(students)}")

        for subject_data in results:
            subject = subject_data['subject']
            date = subject_data.get('date') or datetime.now()  # Используем текущую дату если None
            codes = subject_data['codes']

            print(f"\n  📖 {subject}")
            print(f"     Дата: {date}")
            print(f"     Кодов: {len(codes)}")

            # Создаем сессию олимпиады для этого класса
            olympiad = OlympiadSession(
                subject=subject,
                class_number=class_number,
                date=date,
                is_active=False,
                uploaded_file_name=Path(csv_file).name
            )
            session.add(olympiad)
            await session.flush()

            # Загружаем коды и привязываем к ученикам
            # Для 8 класса - именные коды
            # Для остальных - также именные коды (но БЕЗ возможности выбора 9 класса)
            codes_added = 0

            for i, code_str in enumerate(codes):
                # Циклично распределяем коды между учениками класса
                student = students[i % len(students)] if students else None

                code = Grade8Code(
                    session_id=olympiad.id,
                    code=code_str,
                    is_issued=False,
                    student_id=student.id if student else None
                )
                session.add(code)
                codes_added += 1

            await session.flush()
            print(f"     ✅ Загружено кодов: {codes_added}")
            session_count += 1

        await session.commit()

    return session_count


async def main():
    """Загрузить все CSV файлы"""

    # Ищем CSV файлы вида sch771584_X.csv где X - номер класса
    csv_files = list(Path('.').glob('sch771584_*.csv'))

    if not csv_files:
        print("❌ Не найдено CSV файлов вида sch771584_X.csv")
        return

    print(f"✅ Найдено CSV файлов: {len(csv_files)}")

    total_sessions = 0

    for csv_file in sorted(csv_files):
        # Извлекаем номер класса из имени файла
        match = re.search(r'sch771584_(\d+)\.csv', csv_file.name)
        if not match:
            print(f"⚠️  Пропуск файла {csv_file.name} - неверный формат")
            continue

        class_number = int(match.group(1))

        if not (4 <= class_number <= 11):
            print(f"⚠️  Пропуск файла {csv_file.name} - неверный номер класса ({class_number})")
            continue

        sessions = await load_csv_for_class(str(csv_file), class_number)
        total_sessions += sessions

    print(f"\n{'=' * 70}")
    print(f"✅ Всего загружено сессий: {total_sessions}")


if __name__ == "__main__":
    asyncio.run(main())
