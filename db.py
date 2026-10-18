# db.py - database connection and schema setup for postgresql

import os
import psycopg2

DB_CONFIG = {
    "host": os.environ.get("PGHOST", "localhost"),
    "port": int(os.environ.get("PGPORT", 5432)),
    "dbname": os.environ.get("PGDATABASE", "Modelo_CSPC103"),
    "user": os.environ.get("PGUSER", "postgres"),
    "password": os.environ.get("PGPASSWORD"),
}


def get_connection():
    # connect to postgresql database
    return psycopg2.connect(**DB_CONFIG)


def init_db():
    # ensure database tables are created
    conn = get_connection()
    cur = conn.cursor()

    # 1. students master table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS students (
            student_id SERIAL PRIMARY KEY,
            first_name VARCHAR(100) NOT NULL,
            last_name VARCHAR(100) NOT NULL,
            email VARCHAR(150) UNIQUE NOT NULL,
            program VARCHAR(50) NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'active'
        );
    """)

    # 2. teachers master table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS teachers (
            teacher_id SERIAL PRIMARY KEY,
            first_name VARCHAR(100) NOT NULL,
            last_name VARCHAR(100) NOT NULL,
            email VARCHAR(150) UNIQUE NOT NULL,
            department VARCHAR(100) NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'active'
        );
    """)

    # 3. subjects master table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS subjects (
            subject_id SERIAL PRIMARY KEY,
            subject_code VARCHAR(20) UNIQUE NOT NULL,
            subject_name VARCHAR(150) NOT NULL,
            description TEXT,
            units INTEGER NOT NULL DEFAULT 3
        );
    """)

    # 4. class offerings
    cur.execute("""
        CREATE TABLE IF NOT EXISTS class_offerings (
            offering_id SERIAL PRIMARY KEY,
            subject_id INTEGER NOT NULL REFERENCES subjects(subject_id) ON DELETE RESTRICT,
            teacher_id INTEGER NOT NULL REFERENCES teachers(teacher_id) ON DELETE RESTRICT,
            class_code VARCHAR(50) UNIQUE NOT NULL,
            section VARCHAR(20),
            schedule VARCHAR(100),
            room VARCHAR(50),
            school_year VARCHAR(20) NOT NULL,
            semester VARCHAR(20) NOT NULL
        );
    """)

    # 5. grading periods
    cur.execute("""
        CREATE TABLE IF NOT EXISTS grading_periods (
            period_id SERIAL PRIMARY KEY,
            name VARCHAR(50) NOT NULL,
            start_date DATE,
            end_date DATE,
            school_year VARCHAR(20),
            semester VARCHAR(20)
        );
    """)

    # 6. grade percentages
    cur.execute("""
        CREATE TABLE IF NOT EXISTS grade_percentages (
            percentage_id SERIAL PRIMARY KEY,
            offering_id INTEGER NOT NULL REFERENCES class_offerings(offering_id) ON DELETE CASCADE,
            component_type VARCHAR(50) NOT NULL,
            percentage NUMERIC(5, 2) NOT NULL,
            UNIQUE(offering_id, component_type)
        );
    """)

    # 7. grade components
    cur.execute("""
        CREATE TABLE IF NOT EXISTS grade_components (
            component_id SERIAL PRIMARY KEY,
            grading_period_id INTEGER NOT NULL REFERENCES grading_periods(period_id) ON DELETE CASCADE,
            percentage_id INTEGER NOT NULL REFERENCES grade_percentages(percentage_id) ON DELETE CASCADE,
            name VARCHAR(100) NOT NULL,
            type VARCHAR(50) NOT NULL,
            max_score NUMERIC(6, 2) NOT NULL,
            description TEXT
        );
    """)

    # 8. student enrollments
    cur.execute("""
        CREATE TABLE IF NOT EXISTS enrollments (
            enrollment_id SERIAL PRIMARY KEY,
            student_id INTEGER NOT NULL REFERENCES students(student_id) ON DELETE RESTRICT,
            offering_id INTEGER NOT NULL REFERENCES class_offerings(offering_id) ON DELETE CASCADE,
            enroll_date DATE NOT NULL DEFAULT CURRENT_DATE,
            status VARCHAR(20) NOT NULL DEFAULT 'enrolled',
            UNIQUE(student_id, offering_id)
        );
    """)

    # 9. grade component scores
    cur.execute("""
        CREATE TABLE IF NOT EXISTS grade_component_scores (
            score_id SERIAL PRIMARY KEY,
            enrollment_id INTEGER NOT NULL REFERENCES enrollments(enrollment_id) ON DELETE CASCADE,
            component_id INTEGER NOT NULL REFERENCES grade_components(component_id) ON DELETE CASCADE,
            score NUMERIC(6, 2) NOT NULL,
            remarks TEXT,
            date_recorded DATE NOT NULL DEFAULT CURRENT_DATE,
            UNIQUE(enrollment_id, component_id)
        );
    """)

    # 10. computed final grades
    cur.execute("""
        CREATE TABLE IF NOT EXISTS grades (
            grade_id SERIAL PRIMARY KEY,
            enrollment_id INTEGER NOT NULL UNIQUE REFERENCES enrollments(enrollment_id) ON DELETE CASCADE,
            midterm_grade NUMERIC(5, 2),
            finals_grade NUMERIC(5, 2),
            final_grade NUMERIC(5, 2) NOT NULL,
            remarks VARCHAR(50),
            date_encoded DATE DEFAULT CURRENT_DATE
        );
    """)

    conn.commit()
    cur.close()
    conn.close()


if __name__ == "__main__":
    init_db()
    print("PostgreSQL database initialized successfully.")