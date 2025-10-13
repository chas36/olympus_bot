"""
Скрипт для генерации отчетов по олимпиаде

Использование:
    python scripts/generate_report.py [--session-id ID] [--format FORMAT]

Форматы: console, csv, excel, html
"""

import asyncio
import sys
import os
from datetime import datetime
import argparse

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.database import AsyncSessionLocal, init_db
from database import crud


async def generate_console_report(session_id: int = None):
    """Генерирует отчет в консоль"""
    
    async with AsyncSessionLocal() as session:
        if session_id:
            olympiad_session = await crud.get_session_by_id(session, session_id)
        else:
            olympiad_session = await crud.get_active_session(session)
        
        if not olympiad_session:
            print("❌ Сессия не найдена!")
            return
        
        # Получаем все запросы
        all_requests = await crud.get_all_requests_for_session(session, olympiad_session.id)
        all_students = await crud.get_all_students(session)
        
        # Подсчитываем статистику
        registered_count = len([s for s in all_students if s.is_registered])
        requested_code = len(all_requests)
        grade8_count = len([r for r in all_requests if r.grade == 8])
        grade9_count = len([r for r in all_requests if r.grade == 9])
        screenshot_count = len([r for r in all_requests if r.screenshot_submitted])
        
        # Выводим отчет
        print("\n" + "=" * 70)
        print(f"📊 ОТЧЕТ ПО ОЛИМПИАДЕ")
        print("=" * 70)
        print(f"\n📚 Предмет: {olympiad_session.subject}")
        print(f"📅 Дата: {olympiad_session.date.strftime('%d.%m.%Y %H:%M')}")
        print(f"\n{'=' * 70}")
        print(f"\n👥 УЧЕНИКИ:")
        print(f"   Всего в системе: {len(all_students)}")
        print(f"   Зарегистрировано: {registered_count}")
        print(f"\n📝 КОДЫ ОЛИМПИАДЫ:")
        print(f"   Запросили код: {requested_code}")
        print(f"   - 8 класс: {grade8_count}")
        print(f"   - 9 класс: {grade9_count}")
        print(f"\n📸 СКРИНШОТЫ:")
        print(f"   Прислали: {screenshot_count}")
        print(f"   Не прислали: {requested_code - screenshot_count}")
        if requested_code > 0:
            percentage = (screenshot_count / requested_code) * 100
            print(f"   Процент: {percentage:.1f}%")
        
        print(f"\n{'=' * 70}")
        print(f"\n📋 ДЕТАЛЬНАЯ ИНФОРМАЦИЯ ПО УЧЕНИКАМ:")
        print(f"{'=' * 70}\n")
        
        # Создаем словарь запросов
        requests_dict = {r.student_id: r for r in all_requests}
        
        # Сортируем: сначала те, кто запросил код
        students_with_codes = [(s, requests_dict[s.id]) for s in all_students if s.id in requests_dict]
        students_without_codes = [s for s in all_students if s.id not in requests_dict]
        
        # Ученики с кодами
        if students_with_codes:
            print("✅ Запросили код:\n")
            for student, request in students_with_codes:
                screenshot_icon = "✅" if request.screenshot_submitted else "❌"
                print(f"  {student.full_name}")
                print(f"    Класс: {request.grade} | Скриншот: {screenshot_icon}")
                print(f"    Код: {request.code}")
                print(f"    Запрошено: {request.requested_at.strftime('%d.%m.%Y %H:%M')}")
                if request.screenshot_submitted:
                    print(f"    Скриншот: {request.screenshot_submitted_at.strftime('%d.%m.%Y %H:%M')}")
                print()
        
        # Ученики без кодов
        if students_without_codes:
            print("\n❌ Не запросили код:\n")
            for student in students_without_codes:
                status = "✅ Зарегистрирован" if student.is_registered else "❌ Не зарегистрирован"
                print(f"  {student.full_name} ({status})")
            print()
        
        print("=" * 70 + "\n")


