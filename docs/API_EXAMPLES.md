# 📡 Примеры использования API

Примеры работы с API Olympus Bot через curl, Python и JavaScript.

## 🌐 Base URL

```
http://localhost:8000
```

Для продакшна замените на ваш домен.

---

## 📤 Загрузка файла олимпиады

### cURL

```bash
curl -X POST "http://localhost:8000/upload/olympiad-file" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@olimpiada_fizika.docx"
```

### Python

```python
import requests

url = "http://localhost:8000/upload/olympiad-file"
files = {"file": open("olimpiada_fizika.docx", "rb")}

response = requests.post(url, files=files)
data = response.json()

print(f"Успех: {data['success']}")
print(f"Предмет: {data['subject']}")
print(f"Кодов 8 класса: {data['grade8_codes_created']}")
print(f"Кодов 9 класса: {data['grade9_codes_created']}")
```

### JavaScript

```javascript
const formData = new FormData();
const fileInput = document.querySelector('input[type="file"]');
formData.append('file', fileInput.files[0]);

fetch('http://localhost:8000/upload/olympiad-file', {
  method: 'POST',
  body: formData
})
.then(response => response.json())
.then(data => {
  console.log('Успех:', data.success);
  console.log('Предмет:', data.subject);
});
```

---

## 📊 Получение статистики

### cURL

```bash
curl -X GET "http://localhost:8000/monitoring/statistics"
```

### Python

```python
import requests

response = requests.get("http://localhost:8000/monitoring/statistics")
stats = response.json()

print(f"Активная олимпиада: {stats['active_session']['subject']}")
print(f"Всего учеников: {stats['students']['total']}")
print(f"Запросили код: {stats['codes']['total_requested']}")
print(f"Прислали скриншот: {stats['screenshots']['submitted']}")
```

### Response Example

```json
{
  "active_session": {
    "id": 1,
    "subject": "Физика",
    "date": "2025-10-01T14:30:00",
    "uploaded_file_name": "20251001_143000_fizika.docx"
  },
  "students": {
    "total": 26,
    "registered": 24,
    "unregistered": 2
  },
  "codes": {
    "total_requested": 18,
    "grade8_requested": 12,
    "grade9_requested": 6,
    "grade9_available": 10
  },
  "screenshots": {
    "submitted": 10,
    "missing": 8,
    "percentage": 55.6
  }
}
```

---

## 👥 Статус учеников

### cURL

```bash
curl -X GET "http://localhost:8000/monitoring/students-status"
```

### Python

```python
import requests
import pandas as pd

response = requests.get("http://localhost:8000/monitoring/students-status")
students = response.json()

# Конвертируем в DataFrame для удобства
df = pd.DataFrame(students)

# Фильтруем учеников без скриншотов
missing_screenshots = df[
    (df['code_requested'] == True) & 
    (df['screenshot_submitted'] == False)
]

print(f"Учеников без скриншотов: {len(missing_screenshots)}")
for _, student in missing_screenshots.iterrows():
    print(f"- {student['full_name']} (класс {student['grade']})")
```

---

## 👤 Создание ученика

### cURL

```bash
curl -X POST "http://localhost:8000/admin/students" \
  -H "Content-Type: application/json" \
  -d '{"full_name": "Иванов Иван Иванович"}'
```

### Python

```python
import requests

url = "http://localhost:8000/admin/students"
data = {"full_name": "Иванов Иван Иванович"}

response = requests.post(url, json=data)
student = response.json()

print(f"Ученик создан: {student['full_name']}")
print(f"Код регистрации: {student['registration_code']}")
```

---

## 👥 Массовое создание учеников

### Python

```python
import requests

# Список учеников из файла
with open('students.txt', 'r', encoding='utf-8') as f:
    students = [line.strip() for line in f if line.strip()]

url = "http://localhost:8000/admin/students/bulk"
data = {"students": students}

response = requests.post(url, json=data)
result = response.json()

print(f"Создано учеников: {result['count']}")

# Сохраняем коды в файл
with open('registration_codes.txt', 'w', encoding='utf-8') as f:
    f.write("ФИО | Код\n")
    f.write("-" * 70 + "\n")
    for student in result['students']:
        f.write(f"{student['full_name']} | {student['registration_code']}\n")

print("Коды сохранены в registration_codes.txt")
```

---

## 📥 Экспорт в CSV

### cURL

```bash
curl -X GET "http://localhost:8000/admin/export/students" \
  -o students_export.csv
```

### Python

```python
import requests

url = "http://localhost:8000/admin/export/students"
response = requests.get(url)

with open('students_export.csv', 'wb') as f:
    f.write(response.content)

print("Экспорт завершен: students_export.csv")
```

---

## 🔍 Список учеников без скриншотов

### Python

