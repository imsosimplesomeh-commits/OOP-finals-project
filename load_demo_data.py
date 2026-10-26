# load_demo_data.py - fills Modelo_CSPC103 with the finished test-run data from TEST_RUN_GUIDE.md
# Usage:  python load_demo_data.py   (click Reset Database first, the tables must be empty)
# Everything is saved through the services, so grades and the audit log come from the real code.

import sys

from db import DB_CONFIG, init_db
from models import Student, Teacher, Subject, ClassOffering, GradeComponent, GradeComponentScore
from repositories import (
    AuditRepository, StudentRepository, TeacherRepository, SubjectRepository,
    ClassRepository, GradingPeriodRepository, GradeComponentRepository,
)
from services.student_service import StudentService
from services.teacher_service import TeacherService
from services.subject_service import SubjectService
from services.class_service import ClassService
from services.enrollment_service import EnrollmentService
from services.configuration_service import ConfigurationService
from services.score_service import ScoreService
from services.grading_service import GradingService

DEMO_DB = "Modelo_CSPC103"

students = StudentService()
teachers = TeacherService()
subjects = SubjectService()
classes = ClassService()
enrollments = EnrollmentService()
config = ConfigurationService()
scores = ScoreService()
grading = GradingService()

# name, category, max score; the first three are Midterm, the last three are Finals
COMPONENTS = [("Midterm Quiz", "Quiz", 50), ("Midterm Laboratory/Project", "Laboratory", 100),
              ("Midterm Examination", "Exam", 100), ("Final Quiz", "Quiz", 50),
              ("Final Laboratory/Project", "Laboratory", 100), ("Final Examination", "Exam", 100)]

# raw scores in the same order as COMPONENTS (Juan's Midterm Examination starts at 57, fixed to 75 later)
CSPC_SCORES = {"2026-0001": [40, 90, 57, 45, 85, 80],
               "2026-0002": [20, 60, 55, 30, 70, 65],
               "2026-0003": [50, 100, 100, 48, 95, 92]}
PATHFIT_SCORES = [45, 90, 90, 45, 90, 90]


def check_database():
    # only the demo database, and only when it is empty
    if DB_CONFIG["dbname"] != DEMO_DB:
        sys.exit(f"Stop: this script only loads {DEMO_DB}, not {DB_CONFIG['dbname']}.")
    init_db()
    # enrollments, scores and grades cannot exist without these rows, and every change writes the audit log
    repos = [StudentRepository(), TeacherRepository(), SubjectRepository(), ClassRepository(),
             GradingPeriodRepository(), GradeComponentRepository(), AuditRepository()]
    if any(repo.find_all() for repo in repos):
        sys.exit("Stop: the tables are not empty. Click Reset Database in the app first, then run this again.")


def add_records():
    for number, first, last, program, year in [("2026-0001", "Juan", "Dela Cruz", "BSCS", 2),
                                               ("2026-0002", "Pedro", "Reyes", "BSCS", 2),
                                               ("2026-0003", "Ana", "Garcia", "BSCS", 2),
                                               ("2026-0098", "Carlo", "Mendoza", "BSIT", 1)]:
        students.add(Student(student_id=number, first_name=first, last_name=last, program=program, year_level=year))
    teachers.add(Teacher(teacher_id="T-1001", first_name="Maria", last_name="Santos",
                         department="Information Technology Department"))
    teachers.add(Teacher(teacher_id="T-1002", first_name="Jose", last_name="Ramos",
                         department="Physical Education Department"))
    cspc = subjects.save(Subject(subject_code="CSPC 103", subject_name="Object Oriented Programming", units=3,
                                 description="Object-oriented analysis, design and programming in Java"))
    pathfit = subjects.save(Subject(subject_code="PATHFIT 3", units=2,
                                    subject_name="Physical Activity Towards Health and Fitness 3"))
    return cspc, pathfit


def add_class(code, subject, teacher_id, schedule, room):
    return classes.save(ClassOffering(class_code=code, subject_id=subject.subject_id, teacher_id=teacher_id,
                                      section="A", schedule=schedule, room=room,
                                      school_year="2026-2027", semester="1st"))


def enroll(student_id, offering):
    _, _, enrollment = enrollments.enroll_student(student_id, offering.class_id)
    return enrollment.enrollment_id


def add_components():
    midterm = config.add_period("Midterm", 1, "2026-2027", "1st")
    finals = config.add_period("Finals", 2, "2026-2027", "1st")
    ids = []
    for name, category, max_score in COMPONENTS:
        period = midterm if name.startswith("Midterm") else finals
        component = config.add_component(GradeComponent(period_id=period.period_id, name=name,
                                                        type=category, max_score=max_score))
        ids.append(component.component_id)
    return midterm, finals, ids


def set_weights(offering, period, component_ids, weights):
    config.save_weights(offering.class_id, period.period_id, list(zip(component_ids, weights)))


def save_score(enrollment_id, component_id, value):
    scores.save(GradeComponentScore(enrollment_id=enrollment_id, component_id=component_id, score=value))


def find_score_id(enrollment_id, component_id):
    for score, _ in scores.get_scores(enrollment_id):
        if str(score.component_id) == str(component_id):
            return score.score_id
    return None


def load_cspc(offering, midterm, finals, ids):
    enrolled = {number: enroll(number, offering) for number in CSPC_SCORES}
    set_weights(offering, midterm, ids[:3], [20, 30, 50])
    set_weights(offering, finals, ids[3:], [20, 30, 50])
    for number, values in CSPC_SCORES.items():
        for component_id, value in zip(ids, values):
            save_score(enrolled[number], component_id, value)
    # SC-06: Juan's Midterm Examination is corrected from 57 to 75
    save_score(enrolled["2026-0001"], ids[2], 75)
    grading.bulk_compute_class_grades(offering.class_id)
    # SC-07: Ana's Final Quiz is deleted, then entered again
    scores.delete(find_score_id(enrolled["2026-0003"], ids[3]))
    save_score(enrolled["2026-0003"], ids[3], 48)
    # GR-03: the Midterm weights change to 30/30/40 and the grades are computed again
    set_weights(offering, midterm, ids[:3], [30, 30, 40])
    grading.bulk_compute_class_grades(offering.class_id)


def load_pathfit(offering, midterm, finals, ids):
    juan = enroll("2026-0001", offering)
    set_weights(offering, midterm, ids[:3], [20, 30, 50])
    set_weights(offering, finals, ids[3:], [20, 30, 50])
    for component_id, value in zip(ids, PATHFIT_SCORES):
        save_score(juan, component_id, value)
    grading.bulk_compute_class_grades(offering.class_id)


def main():
    check_database()
    cspc, pathfit = add_records()
    cspc_class = add_class("CSPC103-A", cspc, "T-1001", "TTh 1:00-2:30", "CS-202")
    pathfit_class = add_class("PATHFIT3-A", pathfit, "T-1002", "TTh 3:00-5:00", "Gym")
    midterm, finals, ids = add_components()
    load_cspc(cspc_class, midterm, finals, ids)
    load_pathfit(pathfit_class, midterm, finals, ids)
    # PS-02: a name with an apostrophe
    students.add(Student(student_id="2026-0004", first_name="Kevin", last_name="O'Brien", program="BSIT", year_level=1))
    print("Demo data loaded into " + DEMO_DB + ".")


if __name__ == "__main__":
    main()
