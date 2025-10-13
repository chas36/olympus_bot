# API Documentation - Olympus Bot v2.0

## Обзор

Olympus Bot API v2.0 предоставляет полный набор REST API эндпоинтов для управления олимпиадами, учениками, кодами доступа и статистикой.

**Base URL**: `http://localhost:8000`
**API Base**: `/api`
**Admin API**: `/api/admin`

## Аутентификация

В текущей версии API не требует аутентификации для локального использования. В production рекомендуется добавить JWT или API ключи.

---

## Основные эндпоинты

### Health Check

**GET** `/health`

Проверка работоспособности API.

**Response:**
```json
{
  "status": "ok",
  "version": "2.0.0",
  "message": "Olympus Bot API v2 is running"
}
```

### API Information

**GET** `/api/info`

Информация о возможностях API.

**Response:**
```json
{
  "name": "Olympus Bot API",
  "version": "2.0.0",
  "features": [
    "Управление учениками",
    "Загрузка из Excel и CSV",
    "Автоматическое резервирование кодов 9→8",
    "Мониторинг в реальном времени",
    "Экспорт данных"
  ]
}
```

---

## 📊 Статистика и Мониторинг

### Общая статистика системы

**GET** `/api/admin/statistics/overview`

Получить обзорную статистику по всей системе.

**Response:**
```json
{
  "students": {
    "total": 150,
    "registered": 120,
    "unregistered": 30
  },
  "olympiads": {
    "total": 12,
    "active": 1,
    "inactive": 11
  },
  "classes": [
    {
      "class_number": 9,
      "total": 50,
      "registered": 45,
      "unregistered": 5
    }
  ],
  "active_olympiad": {
    "id": 5,
    "subject": "Математика",
    "date": "2025-10-15",
    "class_number": 9
  }
}
```

### Детальная статистика по олимпиаде

**GET** `/api/admin/statistics/olympiad/{session_id}`

Получить подробную статистику по конкретной олимпиаде.

**Path Parameters:**
- `session_id` (int): ID олимпиады

**Response:**
```json
{
  "olympiad": {
    "id": 5,
    "subject": "Математика",
    "date": "2025-10-15",
    "class_number": 9,
    "is_active": true
  },
  "codes_grade8": {
    "total": 120,
    "issued": 95,
    "remaining": 25,
    "usage_percent": 79.17
  },
  "codes_grade9": {
    "total": 80,
    "used": 65,
    "available": 15,
    "usage_percent": 81.25
  },
  "requests": {
    "total": 95,
    "with_screenshot": 88,
    "completion_rate": 92.63
  }
}
```

### Список зарегистрированных учеников

**GET** `/api/admin/students/registered`

Получить список всех зарегистрированных в боте учеников.

**Query Parameters:**
- `limit` (int, optional): Ограничение количества (default: 100)

**Response:**
```json
[
  {
    "id": 1,
    "full_name": "Иванов Иван Иванович",
    "class_number": 9,
    "parallel": "А",
    "telegram_id": 123456789,
    "telegram_username": "ivanov_ivan",
    "registered_at": "2025-10-01T10:30:00"
  }
]
```

### Список незарегистрированных учеников

**GET** `/api/admin/students/unregistered`

Получить список учеников из базы, которые еще не зарегистрировались в боте.

**Response:**
```json
[
  {
    "id": 45,
    "full_name": "Петров Петр Петрович",
    "class_number": 10,
    "parallel": "Б",
    "telegram_id": null,
    "telegram_username": null
  }
]
```

---

## 👥 Управление учениками

### Получить список всех учеников

**GET** `/api/students`

**Query Parameters:**
- `skip` (int): Пропустить N записей (default: 0)
- `limit` (int): Ограничение количества (default: 100)
- `class_number` (int, optional): Фильтр по классу
- `registered_only` (bool, optional): Только зарегистрированные

**Response:**
```json
[
  {
    "id": 1,
    "full_name": "Иванов Иван Иванович",
    "class_number": 9,
    "parallel": "А",
    "telegram_id": 123456789,
    "telegram_username": "ivanov_ivan",
    "registered_at": "2025-10-01T10:30:00"
  }
]
```

### Получить ученика по ID

**GET** `/api/admin/students/{student_id}`

**Path Parameters:**
- `student_id` (int): ID ученика

**Response:**
```json
{
  "id": 1,
  "full_name": "Иванов Иван Иванович",
  "class_number": 9,
  "parallel": "А",
  "telegram_id": 123456789
}
```

### Удалить ученика

**DELETE** `/api/admin/students/{student_id}`

Удалить ученика из системы.

**Path Parameters:**
- `student_id` (int): ID ученика

