# 🚀 Руководство по развертыванию

Полная инструкция по развертыванию Olympus Bot на продакшн сервере.

## 📋 Требования

### Минимальные

- **CPU**: 1 ядро
- **RAM**: 1 GB
- **Диск**: 10 GB
- **ОС**: Ubuntu 20.04+ / Debian 11+ / CentOS 8+
- **Docker**: 20.10+
- **Docker Compose**: 2.0+

### Рекомендуемые

- **CPU**: 2 ядра
- **RAM**: 2 GB
- **Диск**: 20 GB SSD
- **Интернет**: Стабильное соединение

## 🌐 Развертывание на VPS

### 1. Подключение к серверу

```bash
ssh user@your-server-ip
```

### 2. Установка Docker

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Добавление пользователя в группу docker
sudo usermod -aG docker $USER

# Установка Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Перезагрузка сессии
exit
# Подключитесь снова
ssh user@your-server-ip
```

### 3. Клонирование проекта

```bash
# Установка git если нужно
sudo apt install git -y

# Клонирование
git clone <your-repo-url> olympus_bot
cd olympus_bot
```

### 4. Настройка окружения

```bash
# Создание .env файла
cp .env.example .env

# Редактирование конфигурации
nano .env
```

**Важные параметры для продакшна:**

```env
# Telegram
BOT_TOKEN=your_production_bot_token
ADMIN_TELEGRAM_ID=your_telegram_id

# Database (используйте безопасные пароли!)
DATABASE_URL=postgresql+asyncpg://olympus_user:STRONG_PASSWORD_HERE@db:5432/olympus_bot
DATABASE_URL_SYNC=postgresql://olympus_user:STRONG_PASSWORD_HERE@db:5432/olympus_bot

# Security
SECRET_KEY=YOUR_VERY_LONG_SECRET_KEY_HERE_32_CHARS_MINIMUM

# Timezone
TIMEZONE=Europe/Moscow
```

### 5. Настройка Docker Compose для продакшна

Создайте `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    container_name: olympus_db_prod
    environment:
      POSTGRES_USER: olympus_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}  # Из .env
      POSTGRES_DB: olympus_bot
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: always
    networks:
      - olympus_network

  bot:
    build: .
    container_name: olympus_bot_prod
    command: python bot/main.py
    env_file:
      - .env
    volumes:
      - ./screenshots:/app/screenshots
      - ./uploads:/app/uploads
      - ./logs:/app/logs
    depends_on:
      - db
    restart: always
    networks:
      - olympus_network

  api:
    build: .
    container_name: olympus_api_prod
    command: uvicorn api.main:app --host 0.0.0.0 --port 8000
    env_file:
      - .env
    volumes:
      - ./screenshots:/app/screenshots
      - ./uploads:/app/uploads
      - ./logs:/app/logs
    depends_on:
      - db
    restart: always
    networks:
      - olympus_network

  nginx:
    image: nginx:alpine
    container_name: olympus_nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./screenshots:/usr/share/nginx/html/screenshots
      - /etc/letsencrypt:/etc/letsencrypt  # SSL сертификаты
    depends_on:
      - api
    restart: always
    networks:
      - olympus_network

volumes:
  postgres_data:

networks:
  olympus_network:
    driver: bridge
```

### 6. Конфигурация Nginx

Создайте `nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    upstream api {
        server api:8000;
    }

    server {
        listen 80;
        server_name your-domain.com;

        # Для Let's Encrypt
        location /.well-known/acme-challenge/ {
            root /var/www/certbot;
        }

        # Редирект на HTTPS
        location / {
            return 301 https://$server_name$request_uri;
        }
    }

    server {
        listen 443 ssl http2;
        server_name your-domain.com;

        # SSL сертификаты (после настройки Let's Encrypt)
        ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

        # Проксирование на API
        location / {
            proxy_pass http://api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Статические файлы (скриншоты)
        location /screenshots {
            alias /usr/share/nginx/html/screenshots;
            autoindex off;
        }

        # Лимиты
        client_max_body_size 50M;
    }
}
```

### 7. Настройка SSL с Let's Encrypt

```bash
# Установка Certbot
sudo apt install certbot python3-certbot-nginx -y

