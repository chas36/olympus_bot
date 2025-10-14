// dashboard.js - JavaScript для админ-панели v2

// Обновление времени
function updateTime() {
    const now = new Date();
    document.getElementById('currentTime').textContent = now.toLocaleTimeString('ru-RU');
}
setInterval(updateTime, 1000);
updateTime();

// Загрузка при старте
document.addEventListener('DOMContentLoaded', function() {
    loadDashboard();
    loadStudentsStats();
    loadCodesStats();
    loadSessions();
    loadRecentActivity();
    
    // Автообновление каждые 30 секунд
    setInterval(() => {
        loadDashboard();
        loadRecentActivity();
    }, 30000);
});

// ==================== ДАШБОРД ====================

async function loadDashboard() {
    try {
        const response = await fetch('/api/monitoring/dashboard');
        const data = await response.json();
        
        // Карточки статистики
        const statsHTML = `
            <div class="col-md-3">
                <div class="card stat-card primary">
                    <div class="card-body">
                        <h6 class="text-muted mb-2"><i class="bi bi-people"></i> Всего учеников</h6>
                        <h2 class="mb-0">${data.students.total}</h2>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card stat-card success">
                    <div class="card-body">
                        <h6 class="text-muted mb-2"><i class="bi bi-check-circle"></i> Зарегистрировано</h6>
                        <h2 class="mb-0">${data.students.registered}</h2>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card stat-card warning">
                    <div class="card-body">
                        <h6 class="text-muted mb-2"><i class="bi bi-exclamation-circle"></i> Не зарегистрировано</h6>
                        <h2 class="mb-0">${data.students.not_registered}</h2>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card stat-card info">
                    <div class="card-body">
                        <h6 class="text-muted mb-2"><i class="bi bi-calendar-event"></i> Всего сессий</h6>
                        <h2 class="mb-0">${data.total_sessions}</h2>
                    </div>
                </div>
            </div>
        `;
        document.getElementById('statsCards').innerHTML = statsHTML;
        
        // Активная сессия
        if (data.active_session) {
            const session = data.active_session;
            const progress = session.total_codes > 0 
                ? Math.round((session.issued_codes / session.total_codes) * 100)
                : 0;
            
            const activeHTML = `
                <h4>${session.subject}</h4>
                <p class="text-muted">${new Date(session.date).toLocaleDateString('ru-RU')}</p>
                <hr>
                <div class="row text-center mb-3">
                    <div class="col-4">
                        <h3>${session.total_codes}</h3>
                        <small class="text-muted">Всего кодов</small>
                    </div>
                    <div class="col-4">
                        <h3>${session.issued_codes}</h3>
                        <small class="text-muted">Выдано</small>
                    </div>
                    <div class="col-4">
                        <h3>${session.screenshots}</h3>
                        <small class="text-muted">Скриншотов</small>
                    </div>
                </div>
                <div class="progress" style="height: 25px;">
                    <div class="progress-bar bg-success" style="width: ${progress}%">
                        ${progress}%
                    </div>
                </div>
            `;
            document.getElementById('activeSessionCard').innerHTML = activeHTML;
        } else {
            document.getElementById('activeSessionCard').innerHTML = `
                <div class="alert alert-warning mb-0">
                    <i class="bi bi-exclamation-triangle"></i> Нет активной сессии
                </div>
            `;
        }
    } catch (error) {
        console.error('Ошибка загрузки дашборда:', error);
    }
}

async function loadRecentActivity() {
    try {
        const response = await fetch('/api/monitoring/recent-activity?limit=10');
        const data = await response.json();
        
        if (data.activity.length === 0) {
            document.getElementById('recentActivity').innerHTML = `
                <p class="text-muted mb-0">Пока нет активности</p>
            `;
            return;
        }
        
        const activityHTML = data.activity.map(item => {
            const icon = item.screenshot ? 'bi-camera-fill text-success' : 'bi-key text-primary';
            const time = new Date(item.timestamp).toLocaleTimeString('ru-RU');
            
            return `
                <div class="activity-item">
                    <i class="bi ${icon}"></i>
                    <strong>${item.student}</strong> 
                    <small class="text-muted">- ${item.subject}</small>
                    <br>
                    <small class="text-muted">${time}</small>
                    ${item.screenshot ? '<span class="badge bg-success ms-2">Скриншот</span>' : ''}
                </div>
            `;
        }).join('');
        
        document.getElementById('recentActivity').innerHTML = activityHTML;
    } catch (error) {
        console.error('Ошибка загрузки активности:', error);
    }
}

