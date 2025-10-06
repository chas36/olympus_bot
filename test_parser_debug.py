"""
Тестовый скрипт для отладки парсера

Использование:
    python test_parser_debug.py <путь_к_файлу.docx>
    
Пример:
    python test_parser_debug.py "8И.docx"
"""

# Критерии валидации кода ученика
CODE_VALIDATION_CRITERIA = ['/', 'sbph']

import sys
from parser.docx_parser import parse_olympiad_file

def main():
    if len(sys.argv) < 2:
        print("❌ Использование: python test_parser_debug.py <файл.docx>")
        print("\nПример:")
        print('  python test_parser_debug.py "8И.docx"')
        return
    
    file_path = sys.argv[1]
    
    print(f"📄 Тестирование парсера на файле: {file_path}")
    print("=" * 70)
    
    try:
        # Парсим файл
        result = parse_olympiad_file(file_path)
        
        # Выводим результаты
        print("\n" + "=" * 70)
        print("📊 РЕЗУЛЬТАТЫ ПАРСИНГА")
        print("=" * 70)
        
        print(f"\n📚 Предмет: {result['subject']}")
        
        print(f"\n👥 Коды 8 класса: {len(result['grade8_codes'])} учеников")
        if result['grade8_codes']:
            print("\nПервые 5 записей:")
            for i, student in enumerate(result['grade8_codes'][:5], 1):
                print(f"  {i}. {student['full_name']}")
                print(f"     Код: {student['code']}")
            
            if len(result['grade8_codes']) > 5:
                print(f"\n  ... и еще {len(result['grade8_codes']) - 5} учеников")
        else:
            print("  ⚠️ Коды не найдены!")
        
        print(f"\n🎓 Коды 9 класса: {len(result['grade9_codes'])} кодов")
        if result['grade9_codes']:
            print("\nПервые 5 кодов:")
            for i, code in enumerate(result['grade9_codes'][:5], 1):
                print(f"  {i}. {code}")
            
            if len(result['grade9_codes']) > 5:
                print(f"\n  ... и еще {len(result['grade9_codes']) - 5} кодов")
        else:
            print("  ⚠️ Коды не найдены!")
        
        print("\n" + "=" * 70)
        
        # Проверки
        print("\n🔍 ПРОВЕРКА КАЧЕСТВА:")
        
        if not result['grade8_codes']:
            print("  ❌ Не найдены коды 8 класса - проверьте структуру таблицы")
        else:
            print(f"  ✅ Найдено {len(result['grade8_codes'])} кодов для 8 класса")
        
        if not result['grade9_codes']:
            print("  ❌ Не найдены коды 9 класса - проверьте секцию '9 класс'")
        else:
            print(f"  ✅ Найдено {len(result['grade9_codes'])} кодов для 9 класса")
        
        # Проверка формата кодов
        invalid_codes_8 = []
        for student in result['grade8_codes']:
            code = student['code']
            if not code or not any(c in code for c in CODE_VALIDATION_CRITERIA):
                invalid_codes_8.append(student['full_name'])
        
        if invalid_codes_8:
            print(f"\n  ⚠️ Подозрительные коды 8 класса у {len(invalid_codes_8)} учеников:")
            for name in invalid_codes_8[:3]:
                print(f"    - {name}")
        
        print("\n" + "=" * 70)
        print("✅ Парсинг завершен!")
        
        return result
        
    except FileNotFoundError:
        print(f"\n❌ Ошибка: Файл '{file_path}' не найден!")
        print("   Проверьте путь к файлу")
        return None
        
    except Exception as e:
        print(f"\n❌ Ошибка парсинга: {e}")
        import traceback
        print("\nПодробности:")
        traceback.print_exc()
        return None


if __name__ == "__main__":
    result = main()
    
    if result is None:
        sys.exit(1)
    else:
        sys.exit(0)