# Получение сертификата
sudo certbot --nginx -d your-domain.com

# Автообновление сертификатов
sudo certbot renew --dry-run
```

### 8. Запуск системы

```bash
# Сборка образов
docker-compose -f docker-compose.prod.yml build

# Запуск контейнеров
docker-compose -f docker-compose.prod.yml up -d

# Инициализация базы данных
docker-compose -f docker-compose.prod.yml exec bot python main.py init

# Проверка статуса
docker-compose -f docker-compose.prod.yml ps
```

### 9. Добавление учеников

```bash
# Загрузите файл со списком учеников на сервер
scp students.txt user@your-server-ip:~/olympus_bot/

# На сервере
cd olympus_bot
docker-compose -f docker-compose.prod.yml exec bot python scripts/add_students_from_file.py students.txt
```

## 🔒 Безопасность

### Firewall

```bash
# UFW
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### Регулярные бэкапы

Создайте скрипт бэкапа `backup.sh`:

```bash
#!/bin/bash

BACKUP_DIR="/backup/olympus_bot"
DATE=$(date +%Y%m%d_%H%M%S)

# Создание директории
mkdir -p $BACKUP_DIR

# Бэкап базы данных
docker-compose -f docker-compose.prod.yml exec -T db pg_dump -U olympus_user olympus_bot > $BACKUP_DIR/db_$DATE.sql

# Бэкап файлов
tar -czf $BACKUP_DIR/files_$DATE.tar.gz uploads/ screenshots/

# Удаление старых бэкапов (старше 30 дней)
find $BACKUP_DIR -type f -mtime +30 -delete

echo "✅ Бэкап завершен: $DATE"
```

Добавьте в cron:
```bash
crontab -e

# Бэкап каждый день в 3:00
0 3 * * * /path/to/backup.sh
```

## 📊 Мониторинг

### Просмотр логов

```bash
# Все логи
docker-compose -f docker-compose.prod.yml logs -f

# Только бот
docker-compose -f docker-compose.prod.yml logs -f bot

# Только API
docker-compose -f docker-compose.prod.yml logs -f api

# Логи из файлов
tail -f logs/bot.log
```

### Мониторинг ресурсов

```bash
# Использование ресурсов контейнерами
docker stats

# Размер volumes
docker system df
```

## 🔄 Обновление системы

```bash
cd olympus_bot

# Остановка контейнеров
docker-compose -f docker-compose.prod.yml down

# Получение обновлений
git pull origin main

# Пересборка и запуск
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# Применение миграций (если есть)
docker-compose -f docker-compose.prod.yml exec bot alembic upgrade head
```

## 🆘 Устранение неполадок

### Контейнеры не запускаются

```bash
# Проверка логов
docker-compose -f docker-compose.prod.yml logs

# Проверка сети
docker network ls
docker network inspect olympus_network
```

### База данных недоступна

```bash
# Проверка статуса
docker-compose -f docker-compose.prod.yml exec db pg_isready -U olympus_user

# Пересоздание контейнера БД
docker-compose -f docker-compose.prod.yml restart db
```

### Бот не отвечает

```bash
# Проверка процесса
docker-compose -f docker-compose.prod.yml exec bot ps aux

# Перезапуск бота
docker-compose -f docker-compose.prod.yml restart bot
```

## 📈 Масштабирование

### Для большого количества пользователей

1. **Используйте отдельный сервер для БД**
2. **Добавьте Redis для кэширования**
3. **Настройте балансировщик нагрузки**
4. **Используйте CDN для статических файлов**

### Redis для сессий бота

Добавьте в `docker-compose.prod.yml`:

```yaml
  redis:
    image: redis:alpine
    container_name: olympus_redis
    restart: always
    networks:
      - olympus_network
```

## 🎯 Чеклист перед запуском

- [ ] Сервер настроен и обновлен
- [ ] Docker и Docker Compose установлены
- [ ] Файл .env настроен с безопасными паролями
- [ ] SSL сертификат получен
- [ ] Firewall настроен
- [ ] Бэкапы настроены
- [ ] Бот протестирован
- [ ] Ученики добавлены в систему
- [ ] Регистрационные коды розданы
- [ ] Мониторинг настроен

---

**Готово! Ваша система готова к продакшну! 🎉**
