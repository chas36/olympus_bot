#!/usr/bin/env python3
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from parser.csv_parser import parse_codes_csv
from database.database import AsyncSessionLocal
from database.models import OlympiadSession, Grade8Code, Grade9Code
from datetime import datetime
import glob


async def load_all():
    """Загружает все CSV файлы"""
    csv_files = glob.glob("sch771584_*.csv")
    
    if not csv_files:
        print("❌ Не найдены CSV файлы")
        return
    
    print(f"📁 Найдено файлов: {len(csv_files)}")
    for f in csv_files:
        print(f"  - {f}")
    
    response = input(f"\n❓ Загрузить все? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        return
    
    async with AsyncSessionLocal() as session:
        total = 0
        
        for csv_file in csv_files:
            print(f"\n📂 Обработка {csv_file}...")
            results = parse_codes_csv(csv_file, encoding='windows-1251')
            
            for subject_data in results:
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
                            student_id=None,
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
                
                print(f"  ✅ {subject_data['subject']}: {len(codes)} кодов")
                total += len(codes)
        
        await session.commit()
        print(f"\n{'='*60}")
        print(f"✅ ГОТОВО! Загружено {total} кодов")


if __name__ == "__main__":
    asyncio.run(load_all())
