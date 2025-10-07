import csv
import io
import zipfile
from typing import List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime

from database.models import Student, OlympiadSession, OlympiadCode, CodeRequest


class CodeExporter:
    """Класс для экспорта кодов олимпиад"""
    
    @staticmethod
    async def export_class_codes_csv(
        session: AsyncSession,
        session_id: int,
        class_number: int,
        include_unassigned: bool = False
    ) -> str:
        """
        Экспортирует коды для конкретного класса в CSV
        
        Returns:
            CSV строка
        """
        # Получаем информацию о сессии
        olympiad_result = await session.execute(
            select(OlympiadSession).where(OlympiadSession.id == session_id)
        )
        olympiad = olympiad_result.scalar_one_or_none()
        
        if not olympiad:
            raise ValueError(f"Сессия {session_id} не найдена")
        
        # Получаем коды класса
        query = select(OlympiadCode).where(
            and_(
                OlympiadCode.session_id == session_id,
                OlympiadCode.class_number == class_number
            )
        )
        
        if not include_unassigned:
            query = query.where(OlympiadCode.is_assigned == True)
        
        codes_result = await session.execute(query)
        codes = codes_result.scalars().all()
        
        # Получаем студентов
        student_ids = [c.student_id for c in codes if c.student_id]
        students_result = await session.execute(
            select(Student).where(Student.id.in_(student_ids))
        )
        students = {s.id: s for s in students_result.scalars().all()}
        
        # Получаем запросы кодов
        requests_result = await session.execute(
            select(CodeRequest).where(
                and_(
                    CodeRequest.session_id == session_id,
                    CodeRequest.code_id.in_([c.id for c in codes])
                )
            )
        )
        requests = {r.code_id: r for r in requests_result.scalars().all()}
        
        # Формируем CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Заголовок
        writer.writerow([
            f"Коды олимпиады - {olympiad.subject} - {class_number} класс"
        ])
        writer.writerow([
            f"Дата: {olympiad.date.strftime('%d.%m.%Y %H:%M')}"
        ])
        writer.writerow([])  # Пустая строка
        
        # Колонки
        writer.writerow([
            "№", "ФИО", "Код", "Статус", "Получен", "Скриншот"
        ])
        
        # Данные
        for i, code in enumerate(sorted(codes, key=lambda c: students.get(c.student_id, Student()).full_name if c.student_id else ""), start=1):
            student = students.get(code.student_id)
            request = requests.get(code.id)
            
            if student:
                status = "Распределен"
                issued = "Да" if code.is_issued else "Нет"
                screenshot = "Да" if (request and request.screenshot_submitted) else "Нет"
            else:
                status = "Не распределен"
                issued = "-"
                screenshot = "-"
            
            writer.writerow([
                i,
                student.full_name if student else "-",
                code.code,
                status,
                issued,
                screenshot
            ])
        
        # Итоги
        writer.writerow([])
        writer.writerow(["ИТОГО:", len(codes)])
        assigned = len([c for c in codes if c.is_assigned])
        writer.writerow(["Распределено:", assigned])
        writer.writerow(["Не распределено:", len(codes) - assigned])
        
        return output.getvalue()
    
    @staticmethod
    async def export_all_classes_zip(
        session: AsyncSession,
        session_id: int,
        include_unassigned: bool = False
    ) -> bytes:
        """
        Экспортирует коды всех классов в ZIP архив
        
        Returns:
            ZIP архив в виде bytes
        """
        # Получаем информацию о сессии
        olympiad_result = await session.execute(
            select(OlympiadSession).where(OlympiadSession.id == session_id)
        )
        olympiad = olympiad_result.scalar_one_or_none()
        
        if not olympiad:
            raise ValueError(f"Сессия {session_id} не найдена")
        
        # Получаем все классы с кодами
        result = await session.execute(
            select(OlympiadCode.class_number).distinct().where(
                OlympiadCode.session_id == session_id
            )
        )
        class_numbers = sorted([row[0] for row in result.fetchall()])
        
        # Создаем ZIP архив в памяти
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for class_num in class_numbers:
                # Экспортируем коды класса
                csv_data = await CodeExporter.export_class_codes_csv(
                    session, session_id, class_num, include_unassigned
                )
                
                # Добавляем в архив
                filename = f"{olympiad.subject}_{class_num}_класс.csv"
                zip_file.writestr(filename, csv_data.encode('utf-8-sig'))  # utf-8-sig для Excel
            
            # Добавляем сводный файл
            summary_csv = await CodeExporter._generate_summary_csv(
                session, session_id, class_numbers
            )
            zip_file.writestr(f"{olympiad.subject}_сводка.csv", summary_csv.encode('utf-8-sig'))
        
        zip_buffer.seek(0)
        return zip_buffer.getvalue()
    
    @staticmethod
    async def _generate_summary_csv(
        session: AsyncSession,
        session_id: int,
        class_numbers: List[int]
    ) -> str:
        """Генерирует сводную статистику"""
        olympiad_result = await session.execute(
            select(OlympiadSession).where(OlympiadSession.id == session_id)
        )
        olympiad = olympiad_result.scalar_one_or_none()
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow([f"Сводная статистика - {olympiad.subject}"])
        writer.writerow([f"Дата: {olympiad.date.strftime('%d.%m.%Y %H:%M')}"])
        writer.writerow([])
        
        writer.writerow(["Класс", "Всего кодов", "Распределено", "Получено", "Скриншотов"])
        
        total_codes = 0
        total_assigned = 0
        total_issued = 0
        total_screenshots = 0
        
        for class_num in class_numbers:
            # Коды класса
            codes_result = await session.execute(
                select(OlympiadCode).where(
                    and_(
                        OlympiadCode.session_id == session_id,
                        OlympiadCode.class_number == class_num
                    )
                )
            )
            codes = codes_result.scalars().all()
            
            # Запросы
            code_ids = [c.id for c in codes]
            requests_result = await session.execute(
                select(CodeRequest).where(
                    and_(
                        CodeRequest.session_id == session_id,
                        CodeRequest.code_id.in_(code_ids)
                    )
                )
            )
            requests = requests_result.scalars().all()
            
            # Статистика
            assigned = len([c for c in codes if c.is_assigned])
            issued = len([c for c in codes if c.is_issued])
            screenshots = len([r for r in requests if r.screenshot_submitted])
            
            writer.writerow([
                f"{class_num} класс",
                len(codes),
                assigned,
                issued,
                screenshots
            ])
            
            total_codes += len(codes)
            total_assigned += assigned
            total_issued += issued
            total_screenshots += screenshots
        
        writer.writerow([])
        writer.writerow(["ИТОГО:", total_codes, total_assigned, total_issued, total_screenshots])
        
        return output.getvalue()
    
    @staticmethod
    async def export_student_codes_pdf(
        session: AsyncSession,
        session_id: int,
        class_number: int
    ) -> bytes:
        """
        Экспортирует коды для печати ученикам (PDF)
        
        TODO: Реализация генерации PDF
        Можно использовать библиотеку reportlab
        """
        raise NotImplementedError("PDF экспорт будет реализован позже")