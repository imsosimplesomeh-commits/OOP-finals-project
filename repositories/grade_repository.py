# grade_repository.py - repository for computed period and final grades using PostgreSQL

from db import get_connection
from models import Grade
from repositories.base_repository import Repository


class GradeRepository(Repository):
    def __init__(self, conn_func=get_connection):
        self.conn_func = conn_func

    def _row_to_grade(self, row):
        return Grade(
            grade_id=str(row[0]),
            enrollment_id=str(row[1]),
            midterm_grade=float(row[2]) if row[2] is not None else None,
            finals_grade=float(row[3]) if row[3] is not None else None,
            overall_grade=float(row[4]) if row[4] is not None else None,
            remarks=row[5],
            date_encoded=row[6],
            midterm_equiv=float(row[7]) if row[7] is not None else None,
            final_equiv=float(row[8]) if row[8] is not None else None
        )

    def find_by_id(self, grade_id):
        conn = self.conn_func()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT grade_id, enrollment_id, midterm_grade, finals_grade, overall_grade, remarks, date_encoded, midterm_equiv, final_equiv "
                "FROM grades WHERE grade_id = %s",
                (grade_id,)
            )
            row = cur.fetchone()
            cur.close()
            return self._row_to_grade(row) if row else None
        finally:
            conn.close()

    def find_all(self):
        conn = self.conn_func()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT grade_id, enrollment_id, midterm_grade, finals_grade, overall_grade, remarks, date_encoded, midterm_equiv, final_equiv "
                "FROM grades ORDER BY date_encoded DESC"
            )
            rows = cur.fetchall()
            cur.close()
            return [self._row_to_grade(r) for r in rows]
        finally:
            conn.close()

    def find_by_enrollment(self, enrollment_id):
        conn = self.conn_func()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT grade_id, enrollment_id, midterm_grade, finals_grade, overall_grade, remarks, date_encoded, midterm_equiv, final_equiv "
                "FROM grades WHERE enrollment_id = %s",
                (enrollment_id,)
            )
            row = cur.fetchone()
            cur.close()
            return self._row_to_grade(row) if row else None
        finally:
            conn.close()

    def find_by_offering(self, offering_id):
        conn = self.conn_func()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT g.grade_id, g.enrollment_id, g.midterm_grade, g.finals_grade, g.overall_grade, g.remarks, g.date_encoded, g.midterm_equiv, g.final_equiv "
                "FROM grades g "
                "JOIN enrollments e ON g.enrollment_id = e.enrollment_id "
                "WHERE e.class_id = %s",
                (offering_id,)
            )
            rows = cur.fetchall()
            cur.close()
            return [self._row_to_grade(r) for r in rows]
        finally:
            conn.close()

    def save(self, grade):
        # upsert grade by unique enrollment_id in PostgreSQL
        conn = self.conn_func()
        try:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO grades (enrollment_id, midterm_grade, finals_grade, overall_grade, remarks, date_encoded, midterm_equiv, final_equiv) "
                "VALUES (%s, %s, %s, %s, %s, COALESCE(%s, CURRENT_DATE), %s, %s) "
                "ON CONFLICT (enrollment_id) DO UPDATE SET "
                "midterm_grade = EXCLUDED.midterm_grade, "
                "finals_grade = EXCLUDED.finals_grade, "
                "overall_grade = EXCLUDED.overall_grade, "
                "midterm_equiv = EXCLUDED.midterm_equiv, "
                "final_equiv = EXCLUDED.final_equiv, "
                "remarks = EXCLUDED.remarks, "
                "date_encoded = EXCLUDED.date_encoded "
                "RETURNING grade_id",
                (grade.enrollment_id, grade.midterm_grade, grade.finals_grade,
                 grade.overall_grade, grade.remarks, grade.date_encoded,
                 grade.midterm_equiv, grade.final_equiv)
            )
            gid = cur.fetchone()[0]
            conn.commit()
            cur.close()
            grade.grade_id = str(gid)
            return grade
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def delete_by_id(self, grade_id):
        conn = self.conn_func()
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM grades WHERE grade_id = %s", (grade_id,))
            affected = cur.rowcount
            conn.commit()
            cur.close()
            return affected > 0
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