```python
import requests

url = "http://localhost:8000/monitoring/missing-screenshots"
response = requests.get(url)
missing = response.json()

if not missing:
    print("✅ Все ученики прислали скриншоты!")
else:
    print(f"❌ Учеников без скриншотов: {len(missing)}\n")
    for student in missing:
        print(f"- {student['full_name']}")
        print(f"  Класс: {student['grade']}")
        print(f"  Код: {student['code']}")
        print(f"  Запрошено: {student['requested_at']}")
        print()
```

---

## 📋 Получение списка всех сессий

### cURL

```bash
curl -X GET "http://localhost:8000/upload/sessions"
```

### Python

```python
import requests

response = requests.get("http://localhost:8000/upload/sessions")
sessions = response.json()

print(f"Всего сессий: {len(sessions)}\n")
for session in sessions:
    status = "✅ Активна" if session['is_active'] else "❌ Неактивна"
    print(f"{session['subject']} - {session['date']}")
    print(f"  Статус: {status}")
    print(f"  Файл: {session['uploaded_file_name']}")
    print()
```

---

## 🔄 Активация конкретной сессии

### cURL

```bash
curl -X POST "http://localhost:8000/upload/sessions/1/activate"
```

### Python

```python
import requests

session_id = 1
url = f"http://localhost:8000/upload/sessions/{session_id}/activate"

response = requests.post(url)
result = response.json()

if result['success']:
    print(f"✅ Сессия {session_id} активирована")
else:
    print("❌ Ошибка активации")
```

---

## 🔑 Генерация регистрационных кодов

### Python

```python
import requests

# Генерируем 10 кодов
url = "http://localhost:8000/admin/generate-codes?count=10"
response = requests.get(url)
result = response.json()

print(f"Сгенерировано кодов: {result['count']}\n")
for i, code in enumerate(result['codes'], 1):
    print(f"{i}. {code}")

# Сохраняем в файл
with open('new_codes.txt', 'w') as f:
    for code in result['codes']:
        f.write(f"{code}\n")
```

---

## 📊 Получение детальной статистики с фильтрами

### Python

```python
import requests
from datetime import datetime

# Получаем полную информацию
response = requests.get("http://localhost:8000/monitoring/students-status")
students = response.json()

# Статистика по классам
grade8 = [s for s in students if s.get('grade') == 8]
grade9 = [s for s in students if s.get('grade') == 9]

print("📊 Статистика по классам:")
print(f"  8 класс: {len(grade8)} учеников")
print(f"  9 класс: {len(grade9)} учеников")

# Топ учеников (быстрее всех прислали)
with_screenshots = [
    s for s in students 
    if s['screenshot_submitted'] and s['screenshot_submitted_at']
]
with_screenshots.sort(
    key=lambda x: datetime.fromisoformat(x['screenshot_submitted_at'])
)

print("\n🏆 Топ-5 самых быстрых:")
for i, student in enumerate(with_screenshots[:5], 1):
    print(f"{i}. {student['full_name']}")
    print(f"   Скриншот: {student['screenshot_submitted_at']}")
```

---

## 🔄 Автоматическая синхронизация

### Python скрипт для мониторинга

```python
import requests
import time
from datetime import datetime

def check_status():
    """Проверяет статус и выводит уведомления"""
    response = requests.get("http://localhost:8000/monitoring/statistics")
    stats = response.json()
    
    if not stats.get('active_session'):
        print("⚠️  Нет активной олимпиады")
        return
    
    missing = stats['screenshots']['missing']
    
    if missing > 0:
        print(f"⚠️  {missing} учеников не прислали скриншот!")
        
        # Получаем список
        response = requests.get("http://localhost:8000/monitoring/missing-screenshots")
        students = response.json()
        
        for student in students:
            print(f"  - {student['full_name']}")
    else:
        print("✅ Все скриншоты получены!")

# Проверка каждые 5 минут
while True:
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Проверка статуса...")
    check_status()
    time.sleep(300)  # 5 минут
```

---

## 🌐 WebSocket для real-time обновлений (будущее расширение)

```javascript
// Пример интеграции WebSocket (требует расширения API)
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  switch(data.type) {
    case 'new_request':
      console.log(`Новый запрос от ${data.student_name}`);
      break;
    case 'screenshot_received':
      console.log(`Скриншот получен от ${data.student_name}`);
      break;
  }
};
```

---

## 📖 Дополнительная информация

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

---

## 🛡️ Аутентификация (для будущего расширения)

Сейчас API открыт для локального использования. Для продакшна рекомендуется добавить:

```python
# Пример с Bearer токеном
headers = {
    "Authorization": f"Bearer {API_TOKEN}"
}

response = requests.get(url, headers=headers)
```

---

**💡 Совет**: Используйте библиотеку `httpx` для асинхронных запросов или `requests` для синхронных.
