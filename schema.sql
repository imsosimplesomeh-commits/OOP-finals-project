-- schema.sql - builds the empty Student Grade Management database (PostgreSQL)
-- Safe to run again: every table uses IF NOT EXISTS, so existing rows are kept.
-- db.init_db() runs this same file when the app starts.

-- 1. students master table
CREATE TABLE IF NOT EXISTS students (
    student_id TEXT PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE,
    program VARCHAR(50) NOT NULL,
    year_level INTEGER NOT NULL CHECK (year_level > 0),
    status VARCHAR(20) NOT NULL DEFAULT 'Active'
);

-- 2. teachers master table
CREATE TABLE IF NOT EXISTS teachers (
    teacher_id TEXT PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE,
    department VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'Active'
);

-- 3. subjects master table
CREATE TABLE IF NOT EXISTS subjects (
    subject_id SERIAL PRIMARY KEY,
    subject_code VARCHAR(20) UNIQUE NOT NULL,
    subject_name VARCHAR(150) NOT NULL,
    description TEXT,
    units INTEGER NOT NULL DEFAULT 3 CHECK (units > 0)
);

-- 4. class offerings
CREATE TABLE IF NOT EXISTS class_offerings (
    class_id SERIAL PRIMARY KEY,
    subject_id INTEGER NOT NULL REFERENCES subjects(subject_id) ON DELETE RESTRICT,
    teacher_id TEXT NOT NULL REFERENCES teachers(teacher_id) ON DELETE RESTRICT,
    class_code VARCHAR(50) UNIQUE NOT NULL,
    section VARCHAR(20),
    schedule VARCHAR(100),
    room VARCHAR(50),
    school_year VARCHAR(20) NOT NULL,
    semester VARCHAR(20) NOT NULL
);

-- 5. grading periods
CREATE TABLE IF NOT EXISTS grading_periods (
    period_id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    period_order INTEGER NOT NULL CHECK (period_order > 0),
    start_date DATE,
    end_date DATE,
    school_year VARCHAR(20),
    semester VARCHAR(20)
);

-- 6. grade components are shared; each class stores its own weights
CREATE TABLE IF NOT EXISTS grade_components (
    component_id SERIAL PRIMARY KEY,
    period_id INTEGER NOT NULL REFERENCES grading_periods(period_id) ON DELETE RESTRICT,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(50) NOT NULL,
    max_score NUMERIC(6, 2) NOT NULL CHECK (max_score > 0),
    description TEXT
);

-- 7. weight of each component in each class
CREATE TABLE IF NOT EXISTS grade_percentages (
    percentage_id SERIAL PRIMARY KEY,
    class_id INTEGER NOT NULL REFERENCES class_offerings(class_id) ON DELETE RESTRICT,
    component_id INTEGER NOT NULL REFERENCES grade_components(component_id) ON DELETE RESTRICT,
    percentage NUMERIC(5, 2) NOT NULL CHECK (percentage BETWEEN 0 AND 100),
    UNIQUE(class_id, component_id)
);

-- 8. student enrollments
CREATE TABLE IF NOT EXISTS enrollments (
    enrollment_id SERIAL PRIMARY KEY,
    student_id TEXT NOT NULL REFERENCES students(student_id) ON DELETE RESTRICT,
    class_id INTEGER NOT NULL REFERENCES class_offerings(class_id) ON DELETE RESTRICT,
    enroll_date DATE NOT NULL DEFAULT CURRENT_DATE,
    status VARCHAR(20) NOT NULL DEFAULT 'Enrolled',
    UNIQUE(student_id, class_id)
);

-- 9. grade component scores
CREATE TABLE IF NOT EXISTS grade_component_scores (
    score_id SERIAL PRIMARY KEY,
    enrollment_id INTEGER NOT NULL REFERENCES enrollments(enrollment_id) ON DELETE RESTRICT,
    component_id INTEGER NOT NULL REFERENCES grade_components(component_id) ON DELETE RESTRICT,
    score NUMERIC(6, 2) NOT NULL CHECK (score >= 0),
    remarks TEXT,
    date_recorded DATE NOT NULL DEFAULT CURRENT_DATE,
    UNIQUE(enrollment_id, component_id)
);

-- 10. computed grades, one row per enrollment
CREATE TABLE IF NOT EXISTS grades (
    grade_id SERIAL PRIMARY KEY,
    enrollment_id INTEGER NOT NULL UNIQUE REFERENCES enrollments(enrollment_id) ON DELETE RESTRICT,
    midterm_grade NUMERIC(9, 6),
    finals_grade NUMERIC(9, 6),
    overall_grade NUMERIC(9, 6),
    midterm_equiv NUMERIC(3, 2),
    final_equiv NUMERIC(3, 2),
    remarks VARCHAR(50),
    date_encoded DATE DEFAULT CURRENT_DATE
);

-- 11. audit trail: who changed what, old and new value, when
CREATE TABLE IF NOT EXISTS audit_log (
    log_id SERIAL PRIMARY KEY,
    table_name TEXT NOT NULL,
    record_id TEXT NOT NULL,
    action TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,
    changed_by TEXT NOT NULL,
    changed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- older databases made before this change: widen the three percentage columns
-- (safe to run again; it keeps the rows). Needed so 96.995 still converts to 1.25, not 1.00.
ALTER TABLE grades
    ALTER COLUMN midterm_grade TYPE NUMERIC(9, 6),
    ALTER COLUMN finals_grade TYPE NUMERIC(9, 6),
    ALTER COLUMN overall_grade TYPE NUMERIC(9, 6);
