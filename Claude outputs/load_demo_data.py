# load_demo_data.py - fills the demo database with the finished data of the 52-case test run
# Usage:  python load_demo_data.py
# WARNING: it empties the database first, then adds the records through the same services the app uses.
# After it runs, open the app and the teacher can try the functions without typing the data in.

from db import init_db, reset_database, DB_CONFIG
from models import Student, Teacher, Subject, ClassOffering, GradeComponent, GradeComponentScore
from services.student_service import StudentService
from services.teacher_service import TeacherService
from services.subject_service import SubjectService
from services.class_service import ClassService
from services.enrollment_service import EnrollmentService
from services.configuration_service import ConfigurationService
from services.score_service import ScoreService
from services.grading_service import GradingService

SCHOOL_YEAR = "2026-2027"
SEMESTER = "1st"

students = StudentService()
teachers = TeacherService()
subjects = SubjectService()
classes = ClassService()
enrollments = EnrollmentService()
config = ConfigurationService()
scores = ScoreService()
grading = GradingService()


def add_students():
    people = [("2026-0001", "Juan", "Dela Cruz", "BSCS", 2),
              ("2026-0002", "Pedro", "Reyes", "BSCS", 2),
              ("2026-0003", "Ana", "Garcia", "BSCS", 2),
              ("2026-0004", "Kevin", "O'Brien", "BSIT", 1),
              ("2026-0098", "Carlo", "Mendoza", "BSIT", 1)]
    for student_id, first, last, program, year in people:
        students.add(Student(student_id=student_id, first_name=first, last_name=last,
                             program=program, year_level=year))


def add_teachers_and_subjects():
    teachers.add(Teacher(teacher_id="T-1001", first_name="Maria", last_name="Santos",
                         department="Information Technology Department"))
    teachers.add(Teacher(teacher_id="T-1002", first_name="Jose", last_name="Ramos",
                         department="Physical Education Department"))
    subjects.save(Subject(subject_code="CSPC 103", subject_name="Object Oriented Programming", units=3,
                          description="Object-oriented analysis, design and programming in Java"))
    subjects.save(Subject(subject_code="PATHFIT 3", subject_name="Physical Activity Towards Health and Fitness 3",
                          units=2))


def add_classes():
    classes.save(ClassOffering(class_code="CSPC103-A", subject_id="1", teacher_id="T-1001", section="A",
                               school_year=SCHOOL_YEAR, semester=SEMESTER,
                               schedule="TTh 1:00-2:30", room="CS-202"))
    classes.save(ClassOffering(class_code="PATHFIT3-A", subject_id="2", teacher_id="T-1002", section="A",
                               school_year=SCHOOL_YEAR, semester=SEMESTER,
                               schedule="TTh 3:00-5:00", room="Gym"))


def enroll_students():
    for student_id in ("2026-0001", "2026-0002", "2026-0003"):
        enrollments.enroll_student(student_id, "1")
    enrollments.enroll_student("2026-0001", "2")


def add_grading_setup():
    # returns the component ids in order: 3 midterm ones, then 3 finals ones
    midterm = config.add_period("Midterm", 1, SCHOOL_YEAR, SEMESTER)
    finals = config.add_period("Finals", 2, SCHOOL_YEAR, SEMESTER)
    parts = [("Midterm Quiz", "Quiz", 50, midterm), ("Midterm Laboratory/Project", "Laboratory", 100, midterm),
             ("Midterm Examination", "Exam", 100, midterm), ("Final Quiz", "Quiz", 50, finals),
             ("Final Laboratory/Project", "Laboratory", 100, finals), ("Final Examination", "Exam", 100, finals)]
    ids = []
    for name, kind, max_score, period in parts:
        component = config.add_component(GradeComponent(period_id=period.period_id, name=name,
                                                        type=kind, max_score=max_score))
        ids.append(component.component_id)
    # CSPC103-A uses Midterm 30/30/40 and Finals 20/30/50, PATHFIT3-A uses 20/30/50 for both
    config.save_weights("1", midterm.period_id, list(zip(ids[:3], [30, 30, 40])), changed_by="demo")
    config.save_weights("1", finals.period_id, list(zip(ids[3:], [20, 30, 50])), changed_by="demo")
    config.save_weights("2", midterm.period_id, list(zip(ids[:3], [20, 30, 50])), changed_by="demo")
    config.save_weights("2", finals.period_id, list(zip(ids[3:], [20, 30, 50])), changed_by="demo")
    return ids


def add_scores(component_ids):
    raw_scores = {("2026-0001", "1"): [40, 90, 75, 45, 85, 80],
                  ("2026-0002", "1"): [20, 60, 55, 30, 70, 65],
                  ("2026-0003", "1"): [50, 100, 100, 48, 95, 92],
                  ("2026-0001", "2"): [45, 90, 90, 45, 90, 90]}
    for (student_id, class_id), values in raw_scores.items():
        enrollment = [e for e in enrollments.get_class_enrollments(class_id) if e.student_id == student_id][0]
        for component_id, value in zip(component_ids, values):
            scores.save(GradeComponentScore(enrollment_id=enrollment.enrollment_id,
                                            component_id=component_id, score=value), changed_by="demo")


if __name__ == "__main__":
    print("Loading demo data into", DB_CONFIG["dbname"], "...")
    init_db()
    reset_database()
    add_students()
    add_teachers_and_subjects()
    add_classes()
    enroll_students()
    component_ids = add_grading_setup()
    add_scores(component_ids)
    grading.bulk_compute_class_grades("1", changed_by="demo")
    grading.bulk_compute_class_grades("2", changed_by="demo")
    print("Done. Open the app: python main.py")