**Query Parameters:**
- `force` (bool, optional): Принудительное удаление с историей (default: false)

**Response:**
```json
{
  "success": true,
  "message": "Ученик удален",
  "student_id": 1
}
```

### Очистить всю базу учеников

**DELETE** `/api/admin/students`

⚠️ **КРИТИЧНАЯ ОПЕРАЦИЯ**: Удаляет всех учеников из базы данных.

**Query Parameters:**
- `confirm` (string, required): Должно быть равно `"YES_DELETE_ALL"` для подтверждения

**Response:**
```json
{
  "success": true,
  "message": "База данных учеников очищена",
  "deleted_count": 150
}
```

---

## 🎓 Управление классами

### Получить список всех классов

**GET** `/api/admin/classes`

Получить список всех классов с количеством учеников.

**Response:**
```json
[
  {
    "class_number": 9,
    "total_students": 50,
    "registered": 45,
    "unregistered": 5
  },
  {
    "class_number": 10,
    "total_students": 45,
    "registered": 40,
    "unregistered": 5
  }
]
```

### Получить учеников класса

**GET** `/api/admin/classes/{class_number}/students`

Получить список всех учеников определенного класса.

**Path Parameters:**
- `class_number` (int): Номер класса (4-11)

**Response:**
```json
[
  {
    "id": 1,
    "full_name": "Иванов Иван Иванович",
    "class_number": 9,
    "parallel": "А",
    "telegram_id": 123456789
  }
]
```

### Удалить весь класс

**DELETE** `/api/admin/classes/{class_number}`

⚠️ **КРИТИЧНАЯ ОПЕРАЦИЯ**: Удаляет всех учеников класса.

**Path Parameters:**
- `class_number` (int): Номер класса

**Response:**
```json
{
  "success": true,
  "message": "Класс удален",
  "class_number": 9,
  "deleted_count": 50
}
```

---

## 🏆 Управление олимпиадами

### Получить список всех олимпиад

**GET** `/api/admin/olympiads`

**Query Parameters:**
- `active_only` (bool, optional): Только активные олимпиады

**Response:**
```json
[
  {
    "id": 5,
    "subject": "Математика",
    "date": "2025-10-15",
    "class_number": 9,
    "is_active": true,
    "created_at": "2025-10-01T10:00:00"
  }
]
```

### Удалить олимпиаду

**DELETE** `/api/admin/olympiads/{session_id}`

**Path Parameters:**
- `session_id` (int): ID олимпиады

**Response:**
```json
{
  "success": true,
  "message": "Олимпиада удалена",
  "session_id": 5
}
```

### Активировать олимпиаду

**POST** `/api/admin/olympiads/{session_id}/activate`

Активировать олимпиаду (все остальные будут деактивированы).

**Path Parameters:**
- `session_id` (int): ID олимпиады

**Response:**
```json
{
  "success": true,
  "message": "Олимпиада активирована",
  "olympiad": {
    "id": 5,
    "subject": "Математика",
    "is_active": true
  }
}
```

---

## 🔔 Уведомления

### Тестовое уведомление

**POST** `/api/admin/notifications/test`

Отправить тестовое уведомление всем администраторам.

**Response:**
```json
{
  "success": true,
  "message": "Тестовое уведомление отправлено всем администраторам",
  "admins_notified": 2
}
```

---

## 📥 Экспорт данных

### Экспорт учеников в CSV

**GET** `/api/admin/export/students`

Скачать список всех учеников в формате CSV.

**Response Headers:**
- `Content-Type: text/csv`
- `Content-Disposition: attachment; filename="students.csv"`

### Экспорт учеников в Excel

**GET** `/api/admin/export/students/excel`

Скачать список всех учеников в формате Excel с форматированием.

