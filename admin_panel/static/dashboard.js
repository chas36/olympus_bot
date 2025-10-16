// dashboard.js - JavaScript для админ-панели v2

// Обновление времени
function updateTime() {
    const now = new Date();
    document.getElementById('currentTime').textContent = now.toLocaleTimeString('ru-RU');
}
setInterval(updateTime, 1000);
updateTime();

// Глобальные переменные
let allStudents = [];
let filteredStudents = [];

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

        // Процент регистрации
        const registrationPercent = data.total > 0
            ? Math.round((data.registered / data.total) * 100)
            : 0;

        // Строим статистику по классам
        let byClassHTML = '';
        if (data.by_class && Object.keys(data.by_class).length > 0) {
            byClassHTML = '<hr><h6 class="mb-2">По классам:</h6>';
            byClassHTML += '<div class="row">';
            Object.entries(data.by_class).forEach(([classNum, count]) => {
                byClassHTML += `
                    <div class="col-4 mb-2">
                        <div class="d-flex justify-content-between">
                            <span class="small">${classNum}:</span>
                            <strong class="small">${count}</strong>
                        </div>
                    </div>
                `;
            });
            byClassHTML += '</div>';
        }

        const statsHTML = `
            <div class="row text-center mb-3">
                <div class="col-4">
                    <h2 class="mb-1">${data.total}</h2>
                    <small class="text-muted">Всего</small>
                </div>
                <div class="col-4">
                    <h2 class="text-success mb-1">${data.registered}</h2>
                    <small class="text-muted">Зарегистрировано</small>
                </div>
                <div class="col-4">
                    <h2 class="text-warning mb-1">${data.not_registered}</h2>
                    <small class="text-muted">Ожидают</small>
                </div>
            </div>
            <div class="progress mb-2" style="height: 20px;">
                <div class="progress-bar bg-success" style="width: ${registrationPercent}%">
                    ${registrationPercent}%
                </div>
            </div>
            <p class="text-center text-muted small mb-0">Процент регистрации</p>
            ${byClassHTML}
            <hr>
            <button class="btn btn-primary btn-sm w-100" onclick="loadStudentsList()">
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
        // Загружаем всех учеников, включая не зарегистрированных
        const response = await fetch('/api/students/?include_inactive=true');
        allStudents = await response.json();

        // Заполняем фильтры
        populateStudentsFilters();

        // Показываем учеников
        filteredStudents = allStudents;
        displayStudents(filteredStudents);
    } catch (error) {
        console.error('Ошибка загрузки списка учеников:', error);
    }
}

function populateStudentsFilters() {
    // Собираем уникальные классы и параллели
    const classes = new Set();
    const parallels = new Set();

    allStudents.forEach(s => {
        if (s.class_number) {
            classes.add(s.class_number);
            if (s.parallel) {
                parallels.add(s.parallel);
            }
        }
    });

    // Заполняем селект классов
    const classSelect = document.getElementById('filterClass');
    classSelect.innerHTML = '<option value="">Все классы</option>';
    [...classes].sort((a, b) => a - b).forEach(c => {
        const option = document.createElement('option');
        option.value = c;
        option.textContent = `${c} класс`;
        classSelect.appendChild(option);
    });

    // Заполняем селект параллелей
    const parallelSelect = document.getElementById('filterParallel');
    parallelSelect.innerHTML = '<option value="">Все параллели</option>';
    [...parallels].sort().forEach(p => {
        const option = document.createElement('option');
        option.value = p;
        option.textContent = p;
        parallelSelect.appendChild(option);
    });
}

function displayStudents(students) {
    const tbody = document.querySelector('#studentsTable tbody');

    if (students.length === 0) {
        tbody.innerHTML = `
            <tr><td colspan="7" class="text-center text-muted">Нет учеников</td></tr>
        `;
        document.getElementById('studentsCount').textContent = '';
        return;
    }

    const rows = students.map(s => `
        <tr>
            <td>${s.id}</td>
            <td>${s.full_name}</td>
            <td>${s.class_display || '-'}</td>
            <td><code class="small">${s.registration_code}</code></td>
            <td>
                ${s.is_registered
                    ? '<span class="badge bg-success">Зарегистрирован</span>'
                    : '<span class="badge bg-warning">Ожидает</span>'}
            </td>
            <td>${s.telegram_id || '-'}</td>
            <td>
                <button class="btn btn-sm btn-outline-primary" onclick="showEditStudentModal(${s.id})">
                    <i class="bi bi-pencil"></i>
                </button>
            </td>
        </tr>
    `).join('');

    tbody.innerHTML = rows;
    document.getElementById('studentsCount').textContent = `Показано: ${students.length} из ${allStudents.length}`;
}

function filterStudents() {
    const classFilter = document.getElementById('filterClass').value;
    const parallelFilter = document.getElementById('filterParallel').value;
    const statusFilter = document.getElementById('filterStatus').value;

    filteredStudents = allStudents.filter(s => {
        // Фильтр по классу
        if (classFilter && s.class_number != classFilter) {
            return false;
        }

        // Фильтр по параллели
        if (parallelFilter && s.parallel !== parallelFilter) {
            return false;
        }

        // Фильтр по статусу
        if (statusFilter === 'registered' && !s.is_registered) {
            return false;
        }
        if (statusFilter === 'not_registered' && s.is_registered) {
            return false;
        }

        return true;
    });

    displayStudents(filteredStudents);
}

function resetFilters() {
    document.getElementById('filterClass').value = '';
    document.getElementById('filterParallel').value = '';
    document.getElementById('filterStatus').value = '';
    filterStudents();
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

        const grade8 = data.by_class?.grade8 || { total: 0, assigned: 0, unassigned: 0, issued: 0 };
        const grade8Reserve = data.grade8_reserve || { total: 0, used: 0, available: 0 };

        const statsHTML = `
            <h6 class="mb-3">8 класс:</h6>
            <div class="mb-3">
                <div class="d-flex justify-content-between mb-1">
                    <span>Всего:</span>
                    <strong>${grade8.total}</strong>
                </div>
                <div class="d-flex justify-content-between mb-1">
                    <span>Распределено:</span>
                    <strong class="text-success">${grade8.assigned}</strong>
                </div>
                <div class="d-flex justify-content-between mb-1">
                    <span>Не распределено:</span>
                    <strong class="text-warning">${grade8.unassigned}</strong>
                </div>
                <div class="d-flex justify-content-between">
                    <span>Выдано:</span>
                    <strong class="text-info">${grade8.issued}</strong>
                </div>
            </div>

            <h6 class="mb-3">Резерв 8 класса (из 9 класса):</h6>
            <div>
                <div class="d-flex justify-content-between mb-1">
                    <span>Всего:</span>
                    <strong>${grade8Reserve.total}</strong>
                </div>
                <div class="d-flex justify-content-between mb-1">
                    <span>Использовано:</span>
                    <strong class="text-danger">${grade8Reserve.used}</strong>
                </div>
                <div class="d-flex justify-content-between">
                    <span>Доступно:</span>
                    <strong class="text-success">${grade8Reserve.available}</strong>
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
                                    ${s.is_active
                                        ? `<button class="btn btn-sm btn-danger" onclick="deactivateSession(${s.id})">
                                            <i class="bi bi-pause-circle"></i> Деактивировать
                                           </button>`
                                        : `<button class="btn btn-sm btn-primary" onclick="activateSession(${s.id})">
                                            <i class="bi bi-play"></i> Активировать
                                           </button>`}
                                    <button class="btn btn-sm btn-warning" onclick="distributeSessionCodes(${s.id})">
                                        <i class="bi bi-arrow-down-up"></i> Распределить
                                    </button>
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

