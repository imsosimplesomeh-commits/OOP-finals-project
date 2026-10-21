# enrollment_service.py - handles enrollment logic and validations

from datetime import date
from repositories import ScoreRepository, GradeRepository
from services.validation import required
from models import Enrollment
from repositories.class_repository import ClassRepository
from repositories.enrollment_repository import EnrollmentRepository
from repositories.student_repository import StudentRepository


class EnrollmentService:
    def __init__(self):
        self.enrollment_repo = EnrollmentRepository()
        self.student_repo = StudentRepository()
        self.class_repo = ClassRepository()
        self.scores = ScoreRepository()
        self.grades = GradeRepository()

    def enroll_student(self, student_id, offering_id, enroll_date=None):
        if not student_id or not str(student_id).strip():
            return False, "Student number is required.", None
        student_id = str(student_id).strip()
        if not offering_id:
            return False, "Select a class first.", None
        # validate student and class exist
        student = self.student_repo.find_by_id(student_id)
        if not student:
            return False, f"Student with ID '{student_id}' does not exist.", None

        offering = self.class_repo.find_by_id(offering_id)
        if not offering:
            return False, f"Class offering with ID '{offering_id}' does not exist.", None

        # prevent duplicate enrollment
        existing = self.enrollment_repo.find_by_student_and_offering(student_id, offering_id)
        if existing:
            return False, f"Student '{student.full_name}' is already enrolled in {offering.class_code}.", None

        if enroll_date is not None and not isinstance(enroll_date, date):
            try:
                enroll_date = date.fromisoformat(str(enroll_date))
            except ValueError:
                return False, "Use an enrollment date in YYYY-MM-DD format.", None
        enrollment = Enrollment(
            student_id=student_id,
            class_id=offering_id,
            enroll_date=enroll_date or date.today(),
            status="Enrolled"
        )
        saved = self.enrollment_repo.save(enrollment)
        return True, f"Successfully enrolled {student.full_name}.", saved

    def get_class_enrollments(self, offering_id):
        return self.enrollment_repo.find_by_offering(offering_id)

    def update_status(self, enrollment_id, new_status):
        en = self.enrollment_repo.find_by_id(enrollment_id)
        if not en:
            raise ValueError("Enrollment not found. Refresh the list.")
        new_status = required(new_status, "Enrollment status").capitalize()
        if new_status not in ("Enrolled", "Dropped"):
            raise ValueError("Status must be Enrolled or Dropped.")
        en.status = new_status
        self.enrollment_repo.save(en)
        return True

    def remove_enrollment(self, enrollment_id):
        if not self.enrollment_repo.find_by_id(enrollment_id):
            raise ValueError("Enrollment not found. Refresh the list.")
        if self.scores.find_by_enrollment(enrollment_id):
            raise ValueError("Cannot remove this enrollment because scores depend on it.")
        if self.grades.find_by_enrollment(enrollment_id):
            raise ValueError("Cannot remove this enrollment because a saved grade depends on it.")
        return self.enrollment_repo.delete_by_id(enrollment_id)
