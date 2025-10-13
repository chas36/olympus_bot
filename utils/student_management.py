from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Dict, Tuple
import json
from datetime import datetime
import logging

from database.models import Student, StudentHistory
from utils.auth import generate_multiple_codes

logger = logging.getLogger(__name__)


class StudentManager:
    """Класс для управления учениками"""
    
    @staticmethod
    async def create_student(
        session: AsyncSession,
        full_name: str,
        class_number: int,
        registration_code: str = None
    ) -> Student:
        """Создает нового ученика"""
        if not registration_code:
            registration_code = generate_multiple_codes(1)[0]
        
        student = Student(
            full_name=full_name,
            class_number=class_number,
            registration_code=registration_code,
            is_active=True
        )
        
        session.add(student)
        await session.flush()
        
        # Записываем историю
        await StudentManager._log_history(
            session, student.id, "created",
            new_data={"full_name": full_name, "class_number": class_number}
        )
        
        await session.commit()
        await session.refresh(student)
        
        return student
    
    @staticmethod
    async def bulk_create_students(
        session: AsyncSession,
        students_data: List[Dict]
    ) -> List[Student]:
        """
        Массовое создание учеников
        
        Args:
            students_data: список словарей с ключами full_name, class_number
        """
        # Генерируем коды для всех
        codes = generate_multiple_codes(len(students_data))
        
        created_students = []
        
        for student_data, code in zip(students_data, codes):
            student = await StudentManager.create_student(
                session,
                full_name=student_data["full_name"],
                class_number=student_data["class_number"],
                registration_code=code
            )
            created_students.append(student)
        
        logger.info(f"Создано {len(created_students)} учеников")
        return created_students
    
    @staticmethod
    async def update_student(
        session: AsyncSession,
        student_id: int,
        full_name: str = None,
        class_number: int = None
    ) -> Student:
        """Обновляет данные ученика"""
        result = await session.execute(
            select(Student).where(Student.id == student_id)
        )
        student = result.scalar_one_or_none()
        
        if not student:
            raise ValueError(f"Ученик с ID {student_id} не найден")
        
        old_data = {
            "full_name": student.full_name,
            "class_number": student.class_number
        }
        
        if full_name:
            student.full_name = full_name
        if class_number:
            student.class_number = class_number
        
        student.updated_at = datetime.utcnow()
        
        new_data = {
            "full_name": student.full_name,
            "class_number": student.class_number
        }
        
        await StudentManager._log_history(
            session, student_id, "updated",
            old_data=old_data, new_data=new_data
        )
        
        await session.commit()
        await session.refresh(student)
        
        return student
    
    @staticmethod
    async def change_class(
        session: AsyncSession,
        student_id: int,
        new_class: int
    ) -> Student:
        """Переводит ученика в другой класс"""
        result = await session.execute(
            select(Student).where(Student.id == student_id)
        )
        student = result.scalar_one_or_none()
        
        if not student:
            raise ValueError(f"Ученик с ID {student_id} не найден")
        
        old_class = student.class_number
        student.class_number = new_class
        student.updated_at = datetime.utcnow()
        
        await StudentManager._log_history(
            session, student_id, "class_changed",
            old_data={"class_number": old_class},
            new_data={"class_number": new_class}
        )
        
        await session.commit()
        await session.refresh(student)
        
        logger.info(f"Ученик {student.full_name} переведен из {old_class} в {new_class} класс")
        return student
    
    @staticmethod
    async def deactivate_student(
        session: AsyncSession,
        student_id: int
    ) -> Student:
        """Деактивирует ученика (архивирует)"""
        result = await session.execute(
            select(Student).where(Student.id == student_id)
        )
        student = result.scalar_one_or_none()
        
        if not student:
            raise ValueError(f"Ученик с ID {student_id} не найден")
        
        student.is_active = False
        student.updated_at = datetime.utcnow()
        
        await StudentManager._log_history(
            session, student_id, "deactivated",
            old_data={"is_active": True},
            new_data={"is_active": False}
        )
        
        await session.commit()
        await session.refresh(student)
        
        return student
    
    @staticmethod
    async def compare_and_update(
        session: AsyncSession,
        new_students: List[Dict]
    ) -> Dict:
        """
        Сравнивает новый список учеников с существующим и обновляет БД
        
        Args:
            new_students: список словарей с ключами full_name, class_number
            
        Returns:
            Dict с результатами сверки
        """
        # Получаем всех активных учеников
        result = await session.execute(
            select(Student).where(Student.is_active == True)
        )
        existing_students = {s.full_name: s for s in result.scalars().all()}
        
        new_students_dict = {s["full_name"]: s for s in new_students}
        
        results = {
            "added": [],
            "updated": [],
            "deactivated": [],
            "unchanged": []
        }
        
        # Находим учеников для добавления и обновления
        for name, data in new_students_dict.items():
            if name not in existing_students:
                # Новый ученик
                student = await StudentManager.create_student(
                    session,
                    full_name=name,
                    class_number=data["class_number"]
                )
                results["added"].append({
                    "name": name,
                    "class": data["class_number"],
                    "student_id": student.id
                })
            else:
                # Существующий ученик
                existing = existing_students[name]
                if existing.class_number != data["class_number"]:
                    # Изменился класс
                    await StudentManager.change_class(
                        session,
                        student_id=existing.id,
                        new_class=data["class_number"]
                    )
                    results["updated"].append({
                        "name": name,
                        "old_class": existing.class_number,
                        "new_class": data["class_number"]
                    })
                else:
                    results["unchanged"].append(name)
        
        # Находим учеников для деактивации
        for name, student in existing_students.items():
            if name not in new_students_dict:
                await StudentManager.deactivate_student(session, student.id)
                results["deactivated"].append({
                    "name": name,
                    "class": student.class_number,
                    "student_id": student.id
                })
        
        logger.info(
            f"Сверка завершена: добавлено {len(results['added'])}, "
            f"обновлено {len(results['updated'])}, "
            f"деактивировано {len(results['deactivated'])}"
        )
        
        return results
    
    @staticmethod
    async def get_class_students(
        session: AsyncSession,
        class_number: int,
        include_inactive: bool = False
    ) -> List[Student]:
        """Получает всех учеников указанного класса"""
        query = select(Student).where(Student.class_number == class_number)
        
        if not include_inactive:
            query = query.where(Student.is_active == True)
        
        result = await session.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_students_by_class_distribution(
        session: AsyncSession,
        include_inactive: bool = False
    ) -> Dict[int, List[Student]]:
        """Получает учеников, сгруппированных по классам"""
        query = select(Student)
        
        if not include_inactive:
            query = query.where(Student.is_active == True)
        
        result = await session.execute(query)
        all_students = result.scalars().all()
        
        distribution = {}
        for student in all_students:
            if student.class_number not in distribution:
                distribution[student.class_number] = []
            distribution[student.class_number].append(student)
        
        return distribution
    
    @staticmethod
    async def _log_history(
        session: AsyncSession,
        student_id: int,
        action: str,
        old_data: Dict = None,
        new_data: Dict = None
    ):
        """Записывает изменение в историю"""
        history = StudentHistory(
            student_id=student_id,
            action=action,
            old_data=json.dumps(old_data) if old_data else None,
            new_data=json.dumps(new_data) if new_data else None
        )
        session.add(history)