async function deactivateSession(sessionId) {
    if (!confirm('Деактивировать эту сессию?')) {
        return;
    }

    try {
        const response = await fetch(`/api/admin/olympiads/${sessionId}/deactivate`, {
            method: 'POST'
        });

        const result = await response.json();

        if (result.success) {
            alert('✅ Сессия деактивирована!');
            loadSessions();
            loadDashboard();
        } else {
            alert('❌ Ошибка: ' + (result.message || 'Неизвестная ошибка'));
        }
    } catch (error) {
        alert('❌ Ошибка деактивации: ' + error.message);
    }
}

async function distributeSessionCodes(sessionId) {
    if (!confirm('Распределить коды этой сессии между всеми учениками?\n\nКоды будут распределены по классам и параллелям между ВСЕМИ учениками (не только зарегистрированными).')) {
        return;
    }

    try {
        const response = await fetch(`/api/codes/sessions/${sessionId}/distribute`, {
            method: 'POST'
        });

        const result = await response.json();

        if (result.success) {
            let message = `✅ ${result.message}\n\nДетали распределения:\n`;
            if (result.distribution_log && result.distribution_log.length > 0) {
                result.distribution_log.forEach(log => {
                    message += `\n${log.class}: ${log.codes_assigned} кодов из ${log.students} учеников`;
                });
            }
            alert(message);
            loadSessions();
            loadDashboard();
        } else {
            alert('❌ Ошибка: ' + (result.message || 'Неизвестная ошибка'));
        }
    } catch (error) {
        alert('❌ Ошибка распределения: ' + error.message);
    }
}

