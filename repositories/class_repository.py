# class_repository.py - repository for class offerings using PostgreSQL

from db import get_connection
from models import ClassOffering


class ClassRepository:
    def _row_to_offering(self, row, detailed=False):
        offering = ClassOffering(
            class_id=str(row[0]),
            class_code=row[1],
            schedule=row[2],
            section=row[3],
            school_year=row[4],
            semester=row[5],
            room=row[6],
            subject_id=str(row[7]),
            teacher_id=str(row[8])
        )
        if detailed and len(row) >= 12:
            offering.subject_code = row[9]
            offering.subject_name = row[10]
            offering.teacher_name = row[11]
        return offering

    def find_by_id(self, class_id):
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT co.class_id, co.class_code, co.schedule, co.section, "
                "co.school_year, co.semester, co.room, co.subject_id, co.teacher_id, "
                "s.subject_code, s.subject_name, (t.last_name || ', ' || t.first_name) AS teacher_name "
                "FROM class_offerings co "
                "JOIN subjects s ON co.subject_id = s.subject_id "
                "JOIN teachers t ON co.teacher_id = t.teacher_id "
                "WHERE co.class_id = %s",
                (class_id,)
            )
            row = cur.fetchone()
            cur.close()
            return self._row_to_offering(row, detailed=True) if row else None
        finally:
            conn.close()

    def find_all(self):
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT co.class_id, co.class_code, co.schedule, co.section, "
                "co.school_year, co.semester, co.room, co.subject_id, co.teacher_id, "
                "s.subject_code, s.subject_name, (t.last_name || ', ' || t.first_name) AS teacher_name "
                "FROM class_offerings co "
                "JOIN subjects s ON co.subject_id = s.subject_id "
                "JOIN teachers t ON co.teacher_id = t.teacher_id "
                "ORDER BY co.school_year DESC, co.semester, co.class_code"
            )
            rows = cur.fetchall()
            cur.close()
            return [self._row_to_offering(r, detailed=True) for r in rows]
        finally:
            conn.close()

    def save(self, offering):
        conn = get_connection()
        try:
            cur = conn.cursor()
            if offering.class_id:
                cur.execute(
                    "UPDATE class_offerings SET class_code=%s, schedule=%s, section=%s, "
                    "school_year=%s, semester=%s, room=%s, subject_id=%s, teacher_id=%s "
                    "WHERE class_id=%s RETURNING class_id",
                    (offering.class_code, offering.schedule, offering.section,
                     offering.school_year, offering.semester, offering.room,
                     offering.subject_id, offering.teacher_id, offering.class_id)
                )
                oid = cur.fetchone()[0]
            else:
                cur.execute(
                    "INSERT INTO class_offerings (class_code, schedule, section, school_year, "
                    "semester, room, subject_id, teacher_id) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING class_id",
                    (offering.class_code, offering.schedule, offering.section,
                     offering.school_year, offering.semester, offering.room,
                     offering.subject_id, offering.teacher_id)
                )
                oid = cur.fetchone()[0]
            conn.commit()
            cur.close()
            offering.class_id = str(oid)
            return offering
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def delete_by_id(self, class_id):
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM class_offerings WHERE class_id = %s", (class_id,))
            affected = cur.rowcount
            conn.commit()
            cur.close()
            return affected > 0
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