// ==================== УЧЕНИКИ ====================

async function loadStudentsStats() {
    try {
        const response = await fetch('/api/students/stats');
        const data = await response.json();

        // Строим статистику по классам
        let byClassHTML = '';
        if (data.by_class && Object.keys(data.by_class).length > 0) {
            byClassHTML = '<hr><h6>По классам:</h6><div class="row">';
            Object.entries(data.by_class).forEach(([classNum, count]) => {
                byClassHTML += `
                    <div class="col-6 mb-2">
                        <small class="text-muted">${classNum} класс:</small>
                        <strong>${count}</strong>
                    </div>
                `;
            });
            byClassHTML += '</div>';
        }

        const statsHTML = `
            <div class="row text-center">
                <div class="col-4">
                    <h2>${data.total}</h2>
                    <small class="text-muted">Всего</small>
                </div>
                <div class="col-4">
                    <h2 class="text-success">${data.registered}</h2>
                    <small class="text-muted">Зарегистрировано</small>
                </div>
                <div class="col-4">
                    <h2 class="text-warning">${data.not_registered}</h2>
                    <small class="text-muted">Ожидают</small>
                </div>
            </div>
            ${byClassHTML}
            <hr>
            <button class="btn btn-primary w-100" onclick="loadStudentsList()">
                <i class="bi bi-list"></i> Показать список
            </button>
        `;

        document.getElementById('studentsStats').innerHTML = statsHTML;
    } catch (error) {
        console.error('Ошибка загрузки статистики учеников:', error);
    }
}

async function loadStudentsList() {
    try {
        const response = await fetch('/api/students/');
        const students = await response.json();
        
        const tbody = document.querySelector('#studentsTable tbody');
        
        if (students.length === 0) {
            tbody.innerHTML = `
                <tr><td colspan="5" class="text-center text-muted">Нет учеников</td></tr>
            `;
            return;
        }
        
        const rows = students.map(s => `
            <tr>
                <td>${s.id}</td>
                <td>
                    ${s.full_name}
                    ${s.class_display ? `<br><small class="text-muted">${s.class_display}</small>` : ''}
                </td>
                <td><code>${s.registration_code}</code></td>
                <td>
                    ${s.is_registered
                        ? '<span class="badge bg-success">Зарегистрирован</span>'
                        : '<span class="badge bg-warning">Ожидает</span>'}
                </td>
                <td>${s.telegram_id || '-'}</td>
            </tr>
        `).join('');
        
        tbody.innerHTML = rows;
    } catch (error) {
        console.error('Ошибка загрузки списка учеников:', error);
    }
}

