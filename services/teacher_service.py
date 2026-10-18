from repositories import TeacherRepository, ClassRepository
from services.validation import required


class TeacherService:
    def __init__(self, teacher_repo=None, class_repo=None):
        self.repo = teacher_repo or TeacherRepository()
        self.classes = class_repo or ClassRepository()

    def find_all(self):
        return self.repo.find_all()

    def search(self, query):
        return self.repo.search(query)

    def find_by_id(self, teacher_id):
        return self.repo.find_by_id(teacher_id)

    def validate(self, teacher):
        teacher.teacher_id = required(teacher.teacher_id, "Teacher ID")
        teacher.first_name = required(teacher.first_name, "First name")
        teacher.last_name = required(teacher.last_name, "Last name")
        teacher.department = required(teacher.department, "Department")
        teacher.email = (teacher.email or "").strip() or None
        teacher.status = required(teacher.status, "Status").capitalize()

    def add(self, teacher):
        self.validate(teacher)
        if self.repo.find_by_id(teacher.teacher_id):
            raise ValueError("That teacher ID already exists.")
        return self.repo.save(teacher)

    def update(self, teacher, original_id):
        self.validate(teacher)
        if teacher.teacher_id != str(original_id):
            raise ValueError("The teacher ID cannot be changed.")
        if not self.repo.find_by_id(original_id):
            raise ValueError("Teacher not found. Refresh the list.")
        return self.repo.save(teacher)

    def delete(self, teacher_id):
        if not self.repo.find_by_id(teacher_id):
            raise ValueError("Teacher not found. Refresh the list.")
        for offering in self.classes.find_all():
            if offering.teacher_id == str(teacher_id):
                raise ValueError(f"Cannot delete this teacher because class {offering.class_code} depends on it.")
        return self.repo.delete_by_id(teacher_id)
