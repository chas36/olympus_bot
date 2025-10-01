#!/usr/bin/env python3
"""
Скрипт для организации файлов проекта Olympus Bot
Перемещает скачанные файлы из корня в правильные директории

Использование:
    python organize_files.py
"""

import os
import shutil
from pathlib import Path

# Карта соответствий: имя скачанного файла -> путь назначения
FILE_MAPPING = {
    # Конфигурация и документация
    "requirements_txt.py": "requirements.txt",
    "env_example.sh": ".env.example",
    "readme_full.md": "README_FULL.md",
    "main_readme.md": "README.md",
    "quickstart_guide.md": "QUICKSTART.md",
    "deployment_guide.md": "DEPLOYMENT.md",
    "students_example.txt": "students_example.txt",
    "makefile.txt": "Makefile",
    
    # Docker
    "dockerfile.txt": "Dockerfile",
    "docker_compose.txt": "docker-compose.yml",
    
    # Главный файл
    "main_py.py": "main.py",
    
    # Database
    "database_models.py": "database/models.py",
    "database_connection.py": "database/database.py",
    "crud_operations.py": "database/crud.py",
    
    # Parser
    "docx_parser.py": "parser/docx_parser.py",
    
    # Utils
    "auth_utils.py": "utils/auth.py",
    "admin_notifications.py": "utils/notifications.py",
    
    # Bot
    "bot_main.py": "bot/main.py",
    "bot_keyboards.py": "bot/keyboards.py",
    "bot_middlewares.py": "bot/middlewares.py",
    "bot_registration.py": "bot/handlers/registration.py",
    "bot_olympiad.py": "bot/handlers/olympiad.py",
    "bot_screenshots.py": "bot/handlers/screenshots.py",
    
    # Tasks
    "reminder_system.py": "tasks/reminders.py",
    
    # API
    "api_main.py": "api/main.py",
    "api_upload.py": "api/routers/upload.py",
    "api_monitoring.py": "api/routers/monitoring.py",
    "api_admin.py": "api/routers/admin.py",
    
    # Admin Panel
    "admin_dashboard_html.html": "admin_panel/templates/dashboard.html",
    
    # Scripts
    "script_add_students.py": "scripts/add_students_from_file.py",
    "generate_report_script.py": "scripts/generate_report.py",
    "system_check.py": "scripts/system_check.py",
    "quick_start_script.sh": "scripts/quick_start.sh",
    
    # Alembic
    "alembic_ini.txt": "alembic.ini",
    "alembic_env.py": "alembic/env.py",
    "alembic_script_template.py": "alembic/script.py.mako",
    
    # Tests
    "test_parser.py": "tests/test_parser.py",
    
    # Docs
    "api_examples.md": "docs/API_EXAMPLES.md",
    "faq_document.md": "docs/FAQ.md",
}

# Файлы которые нужно удалить (служебные)
FILES_TO_REMOVE = [
    "project_builder.py",
    "full_installer.py",
    "install_olympus_bot.py",
]

def create_directory_structure():
    """Создает необходимые директории"""
    directories = [
        "bot/handlers",
        "api/routers",
        "database",
        "parser",
        "tasks",
        "utils",
        "admin_panel/templates",
        "admin_panel/static",
        "scripts",
        "tests",
        "docs",
        "alembic/versions",
        "uploads",
        "screenshots",
        "logs",
    ]
    
    print("📁 Создание структуры директорий...")
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"  ✅ {directory}/")
    
    # Создаем __init__.py файлы
    init_files = [
        "bot/__init__.py",
        "bot/handlers/__init__.py",
        "api/__init__.py",
        "api/routers/__init__.py",
        "database/__init__.py",
        "parser/__init__.py",
        "tasks/__init__.py",
        "utils/__init__.py",
    ]
    
    for init_file in init_files:
        Path(init_file).touch()
    
    # Создаем .gitkeep файлы
    gitkeep_files = [
        "uploads/.gitkeep",
        "screenshots/.gitkeep",
        "logs/.gitkeep",
        "alembic/versions/.gitkeep",
    ]
    
    for gitkeep in gitkeep_files:
        Path(gitkeep).touch()


