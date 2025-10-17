# Архитектура системы авторизации через Telegram бота

## Обзор

Система авторизации для доступа к веб-панели через Telegram бота без традиционных логинов/паролей.

##  1. Концепция

### 1.1 Принцип работы

```
1. Пользователь → Открывает веб-панель
2. Панель → Показывает QR-код или ссылку
3. Пользователь → Переходит по ссылке в Telegram
4. Бот → Генерирует одноразовый токен
5. Панель → Проверяет токен и авторизует пользователя
6. Пользователь → Получает доступ к панели
```

### 1.2 Преимущества

- ✅ Не нужно помнить пароли
- ✅ Telegram уже авторизован
- ✅ Безопасная двухфакторная аутентификация
- ✅ Простота использования
- ✅ Автоматический контроль доступа

## 2. База данных

### 2.1 Таблица `users`

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(100),
    full_name VARCHAR(200),
    role VARCHAR(50) DEFAULT 'viewer',  -- admin, teacher, viewer
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);
```

### 2.2 Таблица `auth_tokens`

```sql
CREATE TABLE auth_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    token VARCHAR(64) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    is_used BOOLEAN DEFAULT FALSE,
    used_at TIMESTAMP,
    ip_address VARCHAR(45),
    user_agent TEXT
);
```

### 2.3 Таблица `sessions`

```sql
CREATE TABLE sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    session_token VARCHAR(64) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    ip_address VARCHAR(45),
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 3. Роли и права доступа

### 3.1 Роли

```python
class UserRole(Enum):
    ADMIN = "admin"      # Полный доступ
    TEACHER = "teacher"  # Управление олимпиадами и учениками
    VIEWER = "viewer"    # Только просмотр статистики
```

### 3.2 Матрица доступа

| Действие | Admin | Teacher | Viewer |
|----------|-------|---------|--------|
| Просмотр дашборда | ✅ | ✅ | ✅ |
| Просмотр учеников | ✅ | ✅ | ✅ |
| Добавление учеников | ✅ | ✅ | ❌ |
| Загрузка кодов | ✅ | ✅ | ❌ |
| Активация олимпиад | ✅ | ✅ | ❌ |
| Экспорт данных | ✅ | ✅ | ✅ |
| Управление пользователями | ✅ | ❌ | ❌ |
| Просмотр логов | ✅ | ✅ | ❌ |
| Настройка системы | ✅ | ❌ | ❌ |

## 4. Процесс авторизации

### 4.1 Шаг 1: Генерация ссылки

```python
# api/routers/auth.py

@router.get("/auth/login-link")
async def generate_login_link():
    """Генерирует одноразовую ссылку для авторизации"""
    auth_code = secrets.token_urlsafe(16)

    # Сохраняем в Redis (TTL 5 минут)
    await redis.setex(
        f"auth:pending:{auth_code}",
        300,  # 5 минут
        json.dumps({"created_at": time.time()})
    )

    return {
        "auth_code": auth_code,
        "bot_link": f"https://t.me/{BOT_USERNAME}?start=auth_{auth_code}",
        "qr_code_data": f"https://t.me/{BOT_USERNAME}?start=auth_{auth_code}",
        "expires_in": 300
    }
```

### 4.2 Шаг 2: Обработка в боте

```python
# bot/handlers/auth.py

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext, command: CommandObject):
    """Обработка /start с параметром auth"""

    if command.args and command.args.startswith("auth_"):
        auth_code = command.args[5:]  # Убираем префикс "auth_"

        # Проверяем код в Redis
        pending = await redis.get(f"auth:pending:{auth_code}")

        if not pending:
            await message.answer("❌ Код авторизации истёк или недействителен")
            return

        # Проверяем, есть ли пользователь в системе
        user = await get_user_by_telegram_id(message.from_user.id)

        if not user:
            await message.answer(
                "❌ У вас нет доступа к панели управления.\n"
                "Обратитесь к администратору."
            )
            return

        # Генерируем токен сессии
        session_token = secrets.token_urlsafe(32)

        # Сохраняем в БД
        session = await create_session(user.id, session_token)

        # Сохраняем токен в Redis для быстрого доступа
        await redis.setex(
            f"auth:success:{auth_code}",
            60,  # 1 минута
            session_token
        )

        await message.answer(
            f"✅ Авторизация успешна!\n\n"
            f"Роль: {user.role}\n"
            f"Вернитесь в браузер - авторизация завершается автоматически."
        )
```

### 4.3 Шаг 3: Проверка авторизации