async def generate_csv_report(session_id: int = None, output_file: str = None):
    """Генерирует отчет в CSV формате"""
    import csv
    
    if not output_file:
        output_file = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    async with AsyncSessionLocal() as session:
        if session_id:
            olympiad_session = await crud.get_session_by_id(session, session_id)
        else:
            olympiad_session = await crud.get_active_session(session)
        
        if not olympiad_session:
            print("❌ Сессия не найдена!")
            return
        
        all_requests = await crud.get_all_requests_for_session(session, olympiad_session.id)
        all_students = await crud.get_all_students(session)
        
        requests_dict = {r.student_id: r for r in all_requests}
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Заголовок
            writer.writerow([
                'ФИО', 'Зарегистрирован', 'Telegram ID',
                'Код запрошен', 'Класс', 'Код олимпиады',
                'Время запроса', 'Скриншот', 'Время скриншота'
            ])
            
            # Данные
            for student in all_students:
                request = requests_dict.get(student.id)
                
                row = [
                    student.full_name,
                    'Да' if student.is_registered else 'Нет',
                    student.telegram_id or '-',
                    'Да' if request else 'Нет',
                    request.grade if request else '-',
                    request.code if request else '-',
                    request.requested_at.strftime('%d.%m.%Y %H:%M') if request else '-',
                    'Да' if (request and request.screenshot_submitted) else 'Нет',
                    request.screenshot_submitted_at.strftime('%d.%m.%Y %H:%M') if (request and request.screenshot_submitted_at) else '-'
                ]
                
                writer.writerow(row)
        
        print(f"✅ Отчет сохранен: {output_file}")


async def generate_excel_report(session_id: int = None, output_file: str = None):
    """Генерирует отчет в Excel формате"""
    try:
        import pandas as pd
    except ImportError:
        print("❌ Установите pandas для генерации Excel отчетов: pip install pandas openpyxl")
        return
    
    if not output_file:
        output_file = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    async with AsyncSessionLocal() as session:
        if session_id:
            olympiad_session = await crud.get_session_by_id(session, session_id)
        else:
            olympiad_session = await crud.get_active_session(session)
        
        if not olympiad_session:
            print("❌ Сессия не найдена!")
            return
        
        all_requests = await crud.get_all_requests_for_session(session, olympiad_session.id)
        all_students = await crud.get_all_students(session)
        
        requests_dict = {r.student_id: r for r in all_requests}
        
        # Подготовка данных
        data = []
        for student in all_students:
            request = requests_dict.get(student.id)
            
            data.append({
                'ФИО': student.full_name,
                'Зарегистрирован': 'Да' if student.is_registered else 'Нет',
                'Telegram ID': student.telegram_id or '-',
                'Код запрошен': 'Да' if request else 'Нет',
                'Класс': request.grade if request else '-',
                'Код олимпиады': request.code if request else '-',
                'Время запроса': request.requested_at.strftime('%d.%m.%Y %H:%M') if request else '-',
                'Скриншот': 'Да' if (request and request.screenshot_submitted) else 'Нет',
                'Время скриншота': request.screenshot_submitted_at.strftime('%d.%m.%Y %H:%M') if (request and request.screenshot_submitted_at) else '-'
            })
        
        # Создание Excel файла
        df = pd.DataFrame(data)
        
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Отчет', index=False)
            
            # Автоматическая настройка ширины колонок
            worksheet = writer.sheets['Отчет']
            # Efficiently set column widths using vectorized operations
            for idx, col in enumerate(df.columns):
                max_length = max(df[col].astype(str).map(len).max(), len(str(col))) + 2
                col_letter = worksheet.cell(row=1, column=idx + 1).column_letter
                worksheet.column_dimensions[col_letter].width = max_length
        
        print(f"✅ Отчет сохранен: {output_file}")


async def main():
    parser = argparse.ArgumentParser(description='Генерация отчетов по олимпиаде')
    parser.add_argument('--session-id', type=int, help='ID сессии (по умолчанию активная)')
    parser.add_argument('--format', choices=['console', 'csv', 'excel'], default='console',
                        help='Формат отчета')
    parser.add_argument('--output', help='Имя выходного файла')
    
    args = parser.parse_args()
    
    await init_db()
    
    if args.format == 'console':
        await generate_console_report(args.session_id)
    elif args.format == 'csv':
        await generate_csv_report(args.session_id, args.output)
    elif args.format == 'excel':
        await generate_excel_report(args.session_id, args.output)


if __name__ == "__main__":
    asyncio.run(main())