// ==================== МОНИТОРИНГ ====================

async function loadAllOlympiads() {
    try {
        const response = await fetch('/api/monitoring/all-sessions');
        const data = await response.json();

        const tbody = document.querySelector('#allOlympiadsTable tbody');

        if (data.sessions.length === 0) {
            tbody.innerHTML = `
                <tr><td colspan="9" class="text-center text-muted">Нет олимпиад</td></tr>
            `;
            return;
        }

        const rows = data.sessions.map(s => {
            const date = new Date(s.date);
            const dateStr = isNaN(date.getTime()) ? 'Дата не указана' : date.toLocaleDateString('ru-RU');

            return `
                <tr>
                    <td>${s.id}</td>
                    <td><strong>${s.subject}</strong></td>
                    <td>${dateStr}</td>
                    <td>${s.stage || '-'}</td>
                    <td>${s.class_number || '-'}</td>
                    <td>
                        ${s.is_active
                            ? '<span class="badge bg-success">Активна</span>'
                            : '<span class="badge bg-secondary">Неактивна</span>'}
                    </td>
                    <td>
                        <span class="badge bg-info">${s.issued_codes}/${s.total_codes}</span>
                    </td>
                    <td>
                        <span class="badge bg-primary">${s.code_requests}</span>
                    </td>
                    <td>
                        <span class="badge bg-success">${s.screenshots}</span>
                    </td>
                </tr>
            `;
        }).join('');

        tbody.innerHTML = rows;
    } catch (error) {
        console.error('Ошибка загрузки всех олимпиад:', error);
    }
}

async function loadActiveOlympiadParticipants() {
    try {
        const response = await fetch('/api/monitoring/active-session/participants');
        const data = await response.json();

        const container = document.getElementById('activeOlympiadParticipants');

        if (!data.session) {
            container.innerHTML = `
                <div class="alert alert-warning mb-0">
                    <i class="bi bi-exclamation-triangle"></i> Нет активной олимпиады
                </div>
            `;
            return;
        }

        const sessionDate = new Date(data.session.date);
        const sessionDateStr = isNaN(sessionDate.getTime()) ? 'Дата не указана' : sessionDate.toLocaleDateString('ru-RU');

        let html = `
            <h4>${data.session.subject}</h4>
            <p class="text-muted">
                ${sessionDateStr}
                ${data.session.stage ? `• ${data.session.stage}` : ''}
            </p>
            <hr>
            <p><strong>Участников:</strong> ${data.total_participants}</p>
        `;

        if (data.participants.length === 0) {
            html += `
                <div class="alert alert-info">
                    <i class="bi bi-info-circle"></i> Пока нет участников
                </div>
            `;
        } else {
            html += `
                <div class="table-responsive">
                    <table class="table table-sm table-hover">
                        <thead class="table-light">
                            <tr>
                                <th>ФИО</th>
                                <th>Класс</th>
                                <th>Время запроса</th>
                                <th>Код</th>
                                <th>Скриншот</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${data.participants.map(p => {
                                const requestedAt = new Date(p.requested_at);
                                const requestedTimeStr = requestedAt.toLocaleTimeString('ru-RU');

                                return `
                                    <tr>
                                        <td>${p.full_name}</td>
                                        <td>${p.class_display}</td>
                                        <td><small>${requestedTimeStr}</small></td>
                                        <td><code class="small">${p.code}</code></td>
                                        <td>
                                            ${p.screenshot_submitted
                                                ? '<span class="badge bg-success"><i class="bi bi-check"></i> Да</span>'
                                                : '<span class="badge bg-warning"><i class="bi bi-clock"></i> Нет</span>'}
                                        </td>
                                    </tr>
                                `;
                            }).join('')}
                        </tbody>
                    </table>
                </div>
            `;
        }

        container.innerHTML = html;
    } catch (error) {
        console.error('Ошибка загрузки участников:', error);
    }
}