```python
# api/routers/auth.py

@router.post("/auth/check")
async def check_auth(auth_code: str):
    """Проверяет, завершена ли авторизация"""

    # Проверяем в Redis
    session_token = await redis.get(f"auth:success:{auth_code}")

    if not session_token:
        return {"status": "pending"}

    # Получаем информацию о сессии
    session = await get_session_by_token(session_token)
    user = await get_user_by_id(session.user_id)

    # Удаляем одноразовые коды
    await redis.delete(f"auth:pending:{auth_code}")
    await redis.delete(f"auth:success:{auth_code}")

    return {
        "status": "success",
        "session_token": session_token,
        "user": {
            "id": user.id,
            "name": user.full_name,
            "role": user.role
        }
    }
```

## 5. Frontend: Страница авторизации

### 5.1 HTML

```html
<!-- admin_panel/templates/login.html -->
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Вход - Olympus Bot</title>
    <link rel="icon" type="image/svg+xml" href="/static/favicon.svg">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js"></script>
</head>
<body class="bg-light">
    <div class="container">
        <div class="row justify-content-center align-items-center min-vh-100">
            <div class="col-md-6 col-lg-4">
                <div class="card shadow">
                    <div class="card-body text-center p-5">
                        <h2 class="mb-4">
                            <i class="bi bi-trophy-fill text-warning"></i>
                            Olympus Bot
                        </h2>
                        <p class="text-muted mb-4">
                            Для входа отсканируйте QR-код или перейдите по ссылке в Telegram
                        </p>

                        <div id="qrcode" class="mb-4"></div>

                        <a id="telegram-link" href="#" class="btn btn-primary btn-lg w-100 mb-3">
                            <i class="bi bi-telegram"></i> Открыть в Telegram
                        </a>

                        <div id="status" class="alert alert-info">
                            ⏳ Ожидание авторизации...
                        </div>

                        <small class="text-muted">
                            Код действителен 5 минут
                        </small>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="/static/login.js"></script>
</body>
</html>
```

### 5.2 JavaScript

```javascript
// admin_panel/static/login.js

async function initLogin() {
    // 1. Получаем ссылку для авторизации
    const response = await fetch('/api/auth/login-link');
    const data = await response.json();

    // 2. Показываем QR-код
    new QRCode(document.getElementById('qrcode'), {
        text: data.bot_link,
        width: 256,
        height: 256
    });

    // 3. Устанавливаем ссылку
    document.getElementById('telegram-link').href = data.bot_link;

    // 4. Начинаем проверку каждые 2 секунды
    const checkInterval = setInterval(async () => {
        const checkResponse = await fetch('/api/auth/check', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({auth_code: data.auth_code})
        });

        const checkData = await checkResponse.json();

        if (checkData.status === 'success') {
            clearInterval(checkInterval);

            // Сохраняем токен в cookie
            document.cookie = `session_token=${checkData.session_token}; path=/; max-age=2592000`; // 30 дней

            // Показываем успех
            document.getElementById('status').innerHTML = '✅ Авторизация успешна! Перенаправление...';
            document.getElementById('status').className = 'alert alert-success';

            // Перенаправляем на главную
            setTimeout(() => {
                window.location.href = '/';
            }, 1000);
        }
    }, 2000);

    // 5. Автоматическое обновление через 5 минут
    setTimeout(() => {
        clearInterval(checkInterval);
        location.reload();
    }, 300000);
}

// Запуск при загрузке страницы
document.addEventListener('DOMContentLoaded', initLogin);
```

## 6. Middleware для защиты

```python
# api/middleware/auth.py

from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse

class AuthMiddleware:
    async def __call__(self, request: Request, call_next):
        # Публичные пути
        public_paths = ['/api/auth/', '/static/', '/favicon.svg']

        if any(request.url.path.startswith(path) for path in public_paths):
            return await call_next(request)

        # Проверяем токен
        session_token = request.cookies.get('session_token')

        if not session_token:
            if request.url.path.startswith('/api/'):
                raise HTTPException(status_code=401, detail="Не авторизован")
            return RedirectResponse('/login')

        # Проверяем сессию
        session = await get_session_by_token(session_token)

        if not session or not session.is_active:
            if request.url.path.startswith('/api/'):
                raise HTTPException(status_code=401, detail="Сессия истекла")
            return RedirectResponse('/login')

        # Обновляем время последней активности
        await update_session_activity(session.id)

        # Добавляем пользователя в request
        request.state.user = await get_user_by_id(session.user_id)

        return await call_next(request)
```

## 7. Управление пользователями

### 7.1 Команды бота для администратора

