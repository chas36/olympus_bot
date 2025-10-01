import requests
import json

def read_students(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]

def add_students(students):
    url = "http://localhost:8000/admin/students/bulk"
    headers = {"Content-Type": "application/json"}
    data = {"students": students}
    
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            print("✅ Ученики успешно добавлены")
            return True
        else:
            print(f"❌ Ошибка: {response.status_code}")
            print(response.text)
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

if __name__ == "__main__":
    students = read_students("students_example.txt")
    print(f"📚 Найдено {len(students)} учеников")
    add_students(students)