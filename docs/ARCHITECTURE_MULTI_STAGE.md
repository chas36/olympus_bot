# Архитектура многоэтапной системы олимпиад

## Обзор

Система должна поддерживать несколько этапов олимпиад с возможностью переключения между ними:
- **Школьный этап** (текущая реализация)
- **Муниципальный этап** (планируется)

## 1. Структура базы данных

### 1.1 Новая таблица `olympiad_stages`

```sql
CREATE TABLE olympiad_stages (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,  -- "Школьный этап", "Муниципальный этап"
    code VARCHAR(50) UNIQUE NOT NULL,  -- "school", "municipal"
    description TEXT,
    is_active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 1.2 Обновление существующих таблиц

**olympiad_sessions:**
```sql
ALTER TABLE olympiad_sessions
ADD COLUMN stage_id INTEGER REFERENCES olympiad_stages(id);
```

**students:**
```sql
-- Ученики могут участвовать в разных этапах
-- Связь many-to-many через участие в сессиях
```

## 2. Архитектура переключения этапов

### 2.1 Варианты реализации

#### Вариант A: Глобальный переключатель (рекомендуется)
- Один активный этап в текущий момент времени
- Переключение через настройки в админ-панели
- Простая реализация, минимум изменений

```python
# config/settings.py
class StageConfig:
    ACTIVE_STAGE = "school"  # или "municipal"
```

#### Вариант B: Параллельная работа
- Несколько этапов активны одновременно
- Переключение через URL параметр или сессию
- Требует больше изменений в коде

```
http://localhost:8000/?stage=school
http://localhost:8000/?stage=municipal
```

### 2.2 Рекомендуемый подход: Вариант A + контекст

```python
# utils/stage_context.py
class StageContext:
    def __init__(self, stage_code: str):
        self.stage_code = stage_code
        self.stage = get_stage_by_code(stage_code)

    def get_active_session(self):
        """Получить активную сессию для текущего этапа"""
        return db.query(OlympiadSession).filter(
            OlympiadSession.is_active == True,
            OlympiadSession.stage_id == self.stage.id
        ).first()
```

## 3. Веб-интерфейс

### 3.1 Переключатель в навбаре

```html
<div class="dropdown">
    <button class="btn btn-light dropdown-toggle" type="button" data-bs-toggle="dropdown">
        <i class="bi bi-trophy"></i> Школьный этап
    </button>
    <ul class="dropdown-menu">
        <li><a class="dropdown-item" href="#" onclick="switchStage('school')">
            Школьный этап
        </a></li>
        <li><a class="dropdown-item" href="#" onclick="switchStage('municipal')">
            Муниципальный этап
        </a></li>
    </ul>
</div>
```

### 3.2 Индикация текущего этапа

- Цветовое кодирование navbar
- Иконка рядом с названием
- Водяной знак на странице

## 4. Telegram бот

### 4.1 Команды для учеников

```python
/stage - Узнать текущий этап
/get_code - Получить код (автоматически для текущего этапа)
/my_stages - Показать этапы, в которых участвовал
```

### 4.2 Логика работы

1. При запросе кода бот проверяет активный этап
2. Выдает код только для активного этапа
3. История кодов хранится с привязкой к этапу

## 5. API изменения

### 5.1 Новые endpoints

```python
# Управление этапами
GET  /api/stages              # Список всех этапов
GET  /api/stages/active       # Активный этап
POST /api/stages/{id}/activate # Активировать этап

# Фильтрация по этапам
GET /api/sessions?stage=school
GET /api/students?stage=municipal
```

### 5.2 Изменение существующих endpoints

Все запросы автоматически фильтруются по активному этапу:
```python
@router.get("/api/monitoring/dashboard")
async def get_dashboard():
    stage = get_active_stage()
    # ... фильтрация по stage_id
```

## 6. Миграция данных

### 6.1 Шаги миграции

```bash
# 1. Создать таблицу этапов
alembic revision --autogenerate -m "Add olympiad stages"

# 2. Заполнить начальными данными
INSERT INTO olympiad_stages (name, code, is_active) VALUES
('Школьный этап', 'school', TRUE),
('Муниципальный этап', 'municipal', FALSE);

