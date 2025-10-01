# 🏆 Olympus Bot

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)](https://fastapi.tiangolo.com/)
[![aiogram](https://img.shields.io/badge/aiogram-3.3-blue.svg)](https://docs.aiogram.dev/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Полнофункциональная система управления олимпиадами** через Telegram-бота с веб-панелью администратора.

---

## ✨ Возможности

### Для учеников 👨‍🎓
- 🔐 Регистрация по одноразовому коду
- 📝 Получение персональных кодов для олимпиад (8 или 9 класс)
- 📸 Отправка скриншотов выполненных работ
- ⏰ Автоматические напоминания о необходимости отправки скриншота
- 📊 Проверка своего статуса

### Для администратора 👨‍💼
- 📤 Загрузка .docx файлов с кодами олимпиад
- 👥 Управление учениками
- 🔑 Генерация регистрационных кодов
- 📊 Мониторинг в реальном времени
- 🖼️ Просмотр скриншотов учеников
- 📥 Экспорт данных в CSV/Excel
- 📈 Детальная статистика

---

## 🚀 Быстрый старт

### Автоматическая установка

```bash
# Клонируйте репозиторий
git clone <your-repo-url>
cd olympus_bot

# Запустите скрипт установки
chmod +x scripts/quick_start.sh
./scripts/quick_start.sh
```

### Docker (рекомендуется)

```bash
# 1. Настройте .env файл
cp .env.example .env
nano .env  # Добавьте BOT_TOKEN

# 2. Запустите систему
docker-compose up -d

# 3. Инициализируйте базу данных
docker-compose exec bot python main.py init

# ✅ Готово! Админ-панель: http://localhost:8000
```

### Локальная установка

```bash
# 1. Создайте виртуальное окружение
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows

# 2. Установите зависимости
pip install -r requirements.txt

# 3. Настройте .env и базу данных
cp .env.example .env
# Отредактируйте .env

# 4. Инициализируйте БД
python main.py init

# 5. Запустите
python main.py all
```

---

## 📖 Документация

- 📘 **[Быстрый старт](QUICKSTART.md)** - Установка за 5 минут
- 📗 **[Полная документация](README_FULL.md)** - Подробное руководство
- 📙 **[Развертывание](DEPLOYMENT.md)** - Продакшн-инструкция
- 📕 **[API документация](http://localhost:8000/docs)** - После запуска

---

## 🎯 Основные команды

```bash
# Запуск
python main.py all          # Бот + API
python main.py bot          # Только бот
python main.py api          # Только API

# Docker
make docker-up              # Запустить
make docker-down            # Остановить
make docker-logs            # Логи

# Управление
python scripts/add_students_from_file.py students.txt  # Добавить учеников
python scripts/generate_report.py --format excel       # Создать отчет
python scripts/system_check.py                         # Проверить систему

# База данных
python main.py init         # Инициализировать
alembic upgrade head        # Применить миграции
```

---

## 📁 Структура проекта

```
olympus_bot/
├── 🤖 bot/                 # Telegram бот
│   ├── handlers/           # Обработчики команд
│   ├── keyboards.py        # Клавиатуры
│   ├── middlewares.py      # Middleware
│   └── main.py             # Запуск бота
│
├── 🌐 api/                 # FastAPI backend
│   ├── routers/            # API эндпоинты
│   └── main.py             # API сервер
│
├── 🗄️ database/            # База данных
│   ├── models.py           # Модели SQLAlchemy
│   ├── crud.py             # CRUD операции
│   └── database.py         # Подключение
│
├── 📄 parser/              # Парсер .docx
├── ⏰ tasks/               # Фоновые задачи
├── 🛠️ utils/               # Утилиты
├── 💻 admin_panel/         # Веб-интерфейс
│
├── 📜 scripts/             # Полезные скрипты
│   ├── quick_start.sh      # Быстрый старт
│   ├── add_students_from_file.py
│   ├── generate_report.py
│   └── system_check.py
│
├── 📦 uploads/             # Загруженные файлы
├── 📸 screenshots/         # Скриншоты учеников
├── 📝 logs/                # Логи
│
├── .env                    # Конфигурация
├── docker-compose.yml      # Docker
├── requirements.txt        # Зависимости
└── main.py                 # Главный запуск
```

---

## 🔧 Технологии

- **Backend**: Python 3.11+ / FastAPI / SQLAlchemy
- **Database**: PostgreSQL 15
- **Bot Framework**: aiogram 3.x
- **Document Parser**: python-docx
- **Task Scheduler**: APScheduler
- **Frontend**: Bootstrap 5 + Vanilla JS
- **Deploy**: Docker + Docker Compose

---

## 📊 Скриншоты

### Админ-панель
![Dashboard](https://via.placeholder.com/800x400?text=Admin+Dashboard)

### Telegram бот
![Bot](https://via.placeholder.com/400x600?text=Telegram+Bot)

---

## 🎓 Использование

### 1. Добавьте учеников

```bash
# Создайте файл students.txt с ФИО
python scripts/add_students_from_file.py students.txt
```

### 2. Загрузите файл олимпиады

Откройте http://localhost:8000 и загрузите .docx файл с форматом:

```
Физика за 8 класс

№ | ФИО                      | Код
1 | Иванов Иван Иванович     | code123
2 | Петров Петр Петрович     | code456

Физика за 9 класс
code789
code012
```

### 3. Раздайте коды регистрации

После добавления учеников система создаст файл `registration_codes_*.txt` с кодами.

### 4. Ученики регистрируются

1. Находят бота в Telegram
2. Отправляют `/start`
3. Вводят код регистрации
4. Готово!

---

## 🛡️ Безопасность

- ✅ Одноразовые регистрационные коды
- ✅ Привязка код → ученик
- ✅ Полная история действий
- ✅ Безопасное хранение данных
- ✅ Защита от спама (rate limiting)

---

## 🔍 Проверка системы

Перед запуском проверьте готовность:

```bash
python scripts/system_check.py
```

Скрипт проверит:
- ✅ Настройку .env
- ✅ Подключение к БД
- ✅ Telegram токен
- ✅ Зависимости Python
- ✅ Структуру директорий

---

## 📈 Мониторинг

```bash
# Логи
docker-compose logs -f bot  # Логи бота
docker-compose logs -f api  # Логи API
tail -f logs/bot.log        # Файловые логи

# Статус
docker-compose ps           # Статус контейнеров
docker stats                # Использование ресурсов

# Отчеты
python scripts/generate_report.py --format console  # В консоль
python scripts/generate_report.py --format excel    # Excel файл
```

---

## 🆘 Помощь

### Проблемы с запуском?

1. Проверьте систему: `python scripts/system_check.py`
2. Смотрите логи: `docker-compose logs` или `logs/bot.log`
3. Читайте [TROUBLESHOOTING](README_FULL.md#troubleshooting)

### Нашли баг?

Создайте [Issue](../../issues) с описанием проблемы.

### Хотите помочь?

Отправьте [Pull Request](../../pulls)!

---

## 📝 Лицензия

MIT License - см. [LICENSE](LICENSE)

---

## 🤝 Контакты

- 📧 Email: your@email.com
- 💬 Telegram: @your_username
- 🌐 Website: https://your-site.com

---

## ⭐ Благодарности

Спасибо всем, кто использует и улучшает этот проект!

---

<div align="center">

**Создано с ❤️ для автоматизации олимпиад**

[Документация](README_FULL.md) • [Быстрый старт](QUICKSTART.md) • [Развертывание](DEPLOYMENT.md)

</div>