async function uploadStudents() {
    const fileInput = document.getElementById('studentsFileInput');
    const file = fileInput.files[0];
    
    if (!file) {
        alert('Выберите файл');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    const resultDiv = document.getElementById('uploadStudentsResult');
    resultDiv.innerHTML = '<div class="alert alert-info"><i class="bi bi-hourglass-split"></i> Загрузка...</div>';
    
    try {
        const response = await fetch('/api/students/upload-excel', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            resultDiv.innerHTML = `
                <div class="alert alert-success">
                    <h6><i class="bi bi-check-circle"></i> Успешно загружено!</h6>
                    <p class="mb-0">Создано: <strong>${result.created}</strong></p>
                    <p class="mb-0">Пропущено: <strong>${result.skipped}</strong></p>
                </div>
            `;
            
            fileInput.value = '';
            loadStudentsStats();
            loadDashboard();
        } else {
            resultDiv.innerHTML = `
                <div class="alert alert-danger">
                    <i class="bi bi-x-circle"></i> Ошибка: ${result.detail || 'Неизвестная ошибка'}
                </div>
            `;
        }
    } catch (error) {
        resultDiv.innerHTML = `
            <div class="alert alert-danger">
                <i class="bi bi-x-circle"></i> Ошибка: ${error.message}
            </div>
        `;
    }
}

// ==================== КОДЫ ====================

async function loadCodesStats() {
    try {
        const response = await fetch('/api/codes/stats');
        const data = await response.json();
        
        const statsHTML = `
            <h6 class="mb-3">8 класс:</h6>
            <div class="mb-3">
                <div class="d-flex justify-content-between mb-1">
                    <span>Всего:</span>
                    <strong>${data.grade8.total}</strong>
                </div>
                <div class="d-flex justify-content-between mb-1">
                    <span>Распределено:</span>
                    <strong class="text-success">${data.grade8.assigned}</strong>
                </div>
                <div class="d-flex justify-content-between mb-1">
                    <span>Не распределено:</span>
                    <strong class="text-warning">${data.grade8.unassigned}</strong>
                </div>
                <div class="d-flex justify-content-between">
                    <span>Выдано:</span>
                    <strong class="text-info">${data.grade8.issued}</strong>
                </div>
            </div>
            
            <h6 class="mb-3">9 класс (резерв):</h6>
            <div>
                <div class="d-flex justify-content-between mb-1">
                    <span>Всего:</span>
                    <strong>${data.grade9.total}</strong>
                </div>
                <div class="d-flex justify-content-between mb-1">
                    <span>Использовано:</span>
                    <strong class="text-danger">${data.grade9.used}</strong>
                </div>
                <div class="d-flex justify-content-between">
                    <span>Доступно:</span>
                    <strong class="text-success">${data.grade9.available}</strong>
                </div>
            </div>
        `;
        
        document.getElementById('codesStats').innerHTML = statsHTML;
    } catch (error) {
        console.error('Ошибка загрузки статистики кодов:', error);
    }
}

async function uploadCodes() {
    const fileInput = document.getElementById('codesFileInput');
    const files = fileInput.files;
    
    if (files.length === 0) {
        alert('Выберите файлы');
        return;
    }
    
    const autoReserve = document.getElementById('autoReserveCheck').checked;
    const formData = new FormData();
    
    for (let file of files) {
        formData.append('files', file);
    }
    
    const resultDiv = document.getElementById('uploadCodesResult');
    resultDiv.innerHTML = '<div class="alert alert-info"><i class="bi bi-hourglass-split"></i> Загрузка и обработка...</div>';
    
    try {
        const response = await fetch(`/api/codes/upload-csv?auto_reserve=${autoReserve}`, {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            let html = `
                <div class="alert alert-success">
                    <h6><i class="bi bi-check-circle"></i> Успешно загружено!</h6>
                    <p class="mb-2">Загружено файлов: <strong>${result.uploaded.length}</strong></p>
            `;
            
            if (result.reservation) {
                html += `
                    <hr>
                    <h6><i class="bi bi-arrow-repeat"></i> Резервирование:</h6>
                    <p class="mb-0">${result.reservation.message}</p>
                `;
            }
            
            html += '</div>';
            resultDiv.innerHTML = html;
            
            fileInput.value = '';
            loadCodesStats();
            loadSessions();
            loadDashboard();
        } else {
            resultDiv.innerHTML = `
                <div class="alert alert-danger">
                    <i class="bi bi-x-circle"></i> Ошибка загрузки
                </div>
            `;
        }
    } catch (error) {
        resultDiv.innerHTML = `
            <div class="alert alert-danger">
                <i class="bi bi-x-circle"></i> Ошибка: ${error.message}
            </div>
        `;
    }
}

async function manualReserve() {
    if (!confirm('Зарезервировать коды 9 класса для 8 класса?')) {
        return;
    }
    
    try {
        const response = await fetch('/api/codes/reserve', {
            method: 'POST'
        });
        
        const result = await response.json();
        
        alert(result.message);
        loadCodesStats();
    } catch (error) {
        alert('Ошибка резервирования: ' + error.message);
    }
}

async function loadSessions() {
    try {
        const response = await fetch('/api/codes/sessions');
        const sessions = await response.json();
        
        if (sessions.length === 0) {
            document.getElementById('sessionsTable').innerHTML = `
                <p class="text-muted">Нет сессий</p>
            `;
            return;
        }
        
        const tableHTML = `
            <div class="table-responsive">
                <table class="table table-hover">
                    <thead class="table-light">
                        <tr>
                            <th>ID</th>
                            <th>Предмет</th>
                            <th>Дата</th>
                            <th>Статус</th>
                            <th>Действия</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${sessions.map(s => {
                            const date = new Date(s.date);
                            const dateStr = isNaN(date.getTime()) ? 'Дата не указана' : date.toLocaleDateString('ru-RU');
                            return `
                            <tr>
                                <td>${s.id}</td>
                                <td><strong>${s.subject}</strong></td>
                                <td>${dateStr}</td>
                                <td>
                                    ${s.is_active
                                        ? '<span class="badge bg-success">Активна</span>'
                                        : '<span class="badge bg-secondary">Неактивна</span>'}
                                </td>
                                <td>
                                    ${!s.is_active
                                        ? `<button class="btn btn-sm btn-primary" onclick="activateSession(${s.id})">
                                            <i class="bi bi-play"></i> Активировать
                                           </button>`
                                        : '<button class="btn btn-sm btn-secondary" disabled>Активна</button>'}
                                    <a href="/api/codes/export/session/${s.id}" class="btn btn-sm btn-info">
                                        <i class="bi bi-download"></i> Экспорт
                                    </a>
                                </td>
                            </tr>
                        `}).join('')}
                    </tbody>
                </table>
            </div>
        `;
        
        document.getElementById('sessionsTable').innerHTML = tableHTML;
    } catch (error) {
        console.error('Ошибка загрузки сессий:', error);
    }
}

async function activateSession(sessionId) {
    if (!confirm('Активировать эту сессию? Текущая активная сессия будет деактивирована.')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/codes/sessions/${sessionId}/activate`, {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('Сессия активирована!');
            loadSessions();
            loadDashboard();
        }
    } catch (error) {
        alert('Ошибка активации: ' + error.message);
    }
}

// ==================== МОНИТОРИНГ ====================

async function loadStudentsWithoutCodes() {
    try {
        const response = await fetch('/api/monitoring/students-without-codes');
        const data = await response.json();
        
        if (data.students.length === 0) {
            document.getElementById('studentsWithoutCodes').innerHTML = `
                <div class="alert alert-success mb-0">
                    <i class="bi bi-check-circle"></i> Все ученики получили коды!
                </div>
            `;
            return;
        }
        
        const html = `
            <p><strong>Олимпиада:</strong> ${data.session}</p>
            <p><strong>Учеников без кодов:</strong> ${data.count}</p>
            <hr>
            <div class="list-group">
                ${data.students.map(s => `
                    <div class="list-group-item">
                        <i class="bi bi-person"></i> ${s.full_name}
                        ${s.telegram_id ? '<span class="badge bg-info ms-2">В боте</span>' : ''}
                    </div>
                `).join('')}
            </div>
        `;
        
        document.getElementById('studentsWithoutCodes').innerHTML = html;
    } catch (error) {
        console.error('Ошибка загрузки учеников без кодов:', error);
    }
}

// Загружаем при переключении на таб мониторинга
document.querySelector('button[data-bs-target="#monitoring-tab"]').addEventListener('click', () => {
    loadStudentsWithoutCodes();
});

// ==================== РЕГИСТРАЦИЯ ====================

async function loadClassesData() {
    try {
        const response = await fetch('/api/students/classes');
        const data = await response.json();

        // Обновляем селекты
        const classSelect = document.getElementById('exportClassSelect');
        const parallelSelect = document.getElementById('exportParallelSelect');

        // Заполняем класс
        const uniqueClasses = [...new Set(data.classes.map(c => c.class_number))];
        uniqueClasses.sort((a, b) => a - b);

        uniqueClasses.forEach(classNum => {
            const option = document.createElement('option');
            option.value = classNum;
            option.textContent = `${classNum} класс`;
            classSelect.appendChild(option);
        });

        // Обновляем информацию
        const totalStudents = data.classes.reduce((sum, c) => sum + c.students_count, 0);
        document.getElementById('registrationInfo').innerHTML = `
            <h3>${totalStudents}</h3>
            <p class="text-muted mb-0">Всего учеников</p>
            <hr>
            <h3>${data.classes.length}</h3>
            <p class="text-muted mb-0">Классов и параллелей</p>
        `;

        // Отображаем список классов
        const classesHTML = `
            <div class="table-responsive">
                <table class="table table-hover">
                    <thead class="table-light">
                        <tr>
                            <th>Класс</th>
                            <th>Учеников</th>
                            <th>Действия</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.classes.map(c => `
                            <tr>
                                <td><strong>${c.display}</strong></td>
                                <td>${c.students_count}</td>
                                <td>
                                    <a href="/api/students/export/registration-codes?class_number=${c.class_number}${c.parallel ? '&parallel=' + encodeURIComponent(c.parallel) : ''}"
                                       class="btn btn-sm btn-success">
                                        <i class="bi bi-download"></i> Экспорт
                                    </a>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;

        document.getElementById('classesList').innerHTML = classesHTML;

        // Обработчик изменения класса для фильтрации параллелей
        // Используем onchange вместо addEventListener чтобы избежать дублирования
        classSelect.onchange = () => {
            const selectedClass = classSelect.value;

            // Очищаем селект параллелей
            parallelSelect.innerHTML = '<option value="">Все параллели</option>';

            if (selectedClass) {
                // Фильтруем параллели для выбранного класса
                const parallels = data.classes
                    .filter(c => c.class_number == selectedClass && c.parallel)
                    .map(c => c.parallel);

                parallels.forEach(parallel => {
                    const option = document.createElement('option');
                    option.value = parallel;
                    option.textContent = parallel;
                    parallelSelect.appendChild(option);
                });
            }
        };

    } catch (error) {
        console.error('Ошибка загрузки классов:', error);
    }
}

function exportRegistrationCodes() {
    const classNum = document.getElementById('exportClassSelect').value;
    const parallel = document.getElementById('exportParallelSelect').value;

    let url = '/api/students/export/registration-codes?';
    if (classNum) url += `class_number=${classNum}&`;
    if (parallel) url += `parallel=${encodeURIComponent(parallel)}&`;

    window.location.href = url;
}

// Загружаем при переключении на таб регистрации
document.querySelector('button[data-bs-target="#registration-tab"]').addEventListener('click', () => {
    loadClassesData();
});

// ==================== УПРАВЛЕНИЕ ====================

// Загружаем при переключении на таб управления
document.querySelector('button[data-bs-target="#management-tab"]').addEventListener('click', () => {
    loadManagementData();
});

async function loadManagementData() {
    // Загружаем классы для селекта
    try {
        const response = await fetch('/api/admin/classes');
        const classes = await response.json();

        const classSelect = document.getElementById('deleteClassSelect');
        classSelect.innerHTML = '<option value="">-- Выберите класс --</option>';

        classes.forEach(c => {
            const option = document.createElement('option');
            option.value = c.class_number;
            option.textContent = `${c.class_number} класс (${c.total_students} учеников)`;
            classSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Ошибка загрузки классов:', error);
    }

    // Загружаем олимпиады для селекта
    try {
        const response = await fetch('/api/admin/olympiads');
        const olympiads = await response.json();

        const olympiadSelect = document.getElementById('olympiadSelect');
        olympiadSelect.innerHTML = '<option value="">-- Выберите олимпиаду --</option>';

        olympiads.forEach(o => {
            const option = document.createElement('option');
            option.value = o.id;
            option.textContent = `${o.subject} - ${new Date(o.date).toLocaleDateString('ru-RU')}`;
            option.dataset.olympiad = JSON.stringify(o);
            olympiadSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Ошибка загрузки олимпиад:', error);
    }
}

// Просмотр ученика по ID
async function viewStudent() {
    const studentId = document.getElementById('deleteStudentId').value;
    if (!studentId) {
        alert('Введите ID ученика');
        return;
    }

    try {
        const response = await fetch(`/api/admin/students/${studentId}`);
        if (!response.ok) {
            throw new Error('Ученик не найден');
        }

        const student = await response.json();

        document.getElementById('studentInfo').innerHTML = `
            <div class="alert alert-info">
                <strong>ФИО:</strong> ${student.full_name}<br>
                <strong>Класс:</strong> ${student.class_number || '-'}${student.parallel || ''}<br>
                <strong>Telegram:</strong> ${student.telegram_id || 'Не зарегистрирован'}<br>
                <strong>Username:</strong> ${student.telegram_username || '-'}
            </div>
        `;
    } catch (error) {
        document.getElementById('studentInfo').innerHTML = `
            <div class="alert alert-danger">
                <i class="bi bi-x-circle"></i> ${error.message}
            </div>
        `;
    }
}

// Удаление ученика
async function deleteStudent() {
    const studentId = document.getElementById('deleteStudentId').value;
    if (!studentId) {
        alert('Введите ID ученика');
        return;
    }

    if (!confirm(`Вы уверены, что хотите удалить ученика с ID ${studentId}?`)) {
        return;
    }

    try {
        const response = await fetch(`/api/admin/students/${studentId}`, {
            method: 'DELETE'
        });

        const result = await response.json();

        if (result.success) {
            alert('✅ Ученик успешно удален');
            document.getElementById('deleteStudentId').value = '';
            document.getElementById('studentInfo').innerHTML = '';
            loadDashboard();
            loadStudentsStats();
        } else {
            alert('❌ Ошибка: ' + (result.message || 'Неизвестная ошибка'));
        }
    } catch (error) {
        alert('❌ Ошибка удаления: ' + error.message);
    }
}

// Очистка всей базы учеников
async function clearAllStudents() {
    const confirmation = prompt('⚠️ ВНИМАНИЕ! Это удалит ВСЕХ учеников из базы данных!\n\nДля подтверждения введите: DELETE_ALL');

    if (confirmation !== 'DELETE_ALL') {
        alert('Отменено');
        return;
    }

    try {
        const response = await fetch('/api/admin/students?confirm=YES_DELETE_ALL', {
            method: 'DELETE'
        });

        const result = await response.json();

        if (result.success) {
            alert(`✅ База данных очищена. Удалено учеников: ${result.deleted_count}`);
            loadDashboard();
            loadStudentsStats();
        } else {
            alert('❌ Ошибка: ' + (result.message || 'Неизвестная ошибка'));
        }
    } catch (error) {
        alert('❌ Ошибка очистки: ' + error.message);
    }
}

// Просмотр учеников класса
async function viewClassStudents() {
    const classNumber = document.getElementById('deleteClassSelect').value;
    if (!classNumber) {
        alert('Выберите класс');
        return;
    }

    try {
        const response = await fetch(`/api/admin/classes/${classNumber}/students`);
        const students = await response.json();

        if (students.length === 0) {
            alert('В этом классе нет учеников');
            return;
        }

        // Показываем карточку со списком
        const card = document.getElementById('classStudentsCard');
        const tbody = document.getElementById('classStudentsTableBody');

        tbody.innerHTML = students.map(s => `
            <tr>
                <td>${s.id}</td>
                <td>${s.full_name}</td>
                <td>${s.class_number || '-'}${s.parallel || ''}</td>
                <td>${s.telegram_id || '-'}</td>
                <td>
                    ${s.telegram_id
                        ? '<span class="badge bg-success">Зарегистрирован</span>'
                        : '<span class="badge bg-warning">Не зарегистрирован</span>'}
                </td>
                <td>
                    <button class="btn btn-sm btn-danger" onclick="deleteStudentById(${s.id})">
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            </tr>
        `).join('');

        card.style.display = 'block';

        // Прокручиваем к карточке
        card.scrollIntoView({ behavior: 'smooth' });

        // Обновляем информацию о классе
        document.getElementById('classInfo').innerHTML = `
            <div class="alert alert-info">
                <strong>Класс:</strong> ${classNumber}<br>
                <strong>Учеников:</strong> ${students.length}
            </div>
        `;
    } catch (error) {
        alert('❌ Ошибка загрузки учеников: ' + error.message);
    }
}

// Удаление ученика по ID (из таблицы)
async function deleteStudentById(studentId) {
    if (!confirm(`Удалить ученика с ID ${studentId}?`)) {
        return;
    }

    try {
        const response = await fetch(`/api/admin/students/${studentId}`, {
            method: 'DELETE'
        });

        const result = await response.json();

        if (result.success) {
            alert('✅ Ученик удален');
            // Перезагружаем список класса
            viewClassStudents();
            loadDashboard();
        } else {
            alert('❌ Ошибка: ' + (result.message || 'Неизвестная ошибка'));
        }
    } catch (error) {
        alert('❌ Ошибка удаления: ' + error.message);
    }
}

// Удаление класса
async function deleteClass() {
    const classNumber = document.getElementById('deleteClassSelect').value;
    if (!classNumber) {
        alert('Выберите класс');
        return;
    }

    const confirmation = prompt(`⚠️ Это удалит ВСЕХ учеников ${classNumber} класса!\n\nДля подтверждения введите номер класса:`);

    if (confirmation !== classNumber) {
        alert('Отменено');
        return;
    }

    try {
        const response = await fetch(`/api/admin/classes/${classNumber}`, {
            method: 'DELETE'
        });

        const result = await response.json();

        if (result.success) {
            alert(`✅ Класс ${classNumber} удален. Удалено учеников: ${result.deleted_count}`);
            document.getElementById('deleteClassSelect').value = '';
            document.getElementById('classInfo').innerHTML = '';
            document.getElementById('classStudentsCard').style.display = 'none';
            loadManagementData();
            loadDashboard();
            loadStudentsStats();
        } else {
            alert('❌ Ошибка: ' + (result.message || 'Неизвестная ошибка'));
        }
    } catch (error) {
        alert('❌ Ошибка удаления класса: ' + error.message);
    }
}

// Загрузка информации об олимпиаде
function loadOlympiadInfo() {
    const select = document.getElementById('olympiadSelect');
    const selectedOption = select.options[select.selectedIndex];

    if (!selectedOption.value) {
        document.getElementById('olympiadInfo').innerHTML = '';
        return;
    }

    const olympiad = JSON.parse(selectedOption.dataset.olympiad);

    document.getElementById('olympiadInfo').innerHTML = `
        <div class="alert alert-info">
            <strong>Предмет:</strong> ${olympiad.subject}<br>
            <strong>Дата:</strong> ${new Date(olympiad.date).toLocaleDateString('ru-RU')}<br>
            <strong>Класс:</strong> ${olympiad.class_number || 'Не указан'}<br>
            <strong>Статус:</strong> ${olympiad.is_active
                ? '<span class="badge bg-success">Активна</span>'
                : '<span class="badge bg-secondary">Неактивна</span>'}
        </div>
    `;
}

// Активация олимпиады
async function activateOlympiad() {
    const olympiadId = document.getElementById('olympiadSelect').value;
    if (!olympiadId) {
        alert('Выберите олимпиаду');
        return;
    }

    if (!confirm('Активировать эту олимпиаду? Все остальные будут деактивированы.')) {
        return;
    }

    try {
        const response = await fetch(`/api/admin/olympiads/${olympiadId}/activate`, {
            method: 'POST'
        });

        const result = await response.json();

        if (result.success) {
            alert('✅ Олимпиада активирована!');
            loadManagementData();
            loadOlympiadInfo();
            loadDashboard();
        } else {
            alert('❌ Ошибка: ' + (result.message || 'Неизвестная ошибка'));
        }
    } catch (error) {
        alert('❌ Ошибка активации: ' + error.message);
    }
}

// Удаление олимпиады
async function deleteOlympiad() {
    const olympiadId = document.getElementById('olympiadSelect').value;
    if (!olympiadId) {
        alert('Выберите олимпиаду');
        return;
    }

    if (!confirm('⚠️ Вы уверены, что хотите удалить эту олимпиаду?\nВсе связанные коды будут потеряны!')) {
        return;
    }

    try {
        const response = await fetch(`/api/admin/olympiads/${olympiadId}`, {
            method: 'DELETE'
        });

        const result = await response.json();

        if (result.success) {
            alert('✅ Олимпиада удалена');
            document.getElementById('olympiadSelect').value = '';
            document.getElementById('olympiadInfo').innerHTML = '';
            loadManagementData();
            loadDashboard();
        } else {
            alert('❌ Ошибка: ' + (result.message || 'Неизвестная ошибка'));
        }
    } catch (error) {
        alert('❌ Ошибка удаления: ' + error.message);
    }
}