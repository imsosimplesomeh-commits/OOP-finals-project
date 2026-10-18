from repositories import StudentRepository, EnrollmentRepository
from services.validation import required, positive_integer


class StudentService:
    def __init__(self, student_repo=None, enrollment_repo=None):
        self.repo = student_repo or StudentRepository()
        self.enrollments = enrollment_repo or EnrollmentRepository()

    def find_all(self):
        return self.repo.find_all()

    def search(self, query):
        return self.repo.search(query)

    def find_by_id(self, student_id):
        return self.repo.find_by_id(student_id)

    def validate(self, student):
        student.student_id = required(student.student_id, "Student number")
        student.first_name = required(student.first_name, "First name")
        student.last_name = required(student.last_name, "Last name")
        student.program = required(student.program, "Program")
        student.year_level = positive_integer(student.year_level, "Year level")
        student.email = (student.email or "").strip() or None
        student.status = required(student.status, "Status").capitalize()

    def add(self, student):
        self.validate(student)
        if self.repo.find_by_id(student.student_id):
            raise ValueError("That student number already exists.")
        return self.repo.save(student)

    def update(self, student, original_id):
        self.validate(student)
        if student.student_id != str(original_id):
            raise ValueError("The student number cannot be changed.")
        if not self.repo.find_by_id(original_id):
            raise ValueError("Student not found. Refresh the list.")
        return self.repo.save(student)

    def delete(self, student_id):
        if not self.repo.find_by_id(student_id):
            raise ValueError("Student not found. Refresh the list.")
        if self.enrollments.find_by_student(student_id):
            raise ValueError("Cannot delete this student because enrollments depend on it.")
        return self.repo.delete_by_id(student_id)
