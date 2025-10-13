"""
Тесты для парсера .docx файлов
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from parser.docx_parser import parse_olympiad_file


def test_parse_sample_file():
    """Тест парсинга примера файла"""
    
    # Путь к тестовому файлу
    test_file = "8Ð.docx"
    
    if not os.path.exists(test_file):
        print(f"❌ Тестовый файл {test_file} не найден!")
        return False
    
    print(f"📄 Парсинг файла: {test_file}")
    
    try:
        result = parse_olympiad_file(test_file)
        
        print(f"\n✅ Парсинг успешен!")
        print(f"\nПредмет: {result['subject']}")
        print(f"Кодов 8 класса: {len(result['grade8_codes'])}")
        print(f"Кодов 9 класса: {len(result['grade9_codes'])}")
        
        # Проверяем структуру
        assert 'subject' in result, "Не найден предмет"
        assert 'grade8_codes' in result, "Не найдены коды 8 класса"
        assert 'grade9_codes' in result, "Не найдены коды 9 класса"
        
        # Проверяем наличие данных
        assert len(result['grade8_codes']) > 0, "Нет кодов для 8 класса"
        assert len(result['grade9_codes']) > 0, "Нет кодов для 9 класса"
        
        # Проверяем структуру кодов 8 класса
        for code_data in result['grade8_codes'][:3]:
            print(f"\nПример кода 8 класса:")
            print(f"  Номер: {code_data.get('number')}")
            print(f"  ФИО: {code_data.get('full_name')}")
            print(f"  Код: {code_data.get('code')}")
            
            assert 'full_name' in code_data, "Нет ФИО"
            assert 'code' in code_data, "Нет кода"
            assert code_data['full_name'], "ФИО пустое"
            assert code_data['code'], "Код пустой"
        
        # Проверяем коды 9 класса
        print(f"\nПримеры кодов 9 класса:")
        for code in result['grade9_codes'][:3]:
            print(f"  {code}")
            assert code, "Пустой код"
        
        print(f"\n✅ Все проверки пройдены!")
        return True
        
    except Exception as e:
        print(f"\n❌ Ошибка парсинга: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_parse_structure():
    """Тест проверки структуры распарсенных данных"""
    
    test_file = "8Ð.docx"
    
    if not os.path.exists(test_file):
        print(f"⚠️ Пропуск теста - файл {test_file} не найден")
        return True
    
    result = parse_olympiad_file(test_file)
    
    # Проверяем, что все коды 8 класса имеют правильную структуру
    for code_data in result['grade8_codes']:
        assert isinstance(code_data, dict), "Код должен быть словарем"
        assert 'full_name' in code_data, "Отсутствует ФИО"
        assert 'code' in code_data, "Отсутствует код"
        assert isinstance(code_data['full_name'], str), "ФИО должно быть строкой"
        assert isinstance(code_data['code'], str), "Код должен быть строкой"
    
    # Проверяем, что коды 9 класса - это строки
    for code in result['grade9_codes']:
        assert isinstance(code, str), "Код должен быть строкой"
        assert code.strip(), "Код не должен быть пустым"
    
    print("✅ Структура данных корректна")
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 Тестирование парсера олимпиадных файлов")
    print("=" * 60)
    print()
    
    tests = [
        ("Парсинг примера файла", test_parse_sample_file),
        ("Проверка структуры данных", test_parse_structure),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n{'=' * 60}")
        print(f"📝 Тест: {test_name}")
        print(f"{'=' * 60}")
        
        try:
            if test_func():
                passed += 1
                print(f"\n✅ PASSED")
            else:
                failed += 1
                print(f"\n❌ FAILED")
        except Exception as e:
            failed += 1
            print(f"\n❌ FAILED: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'=' * 60}")
    print(f"📊 Результаты:")
    print(f"  ✅ Пройдено: {passed}")
    print(f"  ❌ Провалено: {failed}")
    print(f"  📊 Всего: {len(tests)}")
    print(f"{'=' * 60}")
    
    sys.exit(0 if failed == 0 else 1)
