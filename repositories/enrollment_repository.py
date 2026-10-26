# enrollment_repository.py - repository for class enrollments using PostgreSQL

from db import get_connection
from models import Enrollment


class EnrollmentRepository:
    def _row_to_enrollment(self, row, detailed=False):
        e = Enrollment(
            enrollment_id=str(row[0]),
            student_id=str(row[1]),
            class_id=str(row[2]),
            enroll_date=row[3],
            status=row[4]
        )
        if detailed and len(row) >= 10:
            e.student_name = row[5]
            e.student_email = row[6]
            e.student_program = row[7]
            e.class_code = row[8]
            e.subject_name = row[9]
        return e

    def find_by_id(self, enrollment_id):
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT e.enrollment_id, e.student_id, e.class_id, e.enroll_date, e.status, "
                "(s.last_name || ', ' || s.first_name) AS student_name, s.email, s.program, "
                "co.class_code, sub.subject_name "
                "FROM enrollments e "
                "JOIN students s ON e.student_id = s.student_id "
                "JOIN class_offerings co ON e.class_id = co.class_id "
                "JOIN subjects sub ON co.subject_id = sub.subject_id "
                "WHERE e.enrollment_id = %s",
                (enrollment_id,)
            )
            row = cur.fetchone()
            cur.close()
            return self._row_to_enrollment(row, detailed=True) if row else None
        finally:
            conn.close()

    def find_all(self):
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT e.enrollment_id, e.student_id, e.class_id, e.enroll_date, e.status, "
                "(s.last_name || ', ' || s.first_name) AS student_name, s.email, s.program, "
                "co.class_code, sub.subject_name "
                "FROM enrollments e "
                "JOIN students s ON e.student_id = s.student_id "
                "JOIN class_offerings co ON e.class_id = co.class_id "
                "JOIN subjects sub ON co.subject_id = sub.subject_id "
                "ORDER BY co.class_code, s.last_name, s.first_name"
            )
            rows = cur.fetchall()
            cur.close()
            return [self._row_to_enrollment(r, detailed=True) for r in rows]
        finally:
            conn.close()

    def find_by_offering(self, class_id):
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT e.enrollment_id, e.student_id, e.class_id, e.enroll_date, e.status, "
                "(s.last_name || ', ' || s.first_name) AS student_name, s.email, s.program, "
                "co.class_code, sub.subject_name "
                "FROM enrollments e "
                "JOIN students s ON e.student_id = s.student_id "
                "JOIN class_offerings co ON e.class_id = co.class_id "
                "JOIN subjects sub ON co.subject_id = sub.subject_id "
                "WHERE e.class_id = %s "
                "ORDER BY s.last_name, s.first_name",
                (class_id,)
            )
            rows = cur.fetchall()
            cur.close()
            return [self._row_to_enrollment(r, detailed=True) for r in rows]
        finally:
            conn.close()

    def find_by_student(self, student_id):
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT e.enrollment_id, e.student_id, e.class_id, e.enroll_date, e.status, "
                "(s.last_name || ', ' || s.first_name) AS student_name, s.email, s.program, "
                "co.class_code, sub.subject_name "
                "FROM enrollments e "
                "JOIN students s ON e.student_id = s.student_id "
                "JOIN class_offerings co ON e.class_id = co.class_id "
                "JOIN subjects sub ON co.subject_id = sub.subject_id "
                "WHERE e.student_id = %s "
                "ORDER BY co.school_year DESC, co.semester, co.class_code",
                (student_id,)
            )
            rows = cur.fetchall()
            cur.close()
            return [self._row_to_enrollment(r, detailed=True) for r in rows]
        finally:
            conn.close()

    def find_by_student_and_offering(self, student_id, class_id):
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT e.enrollment_id, e.student_id, e.class_id, e.enroll_date, e.status "
                "FROM enrollments e WHERE e.student_id = %s AND e.class_id = %s",
                (student_id, class_id)
            )
            row = cur.fetchone()
            cur.close()
            return self._row_to_enrollment(row) if row else None
        finally:
            conn.close()

    def save(self, enrollment):
        conn = get_connection()
        try:
            cur = conn.cursor()
            if enrollment.enrollment_id:
                cur.execute(
                    "UPDATE enrollments SET student_id=%s, class_id=%s, "
                    "enroll_date=COALESCE(%s, CURRENT_DATE), status=%s "
                    "WHERE enrollment_id=%s RETURNING enrollment_id",
                    (enrollment.student_id, enrollment.class_id,
                     enrollment.enroll_date, enrollment.status, enrollment.enrollment_id)
                )
                eid = cur.fetchone()[0]
            else:
                cur.execute(
                    "INSERT INTO enrollments (student_id, class_id, enroll_date, status) "
                    "VALUES (%s, %s, COALESCE(%s, CURRENT_DATE), %s) RETURNING enrollment_id",
                    (enrollment.student_id, enrollment.class_id,
                     enrollment.enroll_date, enrollment.status)
                )
                eid = cur.fetchone()[0]
            conn.commit()
            cur.close()
            enrollment.enrollment_id = str(eid)
            return enrollment
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def delete_by_id(self, enrollment_id):
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM enrollments WHERE enrollment_id = %s", (enrollment_id,))
            affected = cur.rowcount
            conn.commit()
            cur.close()
            return affected > 0
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
