# 🏆 Olympus Bot - Система управления олимпиадами

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)](https://fastapi.tiangolo.com/)
[![aiogram](https://img.shields.io/badge/aiogram-3.3-blue.svg)](https://docs.aiogram.dev/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Автоматизированная система для распределения кодов доступа к олимпиадам и контроля выполнения работ через Telegram-бота.

📖 **[Быстрый старт](QUICKSTART.md)** | 📚 **[Полная документация](README_FULL.md)**

## 📋 Возможности

### Для учеников:
- ✅ Регистрация по одноразовому коду
- 📝 Получение кодов для олимпиад (8 или 9 класс)
- 📸 Отправка скриншотов завершенных работ
- ⏰ Автоматические напоминания о необходимости отправить скриншот

### Для администратора:
- 📤 Загрузка файлов .docx с кодами олимпиад
- 👥 Управление учениками и генерация регистрационных кодов
- 📊 Мониторинг статуса выполнения работ в реальном времени
- 🖼️ Просмотр скриншотов учеников
- 📈 Статистика по запросам и выполнению работ
- 📥 Экспорт данных в CSV

## 🛠️ Технологический стек

- **Backend**: Python 3.11+ / FastAPI / SQLAlchemy
- **Database**: PostgreSQL
- **Bot**: aiogram 3.x
- **Parser**: python-docx
- **Scheduler**: APScheduler
- **Frontend**: Bootstrap 5 + Vanilla JS
- **Deploy**: Docker + Docker Compose

## 🏗️ Архитектура системы

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Ученики   │────────▶│ Telegram Bot │────────▶│  PostgreSQL │
│  (Telegram) │         │   (aiogram)  │         │   Database  │
└─────────────┘         └──────────────┘         └─────────────┘
                              │                          ▲
                              │                          │
                              ▼                          │
                        ┌──────────────┐                 │
                        │  Scheduler   │                 │
                        │ (APScheduler)│─────────────────┘
                        └──────────────┘
                              │
                              │  Напоминания
                              ▼
┌──────────────┐        ┌──────────────┐
│Администратор │───────▶│   FastAPI    │
│ (Web Browser)│        │   Backend    │
└──────────────┘        └──────────────┘
                              │
                              ▼
                        ┌──────────────┐
                        │  File Parser │
                        │ (python-docx)│
                        └──────────────┘
```

## 📁 Структура проекта

```
olympus_bot/
├── bot/                      # Telegram бот
│   ├── handlers/             # Обработчики команд
│   │   ├── registration.py   # Регистрация учеников
│   │   ├── olympiad.py       # Получение кодов
│   │   └── screenshots.py    # Прием скриншотов
│   ├── keyboards.py          # Клавиатуры
│   └── main.py               # Запуск бота
├── api/                      # FastAPI backend
│   ├── routers/              # API эндпоинты
│   │   ├── upload.py         # Загрузка файлов
│   │   ├── monitoring.py     # Мониторинг
│   │   └── admin.py          # Управление
│   └── main.py               # FastAPI приложение
├── parser/                   # Парсер .docx файлов
│   └── docx_parser.py
├── database/                 # База данных
│   ├── models.py             # SQLAlchemy модели
│   ├── crud.py               # CRUD операции
│   └── database.py           # Подключение к БД
├── admin_panel/              # Веб-интерфейс
│   ├── templates/            # HTML шаблоны
│   └── static/               # Статические файлы
├── tasks/                    # Фоновые задачи
│   └── reminders.py          # Система напоминаний
├── utils/                    # Утилиты
│   └── auth.py               # Генерация кодов
├── uploads/                  # Загруженные файлы
├── screenshots/              # Скриншоты учеников
├── logs/                     # Логи
├── .env                      # Конфигурация
├── requirements.txt          # Зависимости
├── main.py                   # Главный файл запуска
└── docker-compose.yml        # Docker конфигурация
```

## 🚀 Быстрый старт

### Вариант 1: Docker (Рекомендуется)

1. **Клонируйте репозиторий**:
```bash
git clone <your-repo-url>
cd olympus_bot
```

2. **Создайте файл .env**:
```bash
cp .env.example .env
```

3. **Отредактируйте .env файл**:
```env
# Получите токен у @BotFather в Telegram
BOT_TOKEN=your_bot_token_here

# Ваш Telegram ID (получите у @userinfobot)
ADMIN_TELEGRAM_ID=your_telegram_id

# БД (используются в docker-compose)
DATABASE_URL=postgresql+asyncpg://olympus_user:olympus_password@db:5432/olympus_bot
DATABASE_URL_SYNC=postgresql://olympus_user:olympus_password@db:5432/olympus_bot

# Секретный ключ (сгенерируйте командой: openssl rand -hex 32)
SECRET_KEY=your_secret_key_here

# Часовой пояс
TIMEZONE=Europe/Moscow
```

4. **Запустите через Docker Compose**:
```bash
docker-compose up -d
```

5. **Проверьте статус**:
```bash
docker-compose ps
```

6. **Инициализируйте базу данных**:
```bash
docker-compose exec bot python main.py init
```

✅ Готово! Бот работает, админ-панель доступна по адресу: http://localhost:8000

### Вариант 2: Локальная установка

1. **Установите PostgreSQL** (если еще не установлен)

2. **Создайте виртуальное окружение**:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows
```

3. **Установите зависимости**:
```bash
pip install -r requirements.txt
```

4. **Настройте .env файл** (см. выше)

5. **Создайте базу данных в PostgreSQL**:
```sql
CREATE DATABASE olympus_bot;
```

6. **Инициализируйте БД**:
```bash
python main.py init
```

7. **Запустите систему**:

Запуск бота и API одновременно:
```bash
python main.py all
```

Или по отдельности:
```bash
# Только бот
python main.py bot

# Только API
python main.py api
```

## 📖 Инструкция по использованию

### Для администратора

#### 1. Подготовка учеников

1. Откройте админ-панель: http://localhost:8000
2. Нажмите "Добавить ученика"
3. Введите ФИО ученика
4. Скопируйте сгенерированный регистрационный код
5. Передайте код ученику

**Массовое добавление через API**:
```bash
curl -X POST http://localhost:8000/admin/students/bulk \
  -H "Content-Type: application/json" \
  -d '{
    "students": [
      "Иванов Иван Иванович",
      "Петров Петр Петрович"
    ]
  }'
```

#### 2. Загрузка файла олимпиады

1. Подготовьте .docx файл с такой структурой:

```
Физика за 8 класс

№  | ФИО                        | Код
1  | Иванов Иван Иванович       | sbph58/sch771584/8/abc123
2  | Петров Петр Петрович       | sbph58/sch771584/8/def456

Физика за 9 класс
sbph59/sch771584/9/xyz789
sbph59/sch771584/9/qwe321
```

2. В админ-панели нажмите "Выберите .docx файл"
3. Загрузите файл
4. Система автоматически:
   - Создаст новую сессию олимпиады
   - Распределит именные коды для 8 класса
   - Добавит коды в пул для 9 класса
   - Деактивирует предыдущие сессии

#### 3. Мониторинг

В админ-панели отображается:
- 📊 Общая статистика
- 👥 Список всех учеников с их статусами
- ✅ Кто получил код и прислал скриншот
- ❌ Кто не прислал скриншот

### Для ученика

#### 1. Регистрация

1. Найдите бота в Telegram (имя вашего бота)
2. Нажмите `/start`
3. Введите регистрационный код, полученный от преподавателя
4. Готово! Теперь вы зарегистрированы

#### 2. Получение кода олимпиады

1. Отправьте команду `/get_code`
2. Выберите класс (8 или 9)
3. Получите свой код доступа
4. Используйте код для входа на олимпиаду

#### 3. Отправка скриншота

1. После завершения работы сделайте скриншот последней страницы
2. Отправьте фото в бота (просто как обычное фото)
3. Бот подтвердит получение

⚠️ **Важно**: Бот будет напоминать вам каждые 30 минут до 21:30, если вы не пришлете скриншот!

## 🔧 Настройка

### Переменные окружения (.env)

```env
# Telegram Bot
BOT_TOKEN=              # Токен бота от @BotFather
ADMIN_TELEGRAM_ID=      # Telegram ID администратора

# Database
DATABASE_URL=           # Асинхронное подключение к PostgreSQL
DATABASE_URL_SYNC=      # Синхронное подключение (для миграций)

# API Settings
API_HOST=0.0.0.0
API_PORT=8000
SECRET_KEY=             # Секретный ключ (32+ символов)

# Paths
UPLOAD_FOLDER=uploads
SCREENSHOTS_FOLDER=screenshots

# Reminders
REMINDER_INTERVAL_MINUTES=30    # Интервал напоминаний
REMINDER_END_TIME=21:30         # Время окончания напоминаний
TIMEZONE=Europe/Moscow          # Часовой пояс

# Registration
REGISTRATION_CODE_LENGTH=12     # Длина регистрационных кодов

# Logging
LOG_LEVEL=INFO
```

## 📊 API Документация

После запуска API доступна автоматическая документация:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Основные эндпоинты:

#### Загрузка файла
```http
POST /upload/olympiad-file
Content-Type: multipart/form-data

file: <.docx file>
```

#### Статистика
```http
GET /monitoring/statistics
```

#### Список учеников с статусами
```http
GET /monitoring/students-status
```

#### Создание ученика
```http
POST /admin/students
Content-Type: application/json

{
  "full_name": "Иванов Иван Иванович"
}
```

#### Экспорт в CSV
```http
GET /admin/export/students
```

## 🔍 Troubleshooting

### Бот не отвечает

1. Проверьте токен в .env
2. Проверьте логи: `docker-compose logs bot` или `logs/bot.log`
3. Убедитесь, что БД запущена: `docker-compose ps`

### Не загружается файл

1. Проверьте формат файла (.docx)
2. Убедитесь, что структура соответствует ожидаемой
3. Проверьте, что все ученики из файла есть в БД

### Не приходят напоминания

1. Проверьте настройки времени в .env
2. Убедитесь, что планировщик запущен (смотрите логи)
3. Проверьте часовой пояс

### База данных не подключается

1. Проверьте DATABASE_URL в .env
2. Убедитесь, что PostgreSQL запущен
3. Проверьте права доступа к БД

## 🛡️ Безопасность

- ✅ Регистрационные коды одноразовые
- ✅ Один Telegram аккаунт = один ученик
- ✅ Коды для 9 класса нельзя переиспользовать
- ✅ Все скриншоты сохраняются с привязкой к ученику
- ✅ История всех запросов в БД

## 📝 Лицензия

MIT License - см. файл [LICENSE](LICENSE)

## 🤝 Вклад в проект

Если вы нашли баг или хотите предложить улучшение, создайте Issue или Pull Request!

## 📧 Контакты

При возникновении вопросов свяжитесь с разработчиком.

---

**Создано с ❤️ для автоматизации олимпиад**
