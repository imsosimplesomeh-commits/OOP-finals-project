# grade_repository.py - repository for computed period and final grades using PostgreSQL

from db import get_connection
from models import Grade
from repositories.base_repository import Repository
from repositories.audit_repository import AuditRepository


class GradeRepository(Repository):
    def __init__(self, conn_func=get_connection, audit_repo=None):
        self.conn_func = conn_func
        self.audit = audit_repo or AuditRepository(conn_func)

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

    def find_by_enrollment(self, enrollment_id, connection=None):
        own_connection = connection is None
        conn = self.conn_func() if own_connection else connection
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
            if own_connection:
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

    def save(self, grade, changed_by=None, connection=None):
        own_connection = connection is None
        conn = self.conn_func() if own_connection else connection
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT enrollment_id FROM enrollments WHERE enrollment_id = %s FOR UPDATE",
                            (grade.enrollment_id,))
                cur.execute("SELECT row_to_json(g) FROM grades g WHERE enrollment_id = %s FOR UPDATE",
                            (grade.enrollment_id,))
                row = cur.fetchone()
                old_value = row[0] if row else None
                cur.execute(
                    "INSERT INTO grades (enrollment_id, midterm_grade, finals_grade, overall_grade, remarks, "
                    "date_encoded, midterm_equiv, final_equiv) "
                    "VALUES (%s, %s, %s, %s, %s, COALESCE(%s, CURRENT_DATE), %s, %s) "
                    "ON CONFLICT (enrollment_id) DO UPDATE SET "
                    "midterm_grade = EXCLUDED.midterm_grade, finals_grade = EXCLUDED.finals_grade, "
                    "overall_grade = EXCLUDED.overall_grade, midterm_equiv = EXCLUDED.midterm_equiv, "
                    "final_equiv = EXCLUDED.final_equiv, remarks = EXCLUDED.remarks, "
                    "date_encoded = EXCLUDED.date_encoded RETURNING grade_id",
                    (grade.enrollment_id, grade.midterm_grade, grade.finals_grade,
                     grade.overall_grade, grade.remarks, grade.date_encoded, grade.midterm_equiv, grade.final_equiv),
                )
                grade_id = cur.fetchone()[0]
                cur.execute("SELECT row_to_json(g) FROM grades g WHERE grade_id = %s", (grade_id,))
                new_value = cur.fetchone()[0]
                self.audit.log_change(cur, "GRADE", grade_id, "UPDATE" if old_value else "INSERT",
                                      old_value, new_value, changed_by)
            if own_connection:
                conn.commit()
            grade.grade_id = str(grade_id)
            return grade
        except Exception:
            if own_connection:
                conn.rollback()
            raise
        finally:
            if own_connection:
                conn.close()

    def delete_by_id(self, grade_id, changed_by=None, connection=None):
        own_connection = connection is None
        conn = self.conn_func() if own_connection else connection
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT enrollment_id FROM grades WHERE grade_id = %s", (grade_id,))
                row = cur.fetchone()
                if row:
                    cur.execute("SELECT enrollment_id FROM enrollments WHERE enrollment_id = %s FOR UPDATE", (row[0],))
                cur.execute("SELECT row_to_json(g) FROM grades g WHERE grade_id = %s FOR UPDATE", (grade_id,))
                row = cur.fetchone()
                if row:
                    cur.execute("DELETE FROM grades WHERE grade_id = %s", (grade_id,))
                    self.audit.log_change(cur, "GRADE", grade_id, "DELETE", row[0], None, changed_by)
            if own_connection:
                conn.commit()
            return row is not None
        except Exception:
            if own_connection:
                conn.rollback()
            raise
        finally:
            if own_connection:
                conn.close()
