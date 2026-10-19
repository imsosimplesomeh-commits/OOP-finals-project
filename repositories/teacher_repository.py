# teacher_repository.py - repository for teacher database operations using PostgreSQL

from db import get_connection
from models import Teacher
from repositories.base_repository import Repository


class TeacherRepository(Repository):
    def _row_to_teacher(self, row):
        return Teacher(
            teacher_id=str(row[0]),
            first_name=row[1],
            last_name=row[2],
            email=row[3],
            department=row[4],
            status=row[5]
        )

    def find_by_id(self, teacher_id):
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT teacher_id, first_name, last_name, email, department, status "
                "FROM teachers WHERE teacher_id = %s",
                (teacher_id,)
            )
            row = cur.fetchone()
            cur.close()
            return self._row_to_teacher(row) if row else None
        finally:
            conn.close()

    def find_all(self):
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT teacher_id, first_name, last_name, email, department, status "
                "FROM teachers ORDER BY last_name, first_name"
            )
            rows = cur.fetchall()
            cur.close()
            return [self._row_to_teacher(r) for r in rows]
        finally:
            conn.close()

    def search(self, query):
        pattern = f"%{query.strip()}%"
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT teacher_id, first_name, last_name, email, department, status "
                "FROM teachers "
                "WHERE first_name ILIKE %s OR last_name ILIKE %s OR email ILIKE %s OR department ILIKE %s "
                "ORDER BY last_name, first_name",
                (pattern, pattern, pattern, pattern)
            )
            rows = cur.fetchall()
            cur.close()
            return [self._row_to_teacher(r) for r in rows]
        finally:
            conn.close()

    def save(self, teacher):
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT teacher_id FROM teachers WHERE teacher_id = %s", (teacher.teacher_id,))
            if cur.fetchone():
                cur.execute(
                    "UPDATE teachers SET first_name=%s, last_name=%s, email=%s, "
                    "department=%s, status=%s WHERE teacher_id=%s RETURNING teacher_id",
                    (teacher.first_name, teacher.last_name, teacher.email or None,
                     teacher.department, teacher.status, teacher.teacher_id)
                )
                tid = cur.fetchone()[0]
            else:
                cur.execute(
                    "INSERT INTO teachers (teacher_id, first_name, last_name, email, department, status) "
                    "VALUES (%s, %s, %s, %s, %s, %s) RETURNING teacher_id",
                    (teacher.teacher_id, teacher.first_name, teacher.last_name, teacher.email or None,
                     teacher.department, teacher.status)
                )
                tid = cur.fetchone()[0]
            conn.commit()
            cur.close()
            teacher.teacher_id = str(tid)
            return teacher
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def delete_by_id(self, teacher_id):
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM teachers WHERE teacher_id = %s", (teacher_id,))
            affected = cur.rowcount
            conn.commit()
            cur.close()
            return affected > 0
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