# 3. Обновить существующие сессии
UPDATE olympiad_sessions
SET stage_id = (SELECT id FROM olympiad_stages WHERE code = 'school')
WHERE stage_id IS NULL;
```

## 7. Безопасность и изоляция

### 7.1 Изоляция данных

- Коды одного этапа не видны в другом
- Статистика раздельная для каждого этапа
- Экспорт данных с указанием этапа

### 7.2 Права доступа

```python
# Администратор может:
- Переключать этапы
- Видеть все этапы
- Управлять любым этапом

# Учитель может:
- Видеть только свой этап
- Управлять только своим этапом
```

## 8. План реализации

### Фаза 1: Подготовка (1-2 часа)
- [ ] Создать таблицу olympiad_stages
- [ ] Добавить поле stage_id в olympiad_sessions
- [ ] Заполнить начальными данными
- [ ] Обновить модели SQLAlchemy

### Фаза 2: Backend (2-3 часа)
- [ ] Добавить StageContext
- [ ] Обновить CRUD функции с фильтрацией по этапам
- [ ] Создать API endpoints для управления этапами
- [ ] Обновить существующие endpoints

### Фаза 3: Frontend (2-3 часа)
- [ ] Добавить переключатель этапов в навбар
- [ ] Обновить дашборд для показа текущего этапа
- [ ] Добавить индикацию этапа на всех страницах
- [ ] Обновить экспорт данных

### Фаза 4: Bot (1-2 часа)
- [ ] Обновить команду /get_code
- [ ] Добавить команду /stage
- [ ] Обновить уведомления

### Фаза 5: Тестирование (1-2 часа)
- [ ] Протестировать переключение этапов
- [ ] Проверить изоляцию данных
- [ ] Провести нагрузочное тестирование

## 9. Особенности муниципального этапа

### Отличия от школьного:

1. **Участники**: Только отобранные ученики
2. **Коды**: Выдаются заранее, не по запросу
3. **Мониторинг**: Более детальный
4. **Отчетность**: Дополнительные отчеты для управления образования

### Дополнительные функции:

```python
# Импорт участников муниципального этапа
POST /api/municipal/import-participants

# Генерация отчетов для УО
GET /api/municipal/reports/summary
GET /api/municipal/reports/by-school
```

## 10. Конфигурация через .env

```bash
# Текущий активный этап
ACTIVE_STAGE=school  # или municipal

# Разрешить параллельную работу этапов
ALLOW_PARALLEL_STAGES=false

# Автопереключение на следующий этап
AUTO_STAGE_TRANSITION=false
```

## 11. Пример использования

```python
# В коде API
from utils.stage_context import get_active_stage

@router.get("/api/sessions")
async def get_sessions(db: Session = Depends(get_db)):
    stage = get_active_stage(db)
    sessions = db.query(OlympiadSession).filter(
        OlympiadSession.stage_id == stage.id
    ).all()
    return sessions

# В боте
async def cmd_get_code(message: Message):
    stage = get_active_stage()
    if stage.code == "school":
        # Логика школьного этапа
        pass
    elif stage.code == "municipal":
        # Логика муниципального этапа
        pass
```

## 12. Визуализация

```
┌─────────────────────────────────────────┐
│  Olympus Bot - [Школьный этап ▼]       │
├─────────────────────────────────────────┤
│                                         │
│  📊 Статистика школьного этапа          │
│  👥 Ученики: 120                        │
│  📝 Олимпиады: 5                        │
│  ✅ Завершено: 3                        │
│                                         │
└─────────────────────────────────────────┘

       ↓ Переключение

┌─────────────────────────────────────────┐
│  Olympus Bot - [Муниципальный этап ▼]  │
├─────────────────────────────────────────┤
│                                         │
│  📊 Статистика муниципального этапа     │
│  👥 Участники: 25                       │
│  📝 Олимпиады: 2                        │
│  ✅ Завершено: 1                        │
│                                         │
└─────────────────────────────────────────┘
```

## Заключение

Эта архитектура обеспечивает:
- ✅ Гибкость переключения между этапами
- ✅ Изоляцию данных
- ✅ Минимальные изменения в существующем коде
- ✅ Возможность расширения на другие этапы (региональный, всероссийский)
- ✅ Простоту использования для администраторов

**Рекомендация**: Начать с реализации глобального переключателя (Вариант A), затем при необходимости добавить параллельную работу.
