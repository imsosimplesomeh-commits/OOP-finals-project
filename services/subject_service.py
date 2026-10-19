from repositories import SubjectRepository, ClassRepository
from services.validation import required, positive_integer


class SubjectService:
    def __init__(self):
        self.repo = SubjectRepository()
        self.classes = ClassRepository()

    def find_all(self):
        return self.repo.find_all()

    def find_by_id(self, subject_id):
        return self.repo.find_by_id(subject_id)

    def save(self, subject):
        subject.subject_code = required(subject.subject_code, "Subject code")
        subject.subject_name = required(subject.subject_name, "Subject name")
        subject.units = positive_integer(subject.units, "Units")
        if subject.subject_id and not self.repo.find_by_id(subject.subject_id):
            raise ValueError("Subject not found. Refresh the list.")
        for existing in self.repo.find_all():
            if existing.subject_code == subject.subject_code and existing.subject_id != subject.subject_id:
                raise ValueError("That subject code already exists.")
        return self.repo.save(subject)

    def delete(self, subject_id):
        if not self.repo.find_by_id(subject_id):
            raise ValueError("Subject not found. Refresh the list.")
        for offering in self.classes.find_all():
            if offering.subject_id == str(subject_id):
                raise ValueError(f"Cannot delete this subject because class {offering.class_code} depends on it.")
        return self.repo.delete_by_id(subject_id)