def organize_files():
    """Перемещает файлы в правильные директории"""
    print("\n📦 Организация файлов...")
    
    moved = 0
    not_found = []
    errors = []
    
    for source_file, destination in FILE_MAPPING.items():
        if not os.path.exists(source_file):
            not_found.append(source_file)
            continue
        
        try:
            # Создаем директорию назначения если нужно
            dest_dir = os.path.dirname(destination)
            if dest_dir:
                os.makedirs(dest_dir, exist_ok=True)
            
            # Перемещаем файл
            shutil.move(source_file, destination)
            print(f"  ✅ {source_file} → {destination}")
            moved += 1
            
        except Exception as e:
            errors.append((source_file, str(e)))
            print(f"  ❌ {source_file}: {e}")
    
    return moved, not_found, errors


def remove_service_files():
    """Удаляет служебные файлы"""
    print("\n🗑️  Удаление служебных файлов...")
    
    for filename in FILES_TO_REMOVE:
        if os.path.exists(filename):
            os.remove(filename)
            print(f"  ✅ Удален: {filename}")


def create_gitignore():
    """Создает .gitignore если его нет"""
    if not os.path.exists(".gitignore"):
        gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
venv/
env/
.venv/

# Environment
.env

# Database
*.db
*.sqlite

# Logs
logs/
*.log

# Uploads
uploads/*
screenshots/*
!uploads/.gitkeep
!screenshots/.gitkeep

# IDE
.idea/
.vscode/
*.swp

# OS
.DS_Store
Thumbs.db

# Alembic
alembic/versions/*.py
!alembic/versions/.gitkeep
"""
        with open(".gitignore", "w") as f:
            f.write(gitignore_content)
        print("\n✅ Создан .gitignore")


def main():
    print("""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║         🏆 OLYMPUS BOT - ОРГАНИЗАЦИЯ ФАЙЛОВ              ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
""")
    
    # Проверяем, что мы в правильной директории
    if not os.path.exists("requirements_txt.py") and not os.path.exists("bot_main.py"):
        print("❌ Ошибка: Запустите скрипт в директории со скачанными файлами!")
        print("   (Должны быть файлы типа bot_main.py, api_main.py и т.д.)")
        return
    
    # Создаем структуру
    create_directory_structure()
    
    # Организуем файлы
    moved, not_found, errors = organize_files()
    
    # Удаляем служебные файлы
    remove_service_files()
    
    # Создаем .gitignore
    create_gitignore()
    
    # Итоговая статистика
    print(f"""
╔═══════════════════════════════════════════════════════════╗
║                      📊 СТАТИСТИКА                        ║
╚═══════════════════════════════════════════════════════════╝

✅ Файлов перемещено: {moved}
⚠️  Файлов не найдено: {len(not_found)}
❌ Ошибок: {len(errors)}
""")
    
    if not_found:
        print("⚠️  Не найдены следующие файлы:")
        for f in not_found:
            print(f"   - {f}")
        print("\n   (Это нормально, если вы не скачали все файлы)")
    
    if errors:
        print("\n❌ Ошибки при перемещении:")
        for f, e in errors:
            print(f"   - {f}: {e}")
    
    print(f"""
╔═══════════════════════════════════════════════════════════╗
║                    ✅ ГОТОВО!                             ║
╚═══════════════════════════════════════════════════════════╝

📂 Структура проекта создана!

📋 СЛЕДУЮЩИЕ ШАГИ:

1. Настройте окружение:
   cp .env.example .env
   nano .env  # Добавьте BOT_TOKEN и другие параметры

2. Проверьте систему:
   python scripts/system_check.py

3. Запустите проект:
   
   🐳 Через Docker (рекомендуется):
   docker-compose up -d
   docker-compose exec bot python main.py init
   
   💻 Или локально:
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\\Scripts\\activate    # Windows
   pip install -r requirements.txt
   python main.py init
   python main.py all

4. Откройте админ-панель:
   http://localhost:8000

📖 Документация:
   - README.md - Обзор проекта
   - QUICKSTART.md - Быстрый старт
   - README_FULL.md - Полная документация
   - docs/FAQ.md - Часто задаваемые вопросы

💡 Если что-то не работает:
   python scripts/system_check.py

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Удачи! 🚀
""")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Прервано пользователем")
    except Exception as e:
        print(f"\n\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
