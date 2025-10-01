.PHONY: help install init migrate bot api all docker-up docker-down docker-logs clean test

help:
	@echo "Olympus Bot - Команды управления"
	@echo ""
	@echo "Установка и инициализация:"
	@echo "  make install      - Установить зависимости"
	@echo "  make init         - Инициализировать базу данных"
	@echo "  make migrate      - Применить миграции"
	@echo ""
	@echo "Запуск (локально):"
	@echo "  make bot          - Запустить только бота"
	@echo "  make api          - Запустить только API"
	@echo "  make all          - Запустить бота и API"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-up    - Запустить через Docker Compose"
	@echo "  make docker-down  - Остановить Docker контейнеры"
	@echo "  make docker-logs  - Посмотреть логи"
	@echo "  make docker-init  - Инициализировать БД в Docker"
	@echo ""
	@echo "Утилиты:"
	@echo "  make clean        - Очистить кэш и временные файлы"
	@echo "  make add-students - Добавить учеников из файла"
	@echo ""

install:
	pip install -r requirements.txt

init:
	python main.py init

migrate:
	alembic upgrade head

bot:
	python main.py bot

api:
	python main.py api

all:
	python main.py all

# Docker команды
docker-up:
	docker-compose up -d
	@echo "✅ Контейнеры запущены"
	@echo "🤖 Бот: docker-compose logs -f bot"
	@echo "🌐 API: http://localhost:8000"

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

docker-init:
	docker-compose exec bot python main.py init

docker-restart:
	docker-compose restart

docker-rebuild:
	docker-compose down
	docker-compose build
	docker-compose up -d

# Утилиты
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.log" -delete
	@echo "✅ Кэш очищен"

add-students:
	@echo "Использование: python scripts/add_students_from_file.py <файл.txt>"
	@echo "Пример: python scripts/add_students_from_file.py students.txt"

# Разработка
dev-bot:
	python -m bot.main

dev-api:
	uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# База данных
db-create-migration:
	@read -p "Введите название миграции: " name; \
	alembic revision --autogenerate -m "$$name"

db-reset:
	@echo "⚠️  ВНИМАНИЕ: Это удалит ВСЕ данные!"
	@read -p "Продолжить? (yes/no): " confirm; \
	if [ "$$confirm" = "yes" ]; then \
		python main.py init; \
		echo "✅ База данных пересоздана"; \
	else \
		echo "❌ Отменено"; \
	fi

# Экспорт данных
export-students:
	@echo "Экспорт доступен через API: http://localhost:8000/admin/export/students"

# Тестирование (для будущего расширения)
test:
	pytest tests/ -v

# Проверка кода
lint:
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

format:
	black .
	isort .
