#!/usr/bin/env python3
"""
Скрипт для загрузки кодов олимпиад из CSV
"""

import sys
import asyncio
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from parser.csv_parser import parse_codes_csv
from database.database import AsyncSessionLocal
from database.models import OlympiadSession, Grade8Code, Grade9Code


async def load_codes(csv_file: str):
    """Загружает коды из CSV"""
    print(f"\n🔑 Загрузка кодов из {csv_file}")
    print("=" * 60)
    
    # Парсим CSV
    results = parse_codes_csv(csv_file, encoding='windows-1251')
    
    if not results:
        print("❌ Не удалось распарсить файл")
        return
    
    print(f"\n✅ Найдено предметов: {len(results)}")
    
    for subject_data in results:
        print(f"\n📚 {subject_data['subject']}")
        print(f"   Класс: {subject_data['class_number']}")
        print(f"   Дата: {subject_data['date']}")
        print(f"   Кодов: {len(subject_data['codes'])}")
    
    # Подтверждение
    response = input(f"\n❓ Загрузить коды в БД? (yes/no): ")
    if response.lower() not in ['yes', 'y', 'да', 'д']:
        print("❌ Отменено")
        return
    
    async with AsyncSessionLocal() as session:
        for subject_data in results:
            print(f"\n📥 Загрузка {subject_data['subject']}...")
            
            # Создаем или получаем сессию олимпиады
            olympiad = OlympiadSession(
                subject=subject_data['subject'],
                date=datetime.now(),  # Можно улучшить парсинг даты
                is_active=True
            )
            session.add(olympiad)
            await session.flush()
            
            # Загружаем коды
            class_num = subject_data['class_number']
            codes = subject_data['codes']
            
            if class_num == 8:
                for code_str in codes:
                    code = Grade8Code(
                        session_id=olympiad.id,
                        code=code_str,
                        is_issued=False
                    )
                    session.add(code)
            elif class_num == 9:
                for code_str in codes:
                    code = Grade9Code(
                        session_id=olympiad.id,
                        code=code_str,
                        is_used=False
                    )
                    session.add(code)
            
            print(f"  ✅ Загружено {len(codes)} кодов")
        
        await session.commit()
        print(f"\n{'='*60}")
        print(f"✅ Все коды загружены!")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python load_codes_from_csv.py <файл.csv>")
        sys.exit(1)
    
    asyncio.run(load_codes(sys.argv[1]))
