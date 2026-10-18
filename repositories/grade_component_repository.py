# grade_component_repository.py - repository for assessable components using PostgreSQL

from db import get_connection
from models import GradeComponent
from repositories.base_repository import Repository


class GradeComponentRepository(Repository):
    def __init__(self, conn_func=get_connection):
        self.conn_func = conn_func

    def _row_to_component(self, row, detailed=False):
        gc = GradeComponent(
            component_id=str(row[0]),
            period_id=str(row[1]),
            name=row[2],
            type=row[3],
            max_score=float(row[4]),
            description=row[5]
        )
        if detailed and len(row) >= 7:
            gc.period_name = row[6]
            if len(row) >= 8:
                gc.percentage_value = float(row[7]) if row[7] is not None else None
        return gc

    def find_by_id(self, component_id):
        conn = self.conn_func()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT gc.component_id, gc.period_id, "
                "gc.name, gc.type, gc.max_score, gc.description, "
                "gp.name AS period_name "
                "FROM grade_components gc "
                "JOIN grading_periods gp ON gc.period_id = gp.period_id "
                "WHERE gc.component_id = %s",
                (component_id,)
            )
            row = cur.fetchone()
            cur.close()
            return self._row_to_component(row, detailed=True) if row else None
        finally:
            conn.close()

    def find_all(self):
        conn = self.conn_func()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT gc.component_id, gc.period_id, "
                "gc.name, gc.type, gc.max_score, gc.description, "
                "gp.name AS period_name "
                "FROM grade_components gc "
                "JOIN grading_periods gp ON gc.period_id = gp.period_id "
                "ORDER BY gp.period_order, gc.component_id"
            )
            rows = cur.fetchall()
            cur.close()
            return [self._row_to_component(r, detailed=True) for r in rows]
        finally:
            conn.close()

    def find_by_offering(self, offering_id):
        conn = self.conn_func()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT gc.component_id, gc.period_id, "
                "gc.name, gc.type, gc.max_score, gc.description, "
                "gp.name AS period_name, gp_perc.percentage "
                "FROM grade_components gc "
                "JOIN grading_periods gp ON gc.period_id = gp.period_id "
                "JOIN grade_percentages gp_perc ON gc.component_id = gp_perc.component_id "
                "WHERE gp_perc.class_id = %s "
                "ORDER BY gp.period_order, gc.component_id",
                (offering_id,)
            )
            rows = cur.fetchall()
            cur.close()
            return [self._row_to_component(r, detailed=True) for r in rows]
        finally:
            conn.close()

    def find_by_offering_and_period(self, offering_id, period_id):
        conn = self.conn_func()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT gc.component_id, gc.period_id, "
                "gc.name, gc.type, gc.max_score, gc.description, "
                "gp.name AS period_name, gp_perc.percentage "
                "FROM grade_components gc "
                "JOIN grading_periods gp ON gc.period_id = gp.period_id "
                "JOIN grade_percentages gp_perc ON gc.component_id = gp_perc.component_id "
                "WHERE gp_perc.class_id = %s AND gc.period_id = %s "
                "ORDER BY gc.type, gc.name",
                (offering_id, period_id)
            )
            rows = cur.fetchall()
            cur.close()
            return [self._row_to_component(r, detailed=True) for r in rows]
        finally:
            conn.close()

    def save(self, component):
        conn = self.conn_func()
        try:
            cur = conn.cursor()
            if component.component_id:
                cur.execute(
                    "UPDATE grade_components SET period_id=%s, "
                    "name=%s, type=%s, max_score=%s, description=%s "
                    "WHERE component_id=%s RETURNING component_id",
                    (component.period_id,
                     component.name, component.type, component.max_score,
                     component.description, component.component_id)
                )
                cid = cur.fetchone()[0]
            else:
                cur.execute(
                    "INSERT INTO grade_components (period_id, name, type, max_score, description) "
                    "VALUES (%s, %s, %s, %s, %s) RETURNING component_id",
                    (component.period_id,
                     component.name, component.type, component.max_score, component.description)
                )
                cid = cur.fetchone()[0]
            conn.commit()
            cur.close()
            component.component_id = str(cid)
            return component
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def delete_by_id(self, component_id):
        conn = self.conn_func()
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM grade_components WHERE component_id = %s", (component_id,))
            affected = cur.rowcount
            conn.commit()
            cur.close()
            return affected > 0
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