// Загружаем при переключении на таб мониторинга
document.querySelector('button[data-bs-target="#monitoring-tab"]').addEventListener('click', () => {
    loadAllOlympiads();
    loadActiveOlympiadParticipants();
});

// Загружаем при переключении на таб учеников
document.querySelector('button[data-bs-target="#students-tab"]').addEventListener('click', () => {
    if (allStudents.length === 0) {
        loadStudentsList();
    }
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
        document.getElementById('olympiadActionButtons').innerHTML = '';
        return;
    }

    const olympiad = JSON.parse(selectedOption.dataset.olympiad);
    console.log('Загружена олимпиада:', olympiad.subject, 'Активна:', olympiad.is_active);

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

    // Показываем кнопки в зависимости от статуса
    if (olympiad.is_active) {
        console.log('Показываем кнопку деактивации');
        document.getElementById('olympiadActionButtons').innerHTML = `
            <button class="btn btn-warning w-100 mb-2" onclick="deactivateOlympiad()">
                <i class="bi bi-pause-circle"></i> Деактивировать
            </button>
            <button class="btn btn-danger w-100 mb-2" onclick="deleteOlympiad()">
                <i class="bi bi-trash"></i> Удалить олимпиаду
            </button>
        `;
    } else {
        console.log('Показываем кнопку активации');
        document.getElementById('olympiadActionButtons').innerHTML = `
            <button class="btn btn-success w-100 mb-2" onclick="activateOlympiad()">
                <i class="bi bi-check-circle"></i> Активировать
            </button>
            <button class="btn btn-danger w-100 mb-2" onclick="deleteOlympiad()">
                <i class="bi bi-trash"></i> Удалить олимпиаду
            </button>
        `;
    }
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

// Деактивация олимпиады
async function deactivateOlympiad() {
    const olympiadId = document.getElementById('olympiadSelect').value;
    if (!olympiadId) {
        alert('Выберите олимпиаду');
        return;
    }

    if (!confirm('Деактивировать эту олимпиаду?')) {
        return;
    }

    try {
        const response = await fetch(`/api/admin/olympiads/${olympiadId}/deactivate`, {
            method: 'POST'
        });

        const result = await response.json();

        if (result.success) {
            alert('✅ Олимпиада деактивирована!');
            loadManagementData();
            loadOlympiadInfo();
            loadDashboard();
        } else {
            alert('❌ Ошибка: ' + (result.message || 'Неизвестная ошибка'));
        }
    } catch (error) {
        alert('❌ Ошибка деактивации: ' + error.message);
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
            document.getElementById('olympiadActionButtons').innerHTML = '';
            loadManagementData();
            loadDashboard();
        } else {
            alert('❌ Ошибка: ' + (result.message || 'Неизвестная ошибка'));
        }
    } catch (error) {
        alert('❌ Ошибка удаления: ' + error.message);
    }
}

// Удаление всех олимпиад
async function deleteAllOlympiads() {
    if (!confirm('⚠️⚠️⚠️ ВЫ УВЕРЕНЫ?\n\nЭто действие удалит ВСЕ олимпиады и все связанные коды!\nЭто действие НЕОБРАТИМО!')) {
        return;
    }

    if (!confirm('Последнее предупреждение!\nВы действительно хотите удалить ВСЕ олимпиады?')) {
        return;
    }

    try {
        const response = await fetch('/api/admin/olympiads', {
            method: 'DELETE'
        });

        const result = await response.json();

        if (result.success) {
            alert(`✅ Удалено олимпиад: ${result.deleted_count}`);
            document.getElementById('olympiadSelect').value = '';
            document.getElementById('olympiadInfo').innerHTML = '';
            document.getElementById('olympiadActionButtons').innerHTML = '';
            loadManagementData();
            loadDashboard();
        } else {
            alert('❌ Ошибка: ' + (result.message || 'Неизвестная ошибка'));
        }
    } catch (error) {
        alert('❌ Ошибка удаления: ' + error.message);
    }
}

