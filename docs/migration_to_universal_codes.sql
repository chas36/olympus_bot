-- Миграция для универсальной системы кодов (5-11 классы)

-- Шаг 1: Создаем новую универсальную таблицу кодов
CREATE TABLE IF NOT EXISTS olympiad_codes (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES olympiad_sessions(id) ON DELETE CASCADE,
    class_number INTEGER NOT NULL, -- 5, 6, 7, 8, 9, 10, 11
    code VARCHAR(100) NOT NULL,
    student_id INTEGER REFERENCES students(id) ON DELETE SET NULL, -- NULL = не распределен
    is_assigned BOOLEAN DEFAULT FALSE, -- Распределен ли код ученику
    assigned_at TIMESTAMP,
    is_issued BOOLEAN DEFAULT FALSE, -- Выдан ли код (запрошен учеником)
    issued_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT unique_code_per_session UNIQUE(session_id, code),
    CONSTRAINT valid_class_number CHECK (class_number >= 5 AND class_number <= 11)
);

CREATE INDEX idx_olympiad_codes_session ON olympiad_codes(session_id);
CREATE INDEX idx_olympiad_codes_class ON olympiad_codes(class_number);
CREATE INDEX idx_olympiad_codes_student ON olympiad_codes(student_id);
CREATE INDEX idx_olympiad_codes_code ON olympiad_codes(code);
CREATE INDEX idx_olympiad_codes_assigned ON olympiad_codes(is_assigned);

-- Шаг 2: Создаем таблицу для дополнительных кодов 9 класса для 8-классников
CREATE TABLE IF NOT EXISTS grade8_reserve_codes (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES olympiad_sessions(id) ON DELETE CASCADE,
    class_parallel VARCHAR(10) NOT NULL, -- "8А", "8Б" и т.д.
    code VARCHAR(100) NOT NULL,
    is_used BOOLEAN DEFAULT FALSE,
    used_by_student_id INTEGER REFERENCES students(id) ON DELETE SET NULL,
    used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT unique_reserve_code UNIQUE(session_id, code)
);

CREATE INDEX idx_grade8_reserve_session ON grade8_reserve_codes(session_id);
CREATE INDEX idx_grade8_reserve_class ON grade8_reserve_codes(class_parallel);
CREATE INDEX idx_grade8_reserve_used ON grade8_reserve_codes(is_used);

-- Шаг 3: Мигрируем данные из старых таблиц (если есть)

-- Миграция grade8_codes -> olympiad_codes
INSERT INTO olympiad_codes (session_id, class_number, code, student_id, is_assigned, assigned_at, is_issued, issued_at)
SELECT
    session_id,
    8 as class_number,
    code,
    student_id,
    (student_id IS NOT NULL) as is_assigned,
    issued_at as assigned_at,
    is_issued,
    issued_at
FROM grade8_codes
ON CONFLICT DO NOTHING;

-- Миграция grade9_codes -> olympiad_codes (как резервные коды для 8 класса)
INSERT INTO olympiad_codes (session_id, class_number, code, student_id, is_assigned, is_issued)
SELECT
    session_id,
    9 as class_number,
    code,
    assigned_student_id,
    is_used as is_assigned,
    is_used as is_issued
FROM grade9_codes
ON CONFLICT DO NOTHING;

-- Шаг 4: Обновляем таблицу code_requests для работы с новой системой
ALTER TABLE code_requests ADD COLUMN IF NOT EXISTS olympiad_code_id INTEGER REFERENCES olympiad_codes(id) ON DELETE SET NULL;

-- Шаг 5: Добавляем комментарии
COMMENT ON TABLE olympiad_codes IS 'Универсальная таблица кодов для всех классов (5-11)';
COMMENT ON TABLE grade8_reserve_codes IS 'Дополнительные коды из пула 9 класса для 8-классников';

COMMENT ON COLUMN olympiad_codes.is_assigned IS 'Код предварительно распределен ученику (Вариант 1)';
COMMENT ON COLUMN olympiad_codes.is_issued IS 'Код выдан ученику по запросу (Вариант 2)';

-- Вывод статистики после миграции
SELECT
    class_number,
    COUNT(*) as total_codes,
    COUNT(student_id) as assigned_codes,
    COUNT(*) - COUNT(student_id) as unassigned_codes
FROM olympiad_codes
GROUP BY class_number
ORDER BY class_number;

-- Готово!
