#!/bin/bash

# Скрипт быстрого старта Olympus Bot
# Использование: ./scripts/quick_start.sh

set -e

echo "========================================="
echo "🏆 Olympus Bot - Быстрый старт"
echo "========================================="
echo ""

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Проверка наличия .env файла
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  Файл .env не найден!${NC}"
    echo "Создаем из .env.example..."
    
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${GREEN}✅ Файл .env создан${NC}"
        echo ""
        echo -e "${YELLOW}⚠️  ВАЖНО: Отредактируйте .env файл и укажите:${NC}"
        echo "  - BOT_TOKEN (получите у @BotFather)"
        echo "  - ADMIN_TELEGRAM_ID (ваш Telegram ID)"
        echo ""
        read -p "Нажмите Enter после редактирования .env..."
    else
        echo -e "${RED}❌ Файл .env.example не найден!${NC}"
        exit 1
    fi
fi

echo ""
echo "Выберите способ запуска:"
echo "1) Docker (рекомендуется)"
echo "2) Локально (требуется PostgreSQL)"
echo ""
read -p "Ваш выбор (1 или 2): " choice

if [ "$choice" = "1" ]; then
    echo ""
    echo "🐳 Запуск через Docker..."
    
    # Проверка наличия Docker
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker не установлен!${NC}"
        echo "Установите Docker: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}❌ Docker Compose не установлен!${NC}"
        echo "Установите Docker Compose: https://docs.docker.com/compose/install/"
        exit 1
    fi
    
    echo "📦 Сборка контейнеров..."
    docker-compose build
    
    echo "🚀 Запуск контейнеров..."
    docker-compose up -d
    
    echo "⏳ Ожидание запуска базы данных..."
    sleep 5
    
    echo "🗄️  Инициализация базы данных..."
    docker-compose exec -T bot python main.py init
    
    echo ""
    echo -e "${GREEN}✅ Система запущена!${NC}"
    echo ""
    echo "📊 Админ-панель: http://localhost:8000"
    echo "🤖 Бот работает в фоновом режиме"
    echo ""
    echo "Полезные команды:"
    echo "  docker-compose logs -f bot    # Логи бота"
    echo "  docker-compose logs -f api    # Логи API"
    echo "  docker-compose ps             # Статус контейнеров"
    echo "  docker-compose down           # Остановить все"
    
elif [ "$choice" = "2" ]; then
    echo ""
    echo "💻 Локальная установка..."
    
    # Проверка Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python 3 не установлен!${NC}"
        exit 1
    fi
    
    # Проверка PostgreSQL
    if ! command -v psql &> /dev/null; then
        echo -e "${YELLOW}⚠️  PostgreSQL не найден${NC}"
        echo "Убедитесь, что PostgreSQL установлен и запущен"
    fi
    
    echo "📦 Создание виртуального окружения..."
    python3 -m venv venv
    
    echo "📦 Активация виртуального окружения..."
    source venv/bin/activate || . venv/Scripts/activate
    
    echo "📦 Установка зависимостей..."
    pip install -r requirements.txt
    
    echo "🗄️  Создание базы данных..."
    echo "Введите параметры подключения к PostgreSQL:"
    read -p "Хост (по умолчанию localhost): " db_host
    db_host=${db_host:-localhost}
    read -p "Порт (по умолчанию 5432): " db_port
    db_port=${db_port:-5432}
    read -p "Пользователь: " db_user
    read -sp "Пароль: " db_password
    echo ""
    
    # Обновляем .env безопасно, не раскрывая пароль в командной строке
    export db_user db_password db_host db_port
    tmp_env=$(mktemp)
    awk -v db_user="$db_user" -v db_password="$db_password" -v db_host="$db_host" -v db_port="$db_port" '
    BEGIN {
        url_async="DATABASE_URL=postgresql+asyncpg://" db_user ":" db_password "@" db_host ":" db_port "/olympus_bot"
        url_sync="DATABASE_URL_SYNC=postgresql://" db_user ":" db_password "@" db_host ":" db_port "/olympus_bot"
    }
    /^DATABASE_URL=/{print url_async; next}
    /^DATABASE_URL_SYNC=/{print url_sync; next}
    {print}
    ' .env > "$tmp_env" && mv "$tmp_env" .env
    unset db_password
    
    echo "🗄️  Инициализация базы данных..."
    python main.py init
    
    echo ""
    echo -e "${GREEN}✅ Установка завершена!${NC}"
    echo ""
    echo "Для запуска используйте:"
    echo "  source venv/bin/activate  # Активация окружения"
    echo "  python main.py all        # Запуск бота и API"
    echo ""
    echo "Или отдельно:"
    echo "  python main.py bot        # Только бот"
    echo "  python main.py api        # Только API"
    
else
    echo -e "${RED}❌ Неверный выбор${NC}"
    exit 1
fi

echo ""
echo "========================================="
echo "🎉 Готово к использованию!"
echo "========================================="
echo ""
echo "Следующие шаги:"
echo "1. Добавьте учеников:"
echo "   python scripts/add_students_from_file.py students_example.txt"
echo ""
echo "2. Откройте админ-панель: http://localhost:8000"
echo ""
echo "3. Загрузите файл с кодами олимпиады"
echo ""
echo "4. Раздайте ученикам регистрационные коды"
echo ""
echo "📖 Подробная документация: README_FULL.md"
