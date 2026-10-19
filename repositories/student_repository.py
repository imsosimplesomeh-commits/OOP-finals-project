# student_repository.py - repository for student database operations using PostgreSQL

from db import get_connection
from models import Student
from repositories.base_repository import Repository


class StudentRepository(Repository):
    def _row_to_student(self, row):
        return Student(
            student_id=str(row[0]),
            first_name=row[1],
            last_name=row[2],
            email=row[3],
            program=row[4],
            year_level=row[5],
            status=row[6]
        )

    def find_by_id(self, student_id):
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT student_id, first_name, last_name, email, program, year_level, status "
                "FROM students WHERE student_id = %s",
                (student_id,)
            )
            row = cur.fetchone()
            cur.close()
            return self._row_to_student(row) if row else None
        finally:
            conn.close()

    def find_all(self):
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT student_id, first_name, last_name, email, program, year_level, status "
                "FROM students ORDER BY last_name, first_name"
            )
            rows = cur.fetchall()
            cur.close()
            return [self._row_to_student(r) for r in rows]
        finally:
            conn.close()

    def search(self, query):
        pattern = f"%{query.strip()}%"
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT student_id, first_name, last_name, email, program, year_level, status "
                "FROM students "
                "WHERE first_name ILIKE %s OR last_name ILIKE %s OR email ILIKE %s OR program ILIKE %s "
                "ORDER BY last_name, first_name",
                (pattern, pattern, pattern, pattern)
            )
            rows = cur.fetchall()
            cur.close()
            return [self._row_to_student(r) for r in rows]
        finally:
            conn.close()

    def save(self, student):
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT student_id FROM students WHERE student_id = %s", (student.student_id,))
            if cur.fetchone():
                cur.execute(
                    "UPDATE students SET first_name=%s, last_name=%s, email=%s, "
                    "program=%s, year_level=%s, status=%s "
                    "WHERE student_id=%s RETURNING student_id",
                    (student.first_name, student.last_name, student.email or None,
                     student.program, student.year_level, student.status, student.student_id)
                )
                sid = cur.fetchone()[0]
            else:
                cur.execute(
                    "INSERT INTO students (student_id, first_name, last_name, email, program, year_level, status) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING student_id",
                    (student.student_id, student.first_name, student.last_name, student.email or None,
                     student.program, student.year_level, student.status)
                )
                sid = cur.fetchone()[0]
            conn.commit()
            cur.close()
            student.student_id = str(sid)
            return student
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def delete_by_id(self, student_id):
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM students WHERE student_id = %s", (student_id,))
            affected = cur.rowcount
            conn.commit()
            cur.close()
            return affected > 0
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
