-- Исправление constraint для grade8_codes.student_id
-- Проблема: поле student_id имеет NOT NULL constraint, но должно быть nullable

-- Шаг 1: Удалить NOT NULL constraint
ALTER TABLE grade8_codes ALTER COLUMN student_id DROP NOT NULL;

-- Проверка изменений
\d grade8_codes