// ==================== УВЕДОМЛЕНИЯ ====================

// Загрузка статуса глобальных уведомлений
async function loadGlobalNotificationStatus() {
    try {
        const response = await fetch('/api/notifications/global');
        const data = await response.json();

        const switchElement = document.getElementById('globalNotificationsSwitch');
        if (switchElement) {
            switchElement.checked = data.notifications_enabled;
        }
    } catch (error) {
        console.error('Ошибка загрузки статуса уведомлений:', error);
    }
}

// Включить глобальные уведомления
async function enableGlobalNotifications() {
    try {
        const response = await fetch('/api/notifications/global', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ notifications_enabled: true })
        });

        const result = await response.json();

        if (result.notifications_enabled) {
            alert('✅ Глобальные уведомления включены');
            loadGlobalNotificationStatus();
        }
    } catch (error) {
        alert('❌ Ошибка: ' + error.message);
    }
}

// Отключить глобальные уведомления
async function disableGlobalNotifications() {
    if (!confirm('⚠️ Вы уверены? Все уведомления администратору будут отключены.')) {
        return;
    }

    try {
        const response = await fetch('/api/notifications/global', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ notifications_enabled: false })
        });

        const result = await response.json();

        if (!result.notifications_enabled) {
            alert('✅ Глобальные уведомления отключены');
            loadGlobalNotificationStatus();
        }
    } catch (error) {
        alert('❌ Ошибка: ' + error.message);
    }
}

// Проверить статус уведомлений ученика
async function checkStudentNotifications() {
    const studentId = document.getElementById('studentNotificationId').value;
    if (!studentId) {
        alert('Введите ID ученика');
        return;
    }

    try {
        const response = await fetch(`/api/notifications/student/${studentId}`);

        if (!response.ok) {
            throw new Error('Ученик не найден');
        }

        const data = await response.json();

        const statusHtml = `
            <div class="alert ${data.notifications_enabled ? 'alert-success' : 'alert-warning'}">
                <strong>Ученик:</strong> ${data.full_name}<br>
                <strong>Статус уведомлений:</strong>
                ${data.notifications_enabled
                    ? '<span class="badge bg-success">Включены</span>'
                    : '<span class="badge bg-warning">Отключены</span>'}
            </div>
        `;

        document.getElementById('studentNotificationInfo').innerHTML = statusHtml;
    } catch (error) {
        document.getElementById('studentNotificationInfo').innerHTML = `
            <div class="alert alert-danger">
                <i class="bi bi-x-circle"></i> ${error.message}
            </div>
        `;
    }
}

// Включить уведомления для ученика
async function enableStudentNotifications() {
    const studentId = document.getElementById('studentNotificationId').value;
    if (!studentId) {
        alert('Введите ID ученика');
        return;
    }

    try {
        const response = await fetch(`/api/notifications/student/${studentId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                student_id: parseInt(studentId),
                notifications_enabled: true
            })
        });

        if (!response.ok) {
            throw new Error('Ученик не найден');
        }

        const result = await response.json();
        alert('✅ ' + result.message);
        checkStudentNotifications();
    } catch (error) {
        alert('❌ Ошибка: ' + error.message);
    }
}

// Отключить уведомления для ученика
async function disableStudentNotifications() {
    const studentId = document.getElementById('studentNotificationId').value;
    if (!studentId) {
        alert('Введите ID ученика');
        return;
    }

    try {
        const response = await fetch(`/api/notifications/student/${studentId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                student_id: parseInt(studentId),
                notifications_enabled: false
            })
        });

        if (!response.ok) {
            throw new Error('Ученик не найден');
        }

        const result = await response.json();
        alert('✅ ' + result.message);
        checkStudentNotifications();
    } catch (error) {
        alert('❌ Ошибка: ' + error.message);
    }
}

// Включить уведомления для ВСЕХ учеников
async function enableAllStudentsNotifications() {
    if (!confirm('Включить уведомления для ВСЕХ учеников?')) {
        return;
    }

    try {
        const response = await fetch('/api/notifications/students/all?notifications_enabled=true', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            }
        });

        const result = await response.json();
        alert(`✅ ${result.message}`);
    } catch (error) {
        alert('❌ Ошибка: ' + error.message);
    }
}

