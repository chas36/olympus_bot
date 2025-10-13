from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from typing import List, Dict, Tuple
import logging

from database.models import Student, OlympiadSession, OlympiadCode, DistributionMode

logger = logging.getLogger(__name__)


class CodeDistributor:
    """Класс для распределения кодов олимпиад"""
    
    @staticmethod
    async def create_codes_from_csv(
        session: AsyncSession,
        session_id: int,
        class_number: int,
        codes: List[str]
    ) -> List[OlympiadCode]:
        """
        Создает коды из распарсенного CSV
        
        Args:
            session_id: ID сессии олимпиады
            class_number: номер класса
            codes: список кодов
        """
        created_codes = []
        
        for code_str in codes:
            code = OlympiadCode(
                session_id=session_id,
                class_number=class_number,
                code=code_str
            )
            session.add(code)
            created_codes.append(code)
        
        await session.flush()
        logger.info(f"Создано {len(created_codes)} кодов для {class_number} класса")
        
        return created_codes
    
    @staticmethod
    async def create_reserve_from_grade9(
        session: AsyncSession,
        session_id: int
    ) -> Dict:
        """
        Создает резерв для 8 классов из кодов 9 класса
        
        Логика:
        1. Получаем все коды 9 класса
        2. Получаем количество учеников в каждом из 8 классов
        3. Распределяем коды 9 класса между 8 классами пропорционально
        """
        # Получаем коды 9 класса
        result = await session.execute(
            select(OlympiadCode).where(
                and_(
                    OlympiadCode.session_id == session_id,
                    OlympiadCode.class_number == 9,
                    OlympiadCode.is_reserve == False
                )
            )
        )
        grade9_codes = result.scalars().all()
        
        if not grade9_codes:
            logger.info("Нет кодов 9 класса для резервирования")
            return {}
        
        # Получаем учеников 8 классов
        result = await session.execute(
            select(
                Student.class_number,
                func.count(Student.id).label('count')
            ).where(
                and_(
                    Student.is_active == True,
                    Student.class_number == 8
                )
            ).group_by(Student.class_number)
        )
        
        # Это даст нам только количество учеников 8 класса
        # Но нам нужно распределить между всеми 8-ми классами
        # Предполагаю, что в БД у нас 8А, 8Б и т.д. хранятся как class_number=8
        # Если в реальности есть 8А, 8Б как отдельные классы, нужно доработать
        
        eighth_grade_students = dict(result.fetchall())
        
        if not eighth_grade_students:
            logger.info("Нет учеников 8 классов для резервирования")
            return {}
        
        total_8th_graders = sum(eighth_grade_students.values())
        reserve_count = len(grade9_codes)
        
        logger.info(f"Резервирование: {reserve_count} кодов 9 класса для {total_8th_graders} учеников 8 классов")
        
        # Распределяем коды пропорционально
        distribution = {}
        codes_to_reserve = []
        
        for class_num, student_count in eighth_grade_students.items():
            # Количество кодов для этого класса
            proportion = student_count / total_8th_graders
            codes_for_class = int(reserve_count * proportion)
            
            distribution[class_num] = {
                "students": student_count,
                "reserved_codes": codes_for_class
            }
            
            # Берем нужное количество кодов
            for _ in range(codes_for_class):
                if grade9_codes:
                    code = grade9_codes.pop()
                    code.is_reserve = True
                    code.reserved_for_class = class_num
                    codes_to_reserve.append(code)
        
        await session.commit()
        
        logger.info(f"Зарезервировано {len(codes_to_reserve)} кодов из {reserve_count}")
        return distribution
    
    @staticmethod
    async def distribute_codes_pre_assign(
        session: AsyncSession,
        session_id: int
    ) -> Dict:
        """
        Предварительное распределение кодов между учениками
        
        Режим pre-distributed: каждому ученику сразу присваивается код
        """
        results = {
            "assigned": [],
            "failed": [],
            "total": 0
        }
        
        # Получаем все активные классы
        result = await session.execute(
            select(Student.class_number).distinct().where(Student.is_active == True)
        )
        class_numbers = [row[0] for row in result.fetchall()]
        
        for class_num in class_numbers:
            # Получаем учеников класса
            students_result = await session.execute(
                select(Student).where(
                    and_(
                        Student.class_number == class_num,
                        Student.is_active == True
                    )
                )
            )
            students = students_result.scalars().all()
            
            # Получаем доступные коды для класса
            codes_result = await session.execute(
                select(OlympiadCode).where(
                    and_(
                        OlympiadCode.session_id == session_id,
                        OlympiadCode.class_number == class_num,
                        OlympiadCode.is_assigned == False
                    )
                )
            )
            available_codes = list(codes_result.scalars().all())
            
            # Если для 8 класса не хватает кодов, используем резерв
            if class_num == 8 and len(available_codes) < len(students):
                reserve_result = await session.execute(
                    select(OlympiadCode).where(
                        and_(
                            OlympiadCode.session_id == session_id,
                            OlympiadCode.is_reserve == True,
                            OlympiadCode.reserved_for_class == class_num,
                            OlympiadCode.is_assigned == False
                        )
                    )
                )
                reserve_codes = list(reserve_result.scalars().all())
                available_codes.extend(reserve_codes)
            
            # Распределяем коды
            for student in students:
                if available_codes:
                    code = available_codes.pop(0)
                    code.student_id = student.id
                    code.is_assigned = True
                    
                    results["assigned"].append({
                        "student_id": student.id,
                        "student_name": student.full_name,
                        "class": class_num,
                        "code": code.code
                    })
                else:
                    results["failed"].append({
                        "student_id": student.id,
                        "student_name": student.full_name,
                        "class": class_num,
                        "reason": "Недостаточно кодов"
                    })
        
        results["total"] = len(results["assigned"])
        await session.commit()
        
        logger.info(f"Распределено кодов: {results['total']}, не распределено: {len(results['failed'])}")
        return results
    
    @staticmethod
    async def get_code_for_student_on_demand(
        session: AsyncSession,
        student_id: int,
        session_id: int
    ) -> OlympiadCode:
        """
        Выдает код ученику в режиме on-demand
        
        Args:
            student_id: ID ученика
            session_id: ID сессии олимпиады
            
        Returns:
            OlympiadCode или None если кодов нет
        """
        # Получаем ученика
        student_result = await session.execute(
            select(Student).where(Student.id == student_id)
        )
        student = student_result.scalar_one_or_none()
        
        if not student:
            raise ValueError(f"Ученик с ID {student_id} не найден")
        
        class_num = student.class_number
        
        # Ищем свободный код для класса ученика
        code_result = await session.execute(
            select(OlympiadCode).where(
                and_(
                    OlympiadCode.session_id == session_id,
                    OlympiadCode.class_number == class_num,
                    OlympiadCode.is_assigned == False
                )
            ).limit(1)
        )
        code = code_result.scalar_one_or_none()
        
        # Если нет кода для 8 класса, пробуем взять из резерва
        if not code and class_num == 8:
            reserve_result = await session.execute(
                select(OlympiadCode).where(
                    and_(
                        OlympiadCode.session_id == session_id,
                        OlympiadCode.is_reserve == True,
                        OlympiadCode.reserved_for_class == class_num,
                        OlympiadCode.is_assigned == False
                    )
                ).limit(1)
            )
            code = reserve_result.scalar_one_or_none()
        
        if code:
            code.student_id = student_id
            code.is_assigned = True
            await session.commit()
            await session.refresh(code)
            
            logger.info(f"Выдан код {code.code} ученику {student.full_name}")
        
        return code
    
    @staticmethod
    async def get_available_codes_count(
        session: AsyncSession,
        session_id: int,
        class_number: int = None
    ) -> Dict[int, int]:
        """Получает количество доступных кодов по классам"""
        query = select(
            OlympiadCode.class_number,
            func.count(OlympiadCode.id).label('count')
        ).where(
            and_(
                OlympiadCode.session_id == session_id,
                OlympiadCode.is_assigned == False
            )
        )
        
        if class_number:
            query = query.where(OlympiadCode.class_number == class_number)
        
        query = query.group_by(OlympiadCode.class_number)
        
        result = await session.execute(query)
        return dict(result.fetchall())
    
    @staticmethod
    async def reassign_code(
        session: AsyncSession,
        code_id: int,
        new_student_id: int
    ) -> OlympiadCode:
        """Переназначает код другому ученику"""
        code_result = await session.execute(
            select(OlympiadCode).where(OlympiadCode.id == code_id)
        )
        code = code_result.scalar_one_or_none()
        
        if not code:
            raise ValueError(f"Код с ID {code_id} не найден")
        
        code.student_id = new_student_id
        code.is_assigned = True
        
        await session.commit()
        await session.refresh(code)
        
        return code