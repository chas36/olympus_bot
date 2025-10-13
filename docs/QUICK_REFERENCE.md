# 🚀 Quick Reference - Olympus Bot v2.0

## Запуск системы

### 1. Запуск API сервера
```bash
python api/main.py
```
или
```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Запуск Telegram бота
```bash
python bot/main.py
```

### 3. Доступ к веб-дашборду
```
http://localhost:8000/
```

### 4. API документация (Swagger)
```
http://localhost:8000/docs
```

---

## 🎯 Быстрые ссылки

| Что нужно | Где найти |
|-----------|-----------|
| 🌐 Веб-дашборд | http://localhost:8000/ |
| 📚 API Swagger | http://localhost:8000/docs |
| 📖 API ReDoc | http://localhost:8000/redoc |
| 🔍 Health Check | http://localhost:8000/health |
| ℹ️ API Info | http://localhost:8000/api/info |

---

## 📊 Основные API эндпоинты

### Статистика
```bash
# Общая статистика
GET http://localhost:8000/api/admin/statistics/overview

# Статистика по олимпиаде
GET http://localhost:8000/api/admin/statistics/olympiad/{id}
```

### Ученики
```bash
# Все ученики
GET http://localhost:8000/api/students

# Зарегистрированные
GET http://localhost:8000/api/admin/students/registered

# Незарегистрированные
GET http://localhost:8000/api/admin/students/unregistered

# Удалить ученика
DELETE http://localhost:8000/api/admin/students/{id}
```

### Классы
```bash
# Все классы
GET http://localhost:8000/api/admin/classes

# Ученики класса
GET http://localhost:8000/api/admin/classes/{number}/students

# Удалить класс
DELETE http://localhost:8000/api/admin/classes/{number}
```

### Олимпиады
```bash
# Все олимпиады
GET http://localhost:8000/api/admin/olympiads

# Активировать олимпиаду
POST http://localhost:8000/api/admin/olympiads/{id}/activate

# Удалить олимпиаду
DELETE http://localhost:8000/api/admin/olympiads/{id}
```

### Экспорт
```bash
# CSV
GET http://localhost:8000/api/admin/export/students

# Excel ученики
GET http://localhost:8000/api/admin/export/students/excel

# Excel олимпиады
GET http://localhost:8000/api/admin/export/olympiads/excel

# Excel статистика
GET http://localhost:8000/api/admin/export/statistics/excel
```

---

## 🤖 Telegram бот команды

### Основные
```
/start - Регистрация ученика
/help - Помощь
/admin - Админ-панель (только для админов)
```

### Админ-панель (через кнопки)
```
/admin → 📊 Статистика
/admin → 👥 Ученики
/admin → 🎓 Классы
/admin → 🏆 Олимпиады
/admin → 📥 Экспорт
```

---

## 📁 Структура проекта

```
olympus_bot/
├── api/
│   ├── main.py                    # FastAPI приложение
│   └── routers/
│       ├── admin.py               # Админ API (CRUD + статистика)
│       ├── dashboard.py           # Веб-дашборд роутер
│       ├── students.py            # API учеников
│       ├── codes.py               # API кодов
│       └── monitoring.py          # API мониторинга
├── bot/
│   ├── main.py                    # Telegram бот
│   ├── keyboards.py               # Клавиатуры бота
│   └── handlers/
│       ├── admin.py               # Базовые админ функции
│       ├── admin_extended.py      # Управление учениками/классами
│       └── admin_olympiads.py     # Управление олимпиадами
├── database/
│   ├── models.py                  # SQLAlchemy модели
│   └── crud.py                    # CRUD операции
├── templates/
│   └── dashboard.html             # Веб-дашборд (Chart.js)
├── utils/
│   ├── admin_logger.py            # Логирование действий
│   ├── admin_notifications.py     # Уведомления админам
│   └── excel_export.py            # Excel экспорт
├── docs/
│   ├── API_DOCUMENTATION.md       # Полная API документация
│   ├── ADMIN_PANEL_V2.md          # Документация админ-панели
│   └── ...
├── .env                           # Конфигурация
└── logs/
    ├── bot.log                    # Логи бота
    └── admin_actions.log          # Логи админских действий
```

---

## ⚙️ Конфигурация (.env)

### Обязательные параметры
```env
# Telegram
BOT_TOKEN=your_bot_token_here
ADMIN_TELEGRAM_ID=123456789
ADMIN_IDS=123456789,987654321

# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/olympus_bot