```python
@router.message(Command("admin"))
async def cmd_admin(message: Message):
    """Админ-команды"""

    # Проверка прав
    if message.from_user.id != ADMIN_TELEGRAM_ID:
        return

    await message.answer(
        "🔧 <b>Управление доступом</b>\n\n"
        "/grant_access @username admin - Дать полный доступ\n"
        "/grant_access @username teacher - Дать доступ учителю\n"
        "/grant_access @username viewer - Дать доступ для просмотра\n"
        "/revoke_access @username - Отозвать доступ\n"
        "/list_users - Список пользователей",
        parse_mode="HTML"
    )

@router.message(Command("grant_access"))
async def cmd_grant_access(message: Message, command: CommandObject):
    """Выдать доступ пользователю"""

    if message.from_user.id != ADMIN_TELEGRAM_ID:
        return

    # Парсинг: /grant_access @username role
    args = command.args.split()

    if len(args) < 2:
        await message.answer("Использование: /grant_access @username роль")
        return

    username = args[0].lstrip('@')
    role = args[1]

    # Создаем или обновляем пользователя
    user = await create_or_update_user(username, role)

    await message.answer(f"✅ Доступ выдан: @{username} → {role}")
```

### 7.2 Веб-интерфейс для управления

```python
# api/routers/admin_users.py

@router.get("/api/admin/users")
async def get_users(current_user: User = Depends(get_current_user)):
    """Список пользователей (только для админа)"""

    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Доступ запрещён")

    users = await get_all_users()
    return users

@router.put("/api/admin/users/{user_id}")
async def update_user(
    user_id: int,
    role: str,
    is_active: bool,
    current_user: User = Depends(get_current_user)
):
    """Обновить пользователя"""

    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Доступ запрещён")

    user = await update_user_access(user_id, role, is_active)
    return user
```

## 8. Безопасность

### 8.1 Защита от атак

```python
# Ограничение попыток
RATE_LIMIT = {
    "login_attempts": 5,  # Попыток в минуту
    "session_duration": 30 * 24 * 60 * 60,  # 30 дней
    "inactivity_timeout": 24 * 60 * 60  # 24 часа
}

# Проверка IP
async def check_ip_whitelist(ip: str) -> bool:
    """Опциональная проверка IP"""
    if not IP_WHITELIST_ENABLED:
        return True
    return ip in ALLOWED_IPS

# CSRF защита
async def verify_csrf_token(request: Request):
    """Проверка CSRF токена"""
    token = request.headers.get('X-CSRF-Token')
    if not token or not await verify_token(token):
        raise HTTPException(status_code=403, detail="CSRF validation failed")
```

### 8.2 Логирование

```python
# database/models.py

class AuditLog(Base):
    """Лог действий пользователей"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String(100))  # "login", "logout", "create_session", etc
    details = Column(JSON)
    ip_address = Column(String(45))
    timestamp = Column(DateTime, default=datetime.utcnow)
```

## 9. План реализации

### Фаза 1: Базовая авторизация (3-4 часа)
- [ ] Создать таблицы users, auth_tokens, sessions
- [ ] Реализовать генерацию ссылок
- [ ] Добавить обработку в боте
- [ ] Создать страницу логина с QR-кодом
- [ ] Реализовать проверку авторизации

### Фаза 2: Middleware и защита (2-3 часа)
- [ ] Добавить AuthMiddleware
- [ ] Реализовать проверку сессий
- [ ] Добавить logout функционал
- [ ] Настроить редирект для неавторизованных

### Фаза 3: Управление пользователями (2-3 часа)
- [ ] Команды бота для администратора
- [ ] Веб-интерфейс управления пользователями
- [ ] Роли и права доступа
- [ ] Аудит логи

### Фаза 4: Безопасность (1-2 часа)
- [ ] Rate limiting
- [ ] CSRF защита
- [ ] Валидация токенов
- [ ] Мониторинг подозрительной активности

### Фаза 5: Тестирование (1-2 часа)
- [ ] Тестирование авторизации
- [ ] Проверка прав доступа
- [ ] Нагрузочное тестирование
- [ ] Тест безопасности

## 10. Альтернативные варианты

### Вариант A: Telegram Login Widget (проще, но менее гибко)

```html
<script async src="https://telegram.org/js/telegram-widget.js?22"
    data-telegram-login="your_bot_name"
    data-size="large"
    data-auth-url="https://yoursite.com/auth/telegram"
    data-request-access="write"></script>
```

### Вариант B: OAuth через Telegram (сложнее, но стандартизировано)

Использовать официальный OAuth flow Telegram.

## Заключение

**Рекомендуемый подход**: Собственная реализация с QR-кодом

**Преимущества:**
- ✅ Полный контроль над процессом
- ✅ Красивый UX с QR-кодом
- ✅ Гибкая система ролей
- ✅ Безопасность
- ✅ Простота использования

**Время реализации**: 10-15 часов

**Приоритет**: Высокий (необходимо для защиты админ-панели)