**Response Headers:**
- `Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- `Content-Disposition: attachment; filename="students_export.xlsx"`

**Excel Features:**
- Цветные заголовки
- Автоширина колонок
- Форматирование даты
- Фильтры

### Экспорт олимпиад в Excel

**GET** `/api/admin/export/olympiads/excel`

Скачать список всех олимпиад в формате Excel.

### Экспорт статистики в Excel

**GET** `/api/admin/export/statistics/excel`

Скачать полную статистику системы в многостраничном Excel файле.

**Excel Sheets:**
1. **Обзор** - общая статистика
2. **Ученики** - список всех учеников
3. **Классы** - статистика по классам
4. **Олимпиады** - список олимпиад с кодами

---

## 📝 Коды доступа

### Получить код для ученика

**POST** `/api/codes/request`

Запросить код доступа для ученика.

**Request Body:**
```json
{
  "telegram_id": 123456789
}
```

**Response:**
```json
{
  "success": true,
  "code": "ABC123XYZ",
  "type": "grade9",
  "olympiad": "Математика",
  "message": "Код для участия"
}
```

### Загрузить скриншот

**POST** `/api/screenshots/upload`

Загрузить скриншот выполненного задания.

**Request Body (multipart/form-data):**
- `telegram_id` (int): ID ученика в Telegram
- `file` (file): Скриншот

**Response:**
```json
{
  "success": true,
  "message": "Скриншот загружен",
  "screenshot_id": 42
}
```

---

## 🌐 Веб-интерфейс

### Админ-панель (Dashboard)

**GET** `/`

Открыть современную веб-панель администратора с графиками и статистикой.

**Features:**
- 📊 Живая статистика в реальном времени
- 📈 Графики по классам (Chart.js)
- 🏆 Интерактивная таблица олимпиад
- 👥 Список недавно зарегистрированных
- 🔄 Автообновление каждые 30 секунд
- 📥 Кнопки экспорта (CSV/Excel)

### API Documentation (Swagger)

**GET** `/docs`

Интерактивная документация API (Swagger UI).

**GET** `/redoc`

Альтернативная документация API (ReDoc).

---

## Коды ошибок

### HTTP Status Codes

- **200 OK** - Успешный запрос
- **201 Created** - Ресурс создан
- **400 Bad Request** - Некорректный запрос
- **404 Not Found** - Ресурс не найден
- **500 Internal Server Error** - Внутренняя ошибка сервера

### Error Response Format

```json
{
  "detail": "Описание ошибки"
}
```

### Примеры ошибок

**404 Not Found:**
```json
{
  "detail": "Ученик с ID 999 не найден"
}
```

**400 Bad Request:**
```json
{
  "detail": "Для удаления всех учеников требуется подтверждение: confirm=YES_DELETE_ALL"
}
```

---

## Примеры использования

### Python (requests)

```python
import requests

BASE_URL = "http://localhost:8000"

# Получить статистику
response = requests.get(f"{BASE_URL}/api/admin/statistics/overview")
stats = response.json()
print(f"Всего учеников: {stats['students']['total']}")

# Удалить ученика
response = requests.delete(f"{BASE_URL}/api/admin/students/42")
print(response.json())

# Экспорт в Excel
response = requests.get(f"{BASE_URL}/api/admin/export/students/excel")
with open("students.xlsx", "wb") as f:
    f.write(response.content)
```

### JavaScript (fetch)

```javascript
const BASE_URL = "http://localhost:8000";

// Получить статистику
const response = await fetch(`${BASE_URL}/api/admin/statistics/overview`);
const stats = await response.json();
console.log(`Всего учеников: ${stats.students.total}`);

// Активировать олимпиаду
const activateResponse = await fetch(
  `${BASE_URL}/api/admin/olympiads/5/activate`,
  { method: 'POST' }
);
const result = await activateResponse.json();
console.log(result.message);
```

### cURL

```bash
# Получить статистику
curl http://localhost:8000/api/admin/statistics/overview

# Удалить ученика
curl -X DELETE http://localhost:8000/api/admin/students/42

# Очистить базу учеников (с подтверждением)
curl -X DELETE "http://localhost:8000/api/admin/students?confirm=YES_DELETE_ALL"

# Скачать Excel
curl -o students.xlsx http://localhost:8000/api/admin/export/students/excel
```

---

## Безопасность

### Рекомендации для Production

1. **Добавить аутентификацию**: JWT токены или API ключи
2. **HTTPS обязателен**: Используйте SSL/TLS сертификаты
3. **Rate Limiting**: Ограничение количества запросов
4. **CORS**: Настроить разрешенные origins
5. **Валидация**: Строгая валидация всех входных данных
6. **Логирование**: Детальное логирование всех критичных операций

### Критичные операции

Следующие операции требуют особой осторожности:

- ⚠️ `DELETE /api/admin/students` - очистка всей базы
- ⚠️ `DELETE /api/admin/classes/{class_number}` - удаление класса
- ⚠️ `DELETE /api/admin/olympiads/{session_id}` - удаление олимпиады

Все критичные операции логируются в `logs/admin_actions.log`.

---

## Поддержка

- **Логи**: `logs/bot.log`, `logs/admin_actions.log`
- **GitHub**: [Olympus Bot Repository](https://github.com/your-repo)
- **Документация бота**: `docs/ADMIN_PANEL_V2.md`
- **Быстрый старт**: `ADMIN_QUICKSTART.md`

---

**Версия**: 2.0.0
**Дата обновления**: Октябрь 2025
**Разработчик**: Olympus Bot Team