// Отключить уведомления для ВСЕХ учеников
async function disableAllStudentsNotifications() {
    if (!confirm('⚠️ Вы уверены?\nЭто отключит уведомления для ВСЕХ учеников в системе!')) {
        return;
    }

    try {
        const response = await fetch('/api/notifications/students/all?notifications_enabled=false', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            }
        });

        const result = await response.json();
        alert(`✅ ${result.message}`);
    } catch (error) {
        alert('❌ Ошибка: ' + error.message);
    }
}

// Загружаем статус уведомлений при инициализации
document.addEventListener('DOMContentLoaded', function() {
    loadGlobalNotificationStatus();
});

// ==================== УПРАВЛЕНИЕ УЧЕНИКАМИ ====================

function showAddStudentModal() {
    // Очищаем форму
    document.getElementById('addStudentName').value = '';
    document.getElementById('addStudentClass').value = '';
    document.getElementById('addStudentParallel').value = '';

    // Показываем модальное окно
    const modal = new bootstrap.Modal(document.getElementById('addStudentModal'));
    modal.show();
}

async function createStudent() {
    const fullName = document.getElementById('addStudentName').value.trim();
    const classNumber = document.getElementById('addStudentClass').value;
    const parallel = document.getElementById('addStudentParallel').value.trim();

    if (!fullName) {
        alert('Введите ФИО ученика');
        return;
    }

    const data = {
        full_name: fullName
    };

    if (classNumber) {
        data.class_number = parseInt(classNumber);
    }

    if (parallel) {
        data.parallel = parallel;
    }

    try {
        const response = await fetch('/api/students/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (response.ok && result.success) {
            alert(`✅ Ученик создан!\n\nИмя: ${result.student.full_name}\nКод: ${result.student.registration_code}\nКласс: ${result.student.class_display || 'Не указан'}`);

            // Закрываем модальное окно
            bootstrap.Modal.getInstance(document.getElementById('addStudentModal')).hide();

            // Перезагружаем список учеников
            loadStudentsList();
            loadStudentsStats();
            loadDashboard();
        } else {
            alert('❌ Ошибка: ' + (result.detail || result.message || 'Неизвестная ошибка'));
        }
    } catch (error) {
        alert('❌ Ошибка создания ученика: ' + error.message);
    }
}

async function showEditStudentModal(studentId) {
    try {
        // Загружаем данные ученика
        const response = await fetch(`/api/students/${studentId}`);
        const student = await response.json();

        if (!response.ok) {
            throw new Error(student.detail || 'Ученик не найден');
        }

        // Заполняем форму
        document.getElementById('editStudentId').value = student.id;
        document.getElementById('editStudentName').value = student.full_name;
        document.getElementById('editStudentClass').value = student.class_number || '';
        document.getElementById('editStudentParallel').value = student.parallel || '';

        // Показываем модальное окно
        const modal = new bootstrap.Modal(document.getElementById('editStudentModal'));
        modal.show();
    } catch (error) {
        alert('❌ Ошибка загрузки данных ученика: ' + error.message);
    }
}

async function updateStudent() {
    const studentId = document.getElementById('editStudentId').value;
    const fullName = document.getElementById('editStudentName').value.trim();
    const classNumber = document.getElementById('editStudentClass').value;
    const parallel = document.getElementById('editStudentParallel').value.trim();

    if (!fullName) {
        alert('Введите ФИО ученика');
        return;
    }

    const data = {
        full_name: fullName
    };

    if (classNumber) {
        data.class_number = parseInt(classNumber);
    } else {
        data.class_number = null;
    }

    if (parallel) {
        data.parallel = parallel;
    } else {
        data.parallel = null;
    }

    try {
        const response = await fetch(`/api/students/${studentId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (response.ok && result.success) {
            alert(`✅ ${result.message}\n\nИмя: ${result.student.full_name}\nКласс: ${result.student.class_display || 'Не указан'}`);

            // Закрываем модальное окно
            bootstrap.Modal.getInstance(document.getElementById('editStudentModal')).hide();

            // Перезагружаем список учеников
            loadStudentsList();
            loadStudentsStats();
            loadDashboard();
        } else {
            alert('❌ Ошибка: ' + (result.detail || result.message || 'Неизвестная ошибка'));
        }
    } catch (error) {
        alert('❌ Ошибка обновления ученика: ' + error.message);
    }
}