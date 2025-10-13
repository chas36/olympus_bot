# ⚠️ Требуется исправление базы данных

## Проблема

При загрузке CSV кодов возникает ошибка:
```
null value in column "student_id" of relation "grade8_codes" violates not-null constraint
```

## Причина

В базе данных поле `grade8_codes.student_id` имеет constraint NOT NULL, но в коде модели это поле установлено как `nullable=True`. База данных не была обновлена после изменения модели.

## Решение

### Вариант 1: SQL скрипт (быстрое исправление)

```bash
# Подключитесь к PostgreSQL
psql -U postgres olympus_bot

# Выполните команду
ALTER TABLE grade8_codes ALTER COLUMN student_id DROP NOT NULL;

# Проверьте изменения
\d grade8_codes

# Выйдите
\q
```

### Вариант 2: Используйте готовый SQL файл

```bash
# Выполните SQL скрипт
psql -U postgres olympus_bot < fix_grade8_codes.sql
```

### Вариант 3: Пересоздать базу данных (если тестовая среда)

```bash
# ВНИМАНИЕ: Это удалит все данные!

# Подключитесь к PostgreSQL
psql -U postgres

# Удалите базу
DROP DATABASE IF EXISTS olympus_bot;

# Создайте заново
CREATE DATABASE olympus_bot;

# Выйдите
\q

# Запустите бота для автоматического создания таблиц
python bot/main.py
# (нажмите Ctrl+C после создания таблиц)
```

---

## После исправления

1. Перезапустите API сервер:
```bash
python api/main.py
```

2. Попробуйте загрузить CSV файлы снова через веб-панель:
   - Откройте http://localhost:8000/
   - Перейдите на таб "🔑 Коды"
   - Выберите CSV файлы
   - Нажмите "Загрузить коды"

---

## Проверка что исправление сработало

```bash
# Подключитесь к базе
psql -U postgres olympus_bot

# Проверьте структуру таблицы
\d grade8_codes

# Должно быть:
# student_id | integer | | nullable
#            ^^^^^^^^^^^^ должно быть без "not null"

# Выйдите
\q
```

---

## Почему это произошло?

1. Модель в коде была изменена: `student_id` стал `nullable=True` (строка 58 в `database/models.py`)
2. База данных не была обновлена автоматически
3. SQLAlchemy не создает миграции автоматически - нужно либо использовать Alembic, либо вручную изменять схему

---

## Предотвращение в будущем

### Используйте Alembic для миграций

```bash
# Установите Alembic
pip install alembic

# Инициализируйте
alembic init alembic

# Создайте миграцию
alembic revision --autogenerate -m "Make student_id nullable in grade8_codes"

# Примените миграцию
alembic upgrade head
```

### Или используйте автосоздание таблиц при разработке

В `database/database.py` можно добавить:

```python
async def init_db():
    async with engine.begin() as conn:
        # Пересоздает все таблицы при каждом запуске (только для разработки!)
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
```

⚠️ **ВНИМАНИЕ**: Это удалит все данные! Используйте только в разработке.

---

## Нужна помощь?

Если возникли проблемы с PostgreSQL:

```bash
# Проверьте что PostgreSQL запущен
brew services list | grep postgresql
# или
sudo systemctl status postgresql

# Запустите если не запущен
brew services start postgresql
# или
sudo systemctl start postgresql

# Проверьте подключение
psql -U postgres -c "SELECT version();"
```

---

**Статус**: ⚠️ Требует действия
**Приоритет**: Высокий (блокирует загрузку кодов)
**Решение**: 1 минута (одна SQL команда)
