FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Копирование requirements
COPY requirements.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода приложения
COPY . .

# Создание необходимых директорий
RUN mkdir -p uploads screenshots logs

# Переменные окружения по умолчанию
ENV PYTHONUNBUFFERED=1

# Expose порты
EXPOSE 8000

# Команда запуска (будет переопределена в docker-compose)
CMD ["python", "main.py"]
