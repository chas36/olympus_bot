# 📝 Changelog - Olympus Bot v2.0

## 🎉 Версия 2.0.0 (2025-01-07)

### 🚀 Основные изменения

#### 1. Поддержка всех классов (4-11)

**Было:**
- Поддержка только 8 и 9 классов
- Раздельные таблицы Grade8Code и Grade9Code

**Стало:**
- Поддержка классов с 4 по 11
- Единая таблица OlympiadCode для всех классов
- Поле `class_number` у каждого ученика

**Файлы:**
- `database/models_new.py` - Обновленные модели
- `database/crud_new.py` - Обновленные CRUD операции

---

#### 2. Система распределения кодов

**Два режима работы:**

**On-Demand (по запросу):**
- Коды хранятся в пуле
- Выдаются ученику при запросе через бота
- Автоматическое резервирование кодов 9 класса для 8 классов

**Pre-Distributed (предварительное распределение):**
- Коды распределяются между учениками заранее
- Каждому ученику присваивается персональный код
- Подходит для подготовки списков

**Файлы:**
- `utils/code_distribution.py` - Логика распределения
- `database/models_new.py` - Enum `DistributionMode`

---

#### 3. Резервирование кодов

**Логика:**
- Коды 9 класса создают резерв для 8 классов
- Распределение пропорционально количеству учеников
- Автоматическое использование при нехватке основных кодов

**Пример:**
- 8 класс: 30 учеников, 25 кодов
- 9 класс: 20 кодов
- Резервирование: 5 кодов из 9 класса для 8 класса

**Файлы:**
- `utils/code_distribution.py::create_reserve_from_grade9()`

---

#### 4. Управление учениками

**Новые возможности:**

**Загрузка из Excel:**
```python
POST /admin/students/upload-excel
```
- Массовая загрузка учеников
- Автоматическая валидация
- Генерация регистрационных кодов

**Обновление с автоматической сверкой:**
```python
POST /admin/students/update-from-excel
```
- Сравнение со существующими
- Добавление новых
- Обновление изменившихся
- Деактивация отсутствующих

**CRUD операции:**
- Создание (`POST /admin/students/`)
- Обновление (`PUT /admin/students/{id}`)
- Перевод класса (`PUT /admin/students/{id}/change-class`)
- Деактивация (`DELETE /admin/students/{id}`)

**История изменений:**
- Таблица `StudentHistory`
- Логирование всех действий

**Файлы:**
- `api/routers/students.py` - API эндпоинты
- `utils/student_management.py` - Бизнес-логика
- `parser/excel_parser.py` - Парсер Excel

---

#### 5. Парсеры данных

**Excel парсер (ученики):**
```python
from parser.excel_parser import parse_students_excel

students, validation = parse_students_excel("students.xlsx")
```

Возможности:
- Автоматическое определение колонок
- Извлечение класса из различных форматов (8А, 9 Б, 11)
- Валидация данных
- Обнаружение дубликатов

**CSV парсер (коды):**
```python
from parser.csv_parser import parse_codes_csv

result = parse_codes_csv("sch771584_8.csv")
```

Возможности:
- Извлечение предмета из заголовка
- Парсинг даты олимпиады
- Определение класса из имени файла
- Валидация кодов

**Файлы:**
- `parser/excel_parser.py`
- `parser/csv_parser.py`

---

#### 6. Экспорт данных

**По классам (CSV):**
```python
GET /admin/codes/export/class/{session_id}/{class_number}
```

Содержит:
- Список учеников
- Коды олимпиады
- Статус получения
- Статус скриншота

**Все классы (ZIP):**
```python
GET /admin/codes/export/all/{session_id}
```

Содержит:
- CSV для каждого класса
- Сводную статистику
- Готово для распределения

**Файлы:**
- `utils/export.py` - Модуль экспорта
- `api/routers/codes.py` - API эндпоинты

---

#### 7. Обновленный бот

**Изменения в командах:**

`/get_code` - Умная выдача кодов:
- Поддержка нескольких активных олимпиад
- Автоматический выбор из пула (on-demand)
- Или выдача предназначенного кода (pre-distributed)
- Использование резерва при необходимости

`/my_status` - Расширенная информация:
- Статус по каждой активной олимпиаде
- Информация о скриншотах
- Коды для копирования

**Файлы:**
- `bot/handlers/olympiad_new.py`
- `bot/handlers/screenshots_new.py`

---

### 🗃️ База данных

#### Новые таблицы:

**`olympiad_codes`** (объединяет Grade8Code и Grade9Code):
```sql
- id
- session_id
- class_number (4-11)
- code
- student_id (nullable)
- is_assigned
- assigned_at
- is_reserve
- reserved_for_class
- is_issued
- issued_at
```

**`student_history`** (история изменений):
```sql
- id
- student_id
- action (created, updated, class_changed, deleted)
- old_data (JSON)
- new_data (JSON)
- timestamp
```

#### Обновленные таблицы:

**`students`:**
- Добавлено: `class_number` (4-11)
- Добавлено: `is_active` (для архивирования)
- Добавлено: `updated_at`

**`olympiad_sessions`:**
- Добавлено: `distribution_mode` (on_demand/pre_distributed)

**`code_requests`:**
- Изменено: `grade` удалено (берется из кода)
- Добавлено: `code_id` (ForeignKey на OlympiadCode)

---

### 🔌 API изменения

#### Новые эндпоинты:

**Управление учениками:**
```
POST   /admin/students/upload-excel
POST   /admin/students/update-from-excel
POST   /admin/students/
PUT    /admin/students/{id}
PUT    /admin/students/{id}/change-class
DELETE /admin/students/{id}
GET    /admin/students/by-class/{class_number}
GET    /admin/students/distribution
```

**Управление кодами:**
```
POST /admin/codes/upload-csv
POST /admin/codes/distribute/{session_id}
GET  /admin/codes/available/{session_id}
POST /admin/codes/reassign/{code_id}
GET  /admin/codes/export/class/{session_id}/{class_number}
GET  /admin/codes/export/all/{session_id}
GET  /admin/codes/sessions
POST /admin/codes/sessions/{session_id}/activate
```

---

### 🎨 Интерфейс

**Обновленная админ-панель (`dashboard_v2.html`):**

**Новые вкладки:**
1. **Дашборд** - Общая статистика
2. **Ученики** - Управление учениками
3. **Коды** - Управление кодами олимпиад
4. **Экспорт** - Выгрузка данных

**Возможности:**
- Drag & Drop загрузка файлов
- Фильтрация по классам
- Выбор режима распределения
- Экспорт одним кликом

---

### 🔧 Утилиты и скрипты

**Новые скрипты:**

`scripts/migrate_to_new_structure.py`:
- Миграция из старой структуры БД
- Безопасная миграция с проверками
- Опциональное удаление старых таблиц

**Обновленные модули:**

`utils/student_management.py`:
- Класс StudentManager
- CRUD операции
- Автоматическая сверка

`utils/code_distribution.py`:
- Класс CodeDistributor
- Логика распределения
- Резервирование

`utils/export.py`:
- Класс CodeExporter
- CSV и ZIP экспорт
- Сводная статистика

---

### 📚 Документация

**Новые документы:**
- `UPGRADE_GUIDE.md` - Руководство по обновлению
- `CHANGELOG_V2.md` - Список изменений
- Обновлен `README.md` с новыми возможностями

---

### ⚠️ Breaking Changes

1. **Структура БД:** Требуется миграция
2. **API эндпоинты:** Некоторые эндпоинты изменены
3. **Модели данных:** Student теперь требует class_number

### 🔄 Миграция

Для обновления с v1.x на v2.0:

```bash
# 1. Backup
pg_dump olympus_bot > backup.sql

# 2. Миграция
python scripts/migrate_to_new_structure.py

# 3. Тестирование
python scripts/system_check.py
```

---

### 🐛 Исправленные ошибки

- Исправлена проблема с распределением кодов 9 класса
- Улучшена валидация данных при парсинге
- Исправлены race conditions при одновременных запросах

---

### 🚀 Производительность

- Оптимизированы запросы к БД
- Кэширование статистики
- Batch операции для массовой загрузки

---

### 📋 TODO для следующих версий

- [ ] PDF экспорт для печати
- [ ] Расширенная аналитика
- [ ] Push-уведомления администратору
- [ ] Мобильное приложение для учителей
- [ ] Интеграция с электронным журналом

---

## 🎯 Рекомендации по использованию

1. **Начните с малого:** Загрузите один класс для тестирования
2. **Используйте on-demand:** Для первых олимпиад
3. **Регулярный backup:** Настройте автоматическое резервное копирование
4. **Мониторинг:** Следите за логами в первые недели

---

## 👥 Участники

- Разработка: Claude (Anthropic)
- Тестирование: Ваша команда
- Обратная связь: Сообщество пользователей

---

**Дата релиза:** 2025-01-07
**Версия:** 2.0.0
**Статус:** Stable