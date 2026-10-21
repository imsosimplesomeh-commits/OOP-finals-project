# grading_period_repository.py - repository for grading periods using PostgreSQL

from db import get_connection
from models import GradingPeriod
from repositories.base_repository import Repository


class GradingPeriodRepository(Repository):
    def _row_to_period(self, row):
        return GradingPeriod(
            period_id=str(row[0]),
            name=row[1],
            start_date=row[2],
            end_date=row[3],
            school_year=row[4],
            semester=row[5],
            period_order=row[6]
        )

    def find_by_id(self, period_id):
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT period_id, name, start_date, end_date, school_year, semester, period_order "
                "FROM grading_periods WHERE period_id = %s",
                (period_id,)
            )
            row = cur.fetchone()
            cur.close()
            return self._row_to_period(row) if row else None
        finally:
            conn.close()

    def find_all(self):
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT period_id, name, start_date, end_date, school_year, semester, period_order "
                "FROM grading_periods ORDER BY period_order, period_id"
            )
            rows = cur.fetchall()
            cur.close()
            return [self._row_to_period(r) for r in rows]
        finally:
            conn.close()

    def save(self, period):
        conn = get_connection()
        try:
            cur = conn.cursor()
            if period.period_id:
                cur.execute(
                    "UPDATE grading_periods SET name=%s, start_date=%s, end_date=%s, "
                    "school_year=%s, semester=%s, period_order=%s WHERE period_id=%s RETURNING period_id",
                    (period.name, period.start_date, period.end_date,
                     period.school_year, period.semester, period.period_order, period.period_id)
                )
                pid = cur.fetchone()[0]
            else:
                cur.execute(
                    "INSERT INTO grading_periods (name, start_date, end_date, school_year, semester, period_order) "
                    "VALUES (%s, %s, %s, %s, %s, %s) RETURNING period_id",
                    (period.name, period.start_date, period.end_date,
                     period.school_year, period.semester, period.period_order)
                )
                pid = cur.fetchone()[0]
            conn.commit()
            cur.close()
            period.period_id = str(pid)
            return period
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def delete_by_id(self, period_id):
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM grading_periods WHERE period_id = %s", (period_id,))
            affected = cur.rowcount
            conn.commit()
            cur.close()
            return affected > 0
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
