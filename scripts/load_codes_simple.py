#!/usr/bin/env python3
"""
Простая загрузка кодов БЕЗ распределения по ученикам
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
    
    results = parse_codes_csv(csv_file, encoding='windows-1251')
    
    if not results:
        print("❌ Не удалось распарсить файл")
        return
    
    print(f"\n✅ Найдено предметов: {len(results)}")
    
    for subject_data in results:
        print(f"  📚 {subject_data['subject']}: {len(subject_data['codes'])} кодов")
    
    response = input(f"\n❓ Загрузить коды в БД БЕЗ распределения? (yes/no): ")
    if response.lower() not in ['yes', 'y', 'да', 'д']:
        print("❌ Отменено")
        return
    
    async with AsyncSessionLocal() as session:
        for subject_data in results:
            print(f"\n📥 {subject_data['subject']}...", end=" ")
            
            # Создаем сессию олимпиады
            olympiad = OlympiadSession(
                subject=subject_data['subject'],
                date=datetime.now(),
                is_active=False
            )
            session.add(olympiad)
            await session.flush()
            
            class_num = subject_data['class_number']
            codes = subject_data['codes']
            
            if class_num == 8:
                for code_str in codes:
                    code = Grade8Code(
                        student_id=None,  # Без распределения
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
            
            print(f"✅ {len(codes)} кодов")
        
        await session.commit()
        print(f"\n{'='*60}")
        print(f"✅ Готово! Коды загружены БЕЗ распределения")
        print(f"💡 Распределите коды через админ-панель или скрипт")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python load_codes_simple.py <файл.csv>")
        sys.exit(1)
    
    asyncio.run(load_codes(sys.argv[1]))
