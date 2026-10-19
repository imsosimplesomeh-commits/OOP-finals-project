# grade_percentage_repository.py - repository for class grading weights using PostgreSQL

from db import get_connection
from models import GradePercentage
from repositories.base_repository import Repository
from repositories.audit_repository import AuditRepository


class GradePercentageRepository(Repository):
    def __init__(self):
        self.audit = AuditRepository()

    def _row_to_percentage(self, row):
        return GradePercentage(
            percentage_id=str(row[0]),
            class_id=str(row[1]),
            component_id=str(row[2]),
            percentage=float(row[3])
        )

    def find_by_id(self, percentage_id):
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT percentage_id, class_id, component_id, percentage "
                "FROM grade_percentages WHERE percentage_id = %s",
                (percentage_id,)
            )
            row = cur.fetchone()
            cur.close()
            return self._row_to_percentage(row) if row else None
        finally:
            conn.close()

    def find_all(self):
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT percentage_id, class_id, component_id, percentage "
                "FROM grade_percentages ORDER BY component_id"
            )
            rows = cur.fetchall()
            cur.close()
            return [self._row_to_percentage(r) for r in rows]
        finally:
            conn.close()

    def find_by_offering(self, class_id):
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT percentage_id, class_id, component_id, percentage "
                "FROM grade_percentages WHERE class_id = %s ORDER BY component_id",
                (class_id,)
            )
            rows = cur.fetchall()
            cur.close()
            return [self._row_to_percentage(r) for r in rows]
        finally:
            conn.close()

    def save(self, percentage, changed_by=None):
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT class_id FROM class_offerings WHERE class_id = %s FOR UPDATE", (percentage.class_id,))
                old_value = None
                if percentage.percentage_id:
                    cur.execute("SELECT row_to_json(w) FROM grade_percentages w WHERE percentage_id = %s FOR UPDATE",
                                (percentage.percentage_id,))
                    row = cur.fetchone()
                    if not row:
                        raise ValueError("Weight not found. Refresh the list.")
                    old_value = row[0]
                    cur.execute(
                        "UPDATE grade_percentages SET class_id=%s, component_id=%s, percentage=%s "
                        "WHERE percentage_id=%s RETURNING percentage_id",
                        (percentage.class_id, percentage.component_id, percentage.percentage, percentage.percentage_id),
                    )
                else:
                    cur.execute(
                        "INSERT INTO grade_percentages (class_id, component_id, percentage) "
                        "VALUES (%s, %s, %s) RETURNING percentage_id",
                        (percentage.class_id, percentage.component_id, percentage.percentage),
                    )
                percentage_id = cur.fetchone()[0]
                cur.execute("SELECT row_to_json(w) FROM grade_percentages w WHERE percentage_id = %s", (percentage_id,))
                new_value = cur.fetchone()[0]
                self.audit.log_change(cur, "GRADE_PERCENTAGE", percentage_id,
                                      "UPDATE" if old_value else "INSERT", old_value, new_value, changed_by)
            conn.commit()
            percentage.percentage_id = str(percentage_id)
            return percentage
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def save_period(self, class_id, values, changed_by=None):
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT class_id FROM class_offerings WHERE class_id = %s FOR UPDATE", (class_id,))
                for component_id, percentage in values:
                    cur.execute(
                        "SELECT row_to_json(w) FROM grade_percentages w "
                        "WHERE class_id = %s AND component_id = %s FOR UPDATE",
                        (class_id, component_id),
                    )
                    row = cur.fetchone()
                    old_value = row[0] if row else None
                    cur.execute(
                        "INSERT INTO grade_percentages (class_id, component_id, percentage) "
                        "VALUES (%s, %s, %s) ON CONFLICT (class_id, component_id) "
                        "DO UPDATE SET percentage = EXCLUDED.percentage RETURNING percentage_id",
                        (class_id, component_id, percentage),
                    )
                    percentage_id = cur.fetchone()[0]
                    cur.execute("SELECT row_to_json(w) FROM grade_percentages w WHERE percentage_id = %s", (percentage_id,))
                    new_value = cur.fetchone()[0]
                    self.audit.log_change(cur, "GRADE_PERCENTAGE", percentage_id,
                                          "UPDATE" if old_value else "INSERT", old_value, new_value, changed_by)
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def delete_by_id(self, percentage_id, changed_by=None):
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT class_id FROM grade_percentages WHERE percentage_id = %s", (percentage_id,))
                row = cur.fetchone()
                if row:
                    cur.execute("SELECT class_id FROM class_offerings WHERE class_id = %s FOR UPDATE", (row[0],))
                cur.execute("SELECT row_to_json(w) FROM grade_percentages w WHERE percentage_id = %s FOR UPDATE", (percentage_id,))
                row = cur.fetchone()
                if row:
                    cur.execute("DELETE FROM grade_percentages WHERE percentage_id = %s", (percentage_id,))
                    self.audit.log_change(cur, "GRADE_PERCENTAGE", percentage_id, "DELETE", row[0], None, changed_by)
            conn.commit()
            return row is not None
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
