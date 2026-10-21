# score_repository.py - repository for student component scores using PostgreSQL

from db import get_connection
from models import GradeComponentScore
from repositories.base_repository import Repository
from repositories.audit_repository import AuditRepository


class ScoreRepository(Repository):
    def __init__(self):
        self.audit = AuditRepository()

    def _row_to_score(self, row, detailed=False):
        s = GradeComponentScore(
            score_id=str(row[0]),
            enrollment_id=str(row[1]),
            component_id=str(row[2]),
            score=float(row[3]),
            remarks=row[4],
            date_recorded=row[5]
        )
        if detailed and len(row) >= 9:
            s.component_name = row[6]
            s.max_score = float(row[7]) if row[7] is not None else None
            s.component_type = row[8]
        return s

    def find_by_id(self, score_id):
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT s.score_id, s.enrollment_id, s.component_id, s.score, s.remarks, "
                "s.date_recorded, gc.name, gc.max_score, gc.type "
                "FROM grade_component_scores s "
                "JOIN grade_components gc ON s.component_id = gc.component_id "
                "WHERE s.score_id = %s",
                (score_id,)
            )
            row = cur.fetchone()
            cur.close()
            return self._row_to_score(row, detailed=True) if row else None
        finally:
            conn.close()

    def find_all(self):
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT s.score_id, s.enrollment_id, s.component_id, s.score, s.remarks, "
                "s.date_recorded, gc.name, gc.max_score, gc.type "
                "FROM grade_component_scores s "
                "JOIN grade_components gc ON s.component_id = gc.component_id "
                "ORDER BY s.date_recorded DESC"
            )
            rows = cur.fetchall()
            cur.close()
            return [self._row_to_score(r, detailed=True) for r in rows]
        finally:
            conn.close()

    def find_by_enrollment(self, enrollment_id, connection=None):
        own_connection = connection is None
        conn = get_connection() if own_connection else connection
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT s.score_id, s.enrollment_id, s.component_id, s.score, s.remarks, "
                "s.date_recorded, gc.name, gc.max_score, gc.type "
                "FROM grade_component_scores s "
                "JOIN grade_components gc ON s.component_id = gc.component_id "
                "WHERE s.enrollment_id = %s "
                "ORDER BY gc.type, gc.name",
                (enrollment_id,)
            )
            rows = cur.fetchall()
            cur.close()
            return [self._row_to_score(r, detailed=True) for r in rows]
        finally:
            if own_connection:
                conn.close()

    def save(self, score, changed_by=None, connection=None):
        own_connection = connection is None
        conn = get_connection() if own_connection else connection
        try:
            with conn.cursor() as cur:
                # the parent lock also protects the first score insert
                cur.execute("SELECT enrollment_id FROM enrollments WHERE enrollment_id = %s FOR UPDATE",
                            (score.enrollment_id,))
                cur.execute(
                    "SELECT row_to_json(s) FROM grade_component_scores s "
                    "WHERE enrollment_id = %s AND component_id = %s FOR UPDATE",
                    (score.enrollment_id, score.component_id),
                )
                row = cur.fetchone()
                old_value = row[0] if row else None
                cur.execute(
                    "INSERT INTO grade_component_scores (enrollment_id, component_id, score, remarks, date_recorded) "
                    "VALUES (%s, %s, %s, %s, COALESCE(%s, CURRENT_DATE)) "
                    "ON CONFLICT (enrollment_id, component_id) DO UPDATE SET "
                    "score = EXCLUDED.score, remarks = EXCLUDED.remarks, date_recorded = EXCLUDED.date_recorded "
                    "RETURNING score_id",
                    (score.enrollment_id, score.component_id, score.score, score.remarks, score.date_recorded),
                )
                score_id = cur.fetchone()[0]
                cur.execute("SELECT row_to_json(s) FROM grade_component_scores s WHERE score_id = %s", (score_id,))
                new_value = cur.fetchone()[0]
                self.audit.log_change(cur, "GRADE_COMPONENT_SCORE", score_id,
                                      "UPDATE" if old_value else "INSERT", old_value, new_value, changed_by)
            if own_connection:
                conn.commit()
            score.score_id = str(score_id)
            return score
        except Exception:
            if own_connection:
                conn.rollback()
            raise
        finally:
            if own_connection:
                conn.close()

    def delete_by_id(self, score_id, changed_by=None, connection=None):
        own_connection = connection is None
        conn = get_connection() if own_connection else connection
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT enrollment_id FROM grade_component_scores WHERE score_id = %s", (score_id,))
                row = cur.fetchone()
                if row:
                    cur.execute("SELECT enrollment_id FROM enrollments WHERE enrollment_id = %s FOR UPDATE", (row[0],))
                cur.execute("SELECT row_to_json(s) FROM grade_component_scores s WHERE score_id = %s FOR UPDATE", (score_id,))
                row = cur.fetchone()
                if row:
                    cur.execute("DELETE FROM grade_component_scores WHERE score_id = %s", (score_id,))
                    self.audit.log_change(cur, "GRADE_COMPONENT_SCORE", score_id, "DELETE", row[0], None, changed_by)
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
