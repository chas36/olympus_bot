#!/bin/bash
# Скрипт для настройки базы данных Olympus Bot

echo "🔧 Настройка базы данных Olympus Bot..."

# Выполняем SQL команды от имени пользователя postgres
sudo -u postgres psql << 'EOF'
-- Создание пользователя (если не существует)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_user WHERE usename = 'olympus_user') THEN
        CREATE USER olympus_user WITH PASSWORD 'olympus_password';
        RAISE NOTICE 'Пользователь olympus_user создан';
    ELSE
        RAISE NOTICE 'Пользователь olympus_user уже существует';
    END IF;
END $$;

-- Создание базы данных (если не существует)
SELECT 'CREATE DATABASE olympus_bot OWNER olympus_user'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'olympus_bot')\gexec

-- Выдача прав
GRANT ALL PRIVILEGES ON DATABASE olympus_bot TO olympus_user;

-- Подключение к базе данных
\c olympus_bot

-- Выдача прав на схему
GRANT ALL ON SCHEMA public TO olympus_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO olympus_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO olympus_user;

-- Выдача прав на будущие объекты
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO olympus_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO olympus_user;

\q
EOF

if [ $? -eq 0 ]; then
    echo "✅ База данных настроена успешно!"
    echo ""
    echo "Теперь вы можете запустить проект:"
    echo "  make migrate  # Применить миграции"
    echo "  make bot      # Запустить бота"
else
    echo "❌ Ошибка при настройке базы данных"
    exit 1
fi
