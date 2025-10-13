import csv
import re
from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class CodesCSVParser:
    """Парсер CSV файлов с кодами олимпиад (табличный формат)"""
    
    def __init__(self, file_path: str, encoding: str = 'utf-8'):
        self.file_path = file_path
        self.encoding = encoding
        
    def parse(self) -> List[Dict]:
        """
        Парсит CSV файл с кодами
        
        Формат:
        - Строка 1: заголовки (A1=класс, E1+=предметы)
        - Строка 2: даты проведения для каждого предмета
        - Строки 3+: коды участников
        
        Returns:
            List[Dict] - список предметов с кодами:
            {
                "subject": название предмета,
                "date": дата (строка),
                "class_number": номер класса,
                "codes": [список кодов]
            }
        """
        logger.info(f"Начинаем парсинг файла: {self.file_path}")
        
        # Извлекаем класс из имени файла
        class_number = None
        filename_match = re.search(r'_(\d{1,2})\.csv', self.file_path)
        if filename_match:
            class_number = int(filename_match.group(1))
            logger.info(f"Класс из имени файла: {class_number}")
        
        # Читаем CSV
        results = []
        
        with open(self.file_path, 'r', encoding=self.encoding) as f:
            reader = csv.reader(f, delimiter=';')  # Используем ; как разделитель
            rows = list(reader)
        
        if len(rows) < 3:
            logger.warning("Файл содержит менее 3 строк, невозможно распарсить")
            return results
        
        # Строка 1: заголовки (предметы начинаются с колонки E, индекс 4)
        header_row = rows[0]
        
        # Строка 2: даты
        dates_row = rows[1]
        
        # Если класс не извлечен из имени, пробуем взять из A1
        if not class_number and len(header_row) > 0:
            match = re.search(r'(\d+)', header_row[0])
            if match:
                class_number = int(match.group(1))
                logger.info(f"Класс из A1: {class_number}")
        
        # Обрабатываем каждый столбец начиная с E (индекс 4)
        for col_idx in range(4, len(header_row)):
            subject = header_row[col_idx].strip()
            
            # Пропускаем пустые столбцы
            if not subject:
                continue
            
            logger.info(f"Обработка предмета: {subject} (колонка {col_idx})")
            
            # Дата для этого предмета
            date_str = dates_row[col_idx].strip() if col_idx < len(dates_row) else ""

            # Парсим дату
            parsed_date = None
            if date_str:
                parsed_date = self._parse_date(date_str)
            
            # Собираем коды из всех строк начиная с 3-й (индекс 2)
            codes = []
            for row_idx in range(2, len(rows)):
                row = rows[row_idx]
                
                # Проверяем, что в этой строке есть данные для текущего столбца
                if col_idx < len(row):
                    code = row[col_idx].strip()
                    
                    # Проверяем, что это валидный код
                    if code and self._is_valid_code(code):
                        codes.append(code)
            
            logger.info(f"  Найдено кодов для {subject}: {len(codes)}")
            
            # Добавляем результат только если есть коды
            if codes:
                results.append({
                    "subject": subject,
                    "date": parsed_date,
                    "date_str": date_str,
                    "class_number": class_number,
                    "codes": codes
                })
        
        logger.info(f"Всего предметов с кодами: {len(results)}")
        return results
    
    def _is_valid_code(self, code: str) -> bool:
        """Проверяет, является ли строка валидным кодом"""
        # Код должен содержать слэши и начинаться с sb
        return (
            code.lower().startswith('sb') and
            '/' in code and
            len(code) > 15
        )

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """
        Парсит дату из строки в различных форматах

        Поддерживаемые форматы:
        - 23.10.2024
        - 23.10.24
        - 23/10/2024
        - 2024-10-23
        - 30 сентября (день месяц)
        """
        if not date_str:
            return None

        # Словарь русских названий месяцев
        months_ru = {
            'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4,
            'мая': 5, 'июня': 6, 'июля': 7, 'августа': 8,
            'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12
        }

        # Пробуем распарсить формат "30 сентября"
        date_str_lower = date_str.lower().strip()
        for month_name, month_num in months_ru.items():
            if month_name in date_str_lower:
                # Извлекаем число
                match = re.search(r'(\d{1,2})', date_str_lower)
                if match:
                    day = int(match.group(1))
                    # Используем текущий год
                    year = datetime.now().year
                    try:
                        return datetime(year, month_num, day)
                    except ValueError:
                        logger.warning(f"Некорректная дата: {date_str}")
                        return None

        # Форматы для парсинга
        formats = [
            "%d.%m.%Y",  # 23.10.2024
            "%d.%m.%y",  # 23.10.24
            "%d/%m/%Y",  # 23/10/2024
            "%d/%m/%y",  # 23/10/24
            "%Y-%m-%d",  # 2024-10-23
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        logger.warning(f"Не удалось распарсить дату: {date_str}")
        return None


def parse_codes_csv(file_path: str, encoding: str = 'utf-8') -> List[Dict]:
    """
    Удобная функция для парсинга CSV файла с кодами
    
    Args:
        file_path: путь к CSV файлу
        encoding: кодировка файла
        
    Returns:
        List[Dict] с распарсенными данными по предметам
    """
    parser = CodesCSVParser(file_path, encoding)
    return parser.parse()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Использование: python csv_parser.py <файл.csv>")
        sys.exit(1)
    
    results = parse_codes_csv(sys.argv[1])
    
    if not results:
        print("❌ Не удалось распарсить файл или файл пустой")
        sys.exit(1)
    
    print(f"\n📊 Результаты парсинга:")
    print(f"  Найдено предметов: {len(results)}")
    
    for subject_data in results:
        print(f"\n  📚 {subject_data['subject']}")
        print(f"     Класс: {subject_data['class_number']}")
        print(f"     Дата: {subject_data['date']}")
        print(f"     Кодов: {len(subject_data['codes'])}")
        
        if subject_data['codes']:
            print(f"     Примеры:")
            for code in subject_data['codes'][:3]:
                print(f"       - {code}")
            
            if len(subject_data['codes']) > 3:
                print(f"       ... и еще {len(subject_data['codes']) - 3}")