# API (опционально)
API_HOST=0.0.0.0
API_PORT=8000
```

---

## 🔧 Частые задачи

### Добавить админа
1. Откройте `.env`
2. Найдите строку `ADMIN_IDS`
3. Добавьте новый ID через запятую: `ADMIN_IDS=123456789,987654321,111222333`
4. Перезапустите бота

### Экспорт всех данных в Excel
**Веб-дашборд:**
- Откройте http://localhost:8000/
- Кнопка "📊 Экспорт статистики"

**Telegram бот:**
```
/admin → 📥 Экспорт → 📊 Статистика (Excel)
```

**API:**
```bash
curl -o stats.xlsx http://localhost:8000/api/admin/export/statistics/excel
```

### Очистить базу учеников
**⚠️ ОСТОРОЖНО! Удалит всех учеников!**

**Telegram бот:**
```
/admin → 👥 Ученики → 🗑 Очистить БД → Подтвердить
```

**API:**
```bash
curl -X DELETE "http://localhost:8000/api/admin/students?confirm=YES_DELETE_ALL"
```

### Активировать олимпиаду
**Telegram бот:**
```
/admin → 🏆 Олимпиады → ✅ Активировать → Выбрать олимпиаду
```

**API:**
```bash
curl -X POST http://localhost:8000/api/admin/olympiads/5/activate
```

---

## 📊 Логи и мониторинг

### Просмотр логов бота
```bash
tail -f logs/bot.log
```

### Просмотр логов админских действий
```bash
tail -f logs/admin_actions.log
```

### Просмотр логов API (console)
```bash
# Логи выводятся в консоль при запуске с --reload
uvicorn api.main:app --reload
```

---

## 🐛 Troubleshooting

### Бот не отвечает
```bash
# Проверьте процесс
ps aux | grep "python bot/main.py"

# Проверьте логи
tail -50 logs/bot.log

# Проверьте BOT_TOKEN в .env
```

### API не запускается
```bash
# Проверьте порт занят или нет
lsof -i :8000

# Убейте процесс если нужно
kill -9 $(lsof -t -i:8000)

# Перезапустите
python api/main.py
```

### База данных не доступна
```bash
# Проверьте PostgreSQL
psql -U postgres -c "SELECT 1"

# Проверьте DATABASE_URL в .env
# Создайте базу если нужно
createdb olympus_bot
```

### Кнопки админ-панели не работают
```bash
# Проверьте ADMIN_IDS в .env
# Формат: ADMIN_IDS=123456789,987654321 (без пробелов!)

# Узнайте свой Telegram ID
# Напишите @userinfobot в Telegram
```

### Excel не генерируется
```bash
# Установите openpyxl
pip install openpyxl

# Проверьте версию
python -c "import openpyxl; print(openpyxl.__version__)"
```

### Дашборд показывает пустые данные
```bash
# Проверьте что API запущен
curl http://localhost:8000/health

# Проверьте эндпоинт статистики
curl http://localhost:8000/api/admin/statistics/overview

# Откройте консоль браузера (F12) и проверьте ошибки
```

---

## 📚 Документация

| Документ | Описание |
|----------|----------|
| `API_DOCUMENTATION.md` | Полная API документация с примерами |
| `ADMIN_PANEL_V2.md` | Telegram бот - админ-панель v2 |
| `ADMIN_QUICKSTART.md` | Быстрый старт для админов |
| `DASHBOARD_UPDATE_SUMMARY.md` | Обзор обновления веб-дашборда |
| `QUICK_REFERENCE.md` | Этот файл - быстрая справка |

---

## 🔐 Безопасность

### Development (текущая конфигурация)
- ✅ Логирование всех админских действий
- ✅ Подтверждение критичных операций
- ✅ Уведомления администраторов
- ⚠️ Без аутентификации API
- ⚠️ CORS открыт для всех

### Production рекомендации
1. Добавить JWT аутентификацию
2. Настроить CORS для конкретных доменов
3. Использовать HTTPS/SSL
4. Rate limiting
5. Firewall правила
6. Backup базы данных

---

## 💡 Полезные команды

### Git
```bash
# Проверить изменения
git status

# Коммит изменений
git add .
git commit -m "feat: Updated admin dashboard with statistics and charts"

# Запушить на GitHub
git push origin main
```

### Python
```bash
# Установить зависимости
pip install -r requirements.txt

# Проверить синтаксис
python3 -m py_compile api/main.py

# Запустить с переменными окружения
python -m uvicorn api.main:app --env-file .env
```

### PostgreSQL
```bash
# Подключиться к базе
psql -U postgres olympus_bot

# Экспорт базы
pg_dump olympus_bot > backup.sql

# Импорт базы
psql olympus_bot < backup.sql

# Список таблиц
\dt
```

---

## 🎉 Быстрые тесты

### Тест API
```bash
# Health check
curl http://localhost:8000/health

# Статистика
curl http://localhost:8000/api/admin/statistics/overview

# Список учеников
curl http://localhost:8000/api/students
```

### Тест веб-дашборда
1. Откройте http://localhost:8000/
2. Должны загрузиться карточки статистики
3. График классов должен отобразиться
4. Таблица олимпиад должна загрузиться

### Тест бота
1. Напишите боту `/start`
2. Напишите `/admin` (если вы админ)
3. Нажмите кнопку "📊 Статистика"
4. Должна прийти статистика

### Тест уведомлений
**Веб-дашборд:**
- Кнопка "🔔 Тест уведомлений"

**API:**
```bash
curl -X POST http://localhost:8000/api/admin/notifications/test
```

Всем админам из `ADMIN_IDS` должно прийти тестовое сообщение.

---

## 📞 Поддержка

Если возникли проблемы:

1. **Проверьте логи**: `logs/bot.log`, `logs/admin_actions.log`
2. **Проверьте документацию**: `docs/` директория
3. **Проверьте .env**: Все ли переменные заполнены?
4. **Перезапустите**: Иногда помогает простой рестарт

---

**Версия**: 2.0.0
**Последнее обновление**: Октябрь 2025
**Статус**: ✅ Ready to use
