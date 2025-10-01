import secrets
import string
from typing import List


def generate_registration_code(length: int = 12) -> str:
    """
    Генерирует случайный регистрационный код
    
    Args:
        length: длина кода (по умолчанию 12 символов)
        
    Returns:
        Строка регистрационного кода (например: 'K7M9-P2X4-Q8W3')
    """
    # Используем буквы (без похожих: O, 0, I, 1, l) и цифры
    alphabet = ''.join(set(string.ascii_uppercase + string.digits) - set('O0I1L'))
    
    # Генерируем код
    code = ''.join(secrets.choice(alphabet) for _ in range(length))
    
    # Форматируем в группы по 4 символа для читабельности
    formatted_code = '-'.join([code[i:i+4] for i in range(0, len(code), 4)])
    
    return formatted_code


def generate_multiple_codes(count: int, length: int = 12) -> List[str]:
    """
    Генерирует несколько уникальных регистрационных кодов
    
    Args:
        count: количество кодов
        length: длина каждого кода
        
    Returns:
        Список уникальных кодов
    """
    codes = set()
    
    while len(codes) < count:
        codes.add(generate_registration_code(length))
    
    return list(codes)


def validate_code_format(code: str) -> bool:
    """
    Проверяет формат регистрационного кода
    
    Args:
        code: код для проверки
        
    Returns:
        True если формат правильный
    """
    # Убираем дефисы для проверки
    clean_code = code.replace('-', '')
    
    # Проверяем длину и символы
    if len(clean_code) != 12:
        return False
    
    alphabet = set(string.ascii_uppercase + string.digits) - set('O0I1L')
    return all(c in alphabet for c in clean_code)


# Пример использования
if __name__ == "__main__":
    print("Генерация одного кода:")
    print(generate_registration_code())
    
    print("\nГенерация 5 кодов:")
    codes = generate_multiple_codes(5)
    for i, code in enumerate(codes, 1):
        print(f"{i}. {code}")
    
    print("\nПроверка формата:")
    print(f"K7M9-P2X4-Q8W3: {validate_code_format('K7M9-P2X4-Q8W3')}")
    print(f"INVALID-CODE: {validate_code_format('INVALID-CODE')}")
