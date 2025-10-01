from docx import Document
from typing import Dict, List, Tuple
import re
from datetime import datetime


class OlympiadDocParser:
    """Парсер .docx файлов с кодами олимпиады"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.document = Document(file_path)
        
    def parse(self) -> Dict:
        """
        Основной метод парсинга документа
        
        Returns:
            Dict с ключами:
            - subject: название предмета
            - grade8_codes: список словарей {full_name, code}
            - grade9_codes: список кодов для 9 класса
        """
        result = {
            "subject": None,
            "grade8_codes": [],
            "grade9_codes": []
        }
        
        # Парсим предмет из текста
        result["subject"] = self._extract_subject()
        
        # Парсим таблицы
        tables = self.document.tables
        
        if len(tables) > 0:
            # Первая таблица - 8 класс с именами
            result["grade8_codes"] = self._parse_grade8_table(tables[0])
        
        # Парсим коды 9 класса из текста после таблицы
        result["grade9_codes"] = self._extract_grade9_codes()
        
        return result
    
    def _extract_subject(self) -> str:
        """Извлекает название предмета из документа"""
        # Ищем в параграфах упоминание предмета
        for paragraph in self.document.paragraphs:
            text = paragraph.text.strip()
            # Паттерн для поиска предмета (например, "Физика за 8 класс" или просто "Физика")
            if text and any(word in text.lower() for word in ['физика', 'математика', 'химия', 'биология', 'информатика']):
                # Извлекаем название предмета
                match = re.search(r'(Физика|Математика|Химия|Биология|Информатика)', text, re.IGNORECASE)
                if match:
                    return match.group(1).capitalize()
        
        # Если не нашли в параграфах, проверяем заголовки
        for table in self.document.tables:
            if len(table.rows) > 0:
                first_row = table.rows[0]
                for cell in first_row.cells:
                    text = cell.text.strip()
                    match = re.search(r'(Физика|Математика|Химия|Биология|Информатика)', text, re.IGNORECASE)
                    if match:
                        return match.group(1).capitalize()
        
        return "Неизвестный предмет"
    
    def _parse_grade8_table(self, table) -> List[Dict]:
        """
        Парсит таблицу с кодами для 8 класса
        
        Ожидаемая структура таблицы:
        № | ФИО | Код
        """
        grade8_codes = []
        
        # Начинаем со второй строки (первая - заголовки)
        for i, row in enumerate(table.rows[1:], start=1):
            cells = row.cells
            
            if len(cells) >= 3:
                # Извлекаем данные
                number = cells[0].text.strip()
                full_name = cells[1].text.strip()
                code = cells[2].text.strip()
                
                # Проверяем, что это не пустая строка
                if full_name and code:
                    grade8_codes.append({
                        "number": number,
                        "full_name": full_name,
                        "code": code
                    })
        
        return grade8_codes
    
    def _extract_grade9_codes(self) -> List[str]:
        """
        Извлекает коды для 9 класса из текста документа
        
        Ожидается, что коды идут списком после заголовка типа "Физика за 9 класс"
        """
        grade9_codes = []
        capture_codes = False
        
        for paragraph in self.document.paragraphs:
            text = paragraph.text.strip()
            
            # Начинаем захватывать коды после заголовка "... за 9 класс"
            if "9 класс" in text.lower():
                capture_codes = True
                continue
            
            # Если мы в режиме захвата и строка похожа на код
            if capture_codes and text:
                # Паттерн кода: начинается с sbph59 и содержит слэши
                if text.startswith("sbph59/") or text.startswith("sbph9"):
                    grade9_codes.append(text)
                # Если встретили пустую строку или новую секцию, прекращаем захват
                elif text.startswith("---") or not text:
                    break
        
        return grade9_codes


def parse_olympiad_file(file_path: str) -> Dict:
    """
    Удобная функция для парсинга файла олимпиады
    
    Args:
        file_path: путь к .docx файлу
        
    Returns:
        Dict с распарсенными данными
    """
    parser = OlympiadDocParser(file_path)
    return parser.parse()


# Пример использования
if __name__ == "__main__":
    # Тестовый парсинг
    result = parse_olympiad_file("8Ð.docx")
    
    print(f"Предмет: {result['subject']}")
    print(f"\n8 класс ({len(result['grade8_codes'])} учеников):")
    for student in result['grade8_codes'][:3]:  # Показываем первых 3
        print(f"  {student['number']}. {student['full_name']} - {student['code']}")
    print("  ...")
    
    print(f"\n9 класс ({len(result['grade9_codes'])} кодов):")
    for code in result['grade9_codes'][:3]:  # Показываем первых 3
        print(f"  {code}")
    print("  ...")
