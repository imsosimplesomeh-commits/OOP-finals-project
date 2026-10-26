# subject_repository.py - repository for subject database operations using PostgreSQL

from db import get_connection
from models import Subject


class SubjectRepository:
    def _row_to_subject(self, row):
        return Subject(
            subject_id=str(row[0]),
            subject_code=row[1],
            subject_name=row[2],
            description=row[3],
            units=int(row[4])
        )

    def find_by_id(self, subject_id):
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT subject_id, subject_code, subject_name, description, units "
                "FROM subjects WHERE subject_id = %s",
                (subject_id,)
            )
            row = cur.fetchone()
            cur.close()
            return self._row_to_subject(row) if row else None
        finally:
            conn.close()

    def find_all(self):
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT subject_id, subject_code, subject_name, description, units "
                "FROM subjects ORDER BY subject_code"
            )
            rows = cur.fetchall()
            cur.close()
            return [self._row_to_subject(r) for r in rows]
        finally:
            conn.close()

    def save(self, subject):
        conn = get_connection()
        try:
            cur = conn.cursor()
            if subject.subject_id:
                cur.execute(
                    "UPDATE subjects SET subject_code=%s, subject_name=%s, "
                    "description=%s, units=%s WHERE subject_id=%s RETURNING subject_id",
                    (subject.subject_code, subject.subject_name,
                     subject.description, subject.units, subject.subject_id)
                )
                sid = cur.fetchone()[0]
            else:
                cur.execute(
                    "INSERT INTO subjects (subject_code, subject_name, description, units) "
                    "VALUES (%s, %s, %s, %s) RETURNING subject_id",
                    (subject.subject_code, subject.subject_name,
                     subject.description, subject.units)
                )
                sid = cur.fetchone()[0]
            conn.commit()
            cur.close()
            subject.subject_id = str(sid)
            return subject
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def delete_by_id(self, subject_id):
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM subjects WHERE subject_id = %s", (subject_id,))
            affected = cur.rowcount
            conn.commit()
            cur.close()
            return affected > 0
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
