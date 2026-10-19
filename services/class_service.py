from repositories import ClassRepository, SubjectRepository, TeacherRepository
from repositories import EnrollmentRepository, GradePercentageRepository
from services.validation import required


class ClassService:
    def __init__(self):
        self.repo = ClassRepository()
        self.subjects = SubjectRepository()
        self.teachers = TeacherRepository()
        self.enrollments = EnrollmentRepository()
        self.weights = GradePercentageRepository()

    def find_all(self):
        return self.repo.find_all()

    def find_by_id(self, class_id):
        return self.repo.find_by_id(class_id)

    def save(self, offering):
        offering.class_code = required(offering.class_code, "Class code")
        offering.subject_id = required(offering.subject_id, "Subject")
        offering.teacher_id = required(offering.teacher_id, "Teacher")
        offering.school_year = required(offering.school_year, "School year")
        offering.semester = required(offering.semester, "Semester")
        offering.section = required(offering.section, "Section")
        if not self.subjects.find_by_id(offering.subject_id):
            raise ValueError("The selected subject does not exist.")
        if not self.teachers.find_by_id(offering.teacher_id):
            raise ValueError("The selected teacher does not exist.")
        if offering.class_id and not self.repo.find_by_id(offering.class_id):
            raise ValueError("Class not found. Refresh the list.")
        for existing in self.repo.find_all():
            if existing.class_code == offering.class_code and existing.class_id != offering.class_id:
                raise ValueError("That class code already exists.")
        return self.repo.save(offering)

    def delete(self, class_id):
        if not self.repo.find_by_id(class_id):
            raise ValueError("Class not found. Refresh the list.")
        if self.enrollments.find_by_offering(class_id):
            raise ValueError("Cannot delete this class because enrollments depend on it.")
        if self.weights.find_by_offering(class_id):
            raise ValueError("Cannot delete this class because grading weights depend on it.")
        return self.repo.delete_by_id(class_id)
