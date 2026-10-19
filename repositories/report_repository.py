from db import get_connection
from psycopg2.extras import RealDictCursor


class ReportRepository:
    def __init__(self, conn_func=get_connection):
        self.conn_func = conn_func

    def _read(self, query, params):
        conn = self.conn_func()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                return [dict(row) for row in cur.fetchall()]
        finally:
            conn.close()

    def find_class_header(self, class_id):
        rows = self._read("""
            SELECT c.class_code, c.section, c.school_year, c.semester,
                   c.schedule, c.room, s.subject_code, s.subject_name,
                   t.first_name || ' ' || t.last_name AS teacher_name, t.department
            FROM class_offerings c
            JOIN subjects s ON s.subject_id = c.subject_id
            JOIN teachers t ON t.teacher_id = c.teacher_id
            WHERE c.class_id = %s
        """, (class_id,))
        return rows[0] if rows else None

    def find_class_students(self, class_id):
        return self._read("""
            SELECT s.student_id, s.last_name || ', ' || s.first_name AS student_name,
                   s.program, g.midterm_equiv, g.final_equiv
            FROM enrollments e
            JOIN students s ON s.student_id = e.student_id
            LEFT JOIN grades g ON g.enrollment_id = e.enrollment_id
            WHERE e.class_id = %s
            ORDER BY s.last_name, s.first_name, s.student_id
        """, (class_id,))

    def find_student_subjects(self, student_id):
        return self._read("""
            SELECT s.subject_code, s.subject_name, s.units,
                   t.first_name || ' ' || t.last_name AS teacher_name,
                   g.final_equiv, c.school_year, c.semester
            FROM enrollments e
            JOIN class_offerings c ON c.class_id = e.class_id
            JOIN subjects s ON s.subject_id = c.subject_id
            JOIN teachers t ON t.teacher_id = c.teacher_id
            LEFT JOIN grades g ON g.enrollment_id = e.enrollment_id
            WHERE e.student_id = %s
            ORDER BY c.school_year DESC, c.semester DESC, s.subject_code, c.class_id
        """, (student_id,))
