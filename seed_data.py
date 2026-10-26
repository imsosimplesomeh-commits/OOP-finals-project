# seed_data.py - seeds sample academic data for testing the CSPC 103 system

from datetime import date
from db import init_db
from models import (
    Student, Teacher, Subject, ClassOffering, GradingPeriod,
    GradePercentage, GradeComponent, Enrollment, GradeComponentScore
)
from repositories import (
    StudentRepository, TeacherRepository, SubjectRepository, ClassRepository,
    GradingPeriodRepository, GradePercentageRepository, GradeComponentRepository,
    EnrollmentRepository, ScoreRepository
)
from services import GradingService


def seed_all():
    print("Initializing database schema...")
    init_db()

    student_repo = StudentRepository()
    teacher_repo = TeacherRepository()
    subject_repo = SubjectRepository()
    class_repo = ClassRepository()
    period_repo = GradingPeriodRepository()
    perc_repo = GradePercentageRepository()
    comp_repo = GradeComponentRepository()
    enroll_repo = EnrollmentRepository()
    score_repo = ScoreRepository()
    grading_service = GradingService()

    # 1. Teachers
    teachers = teacher_repo.find_all()
    if not teachers:
        t1 = teacher_repo.save(Teacher(
            first_name="Brenda", last_name="Balala", email="bbalala@ndmu.edu.ph",
            department="Computer Studies", status="active"
        ))
    else:
        t1 = teachers[0]

    # 2. Subjects
    subjects = subject_repo.find_all()
    cs103 = None
    for s in subjects:
        if "CSPC 103" in s.subject_code or "CS103" in s.subject_code:
            cs103 = s
            break
    if not cs103:
        cs103 = subject_repo.save(Subject(
            subject_code="CSPC 103",
            subject_name="Object Oriented Programming",
            description="Advanced OOP Design, Design Patterns, Refactoring & Persistence",
            units=3
        ))

    # 3. Class Offerings
    offerings = class_repo.find_all()
    offering = None
    for o in offerings:
        if o.class_code == "CSPC103-A":
            offering = o
            break
    if not offering:
        offering = class_repo.save(ClassOffering(
            class_code="CSPC103-A",
            schedule="MWF 10:30-11:30 AM",
            section="BSCS-2A",
            school_year="2026-2027",
            semester="1st",
            room="CompLab 3",
            subject_id=cs103.subject_id,
            teacher_id=t1.teacher_id
        ))
    else:
        # update school year to 2026-2027 if it was previously older
        offering.school_year = "2026-2027"
        class_repo.save(offering)

    # 4. Grading Periods (Midterm and Finals)
    periods = period_repo.find_all()
    midterm_p = None
    finals_p = None
    for p in periods:
        if "mid" in p.name.lower():
            midterm_p = p
        elif "fin" in p.name.lower():
            finals_p = p

    if not midterm_p:
        midterm_p = period_repo.save(GradingPeriod(
            name="Midterm",
            start_date=date(2026, 8, 17),
            end_date=date(2026, 10, 16),
            school_year="2026-2027",
            semester="1st"
        ))
    else:
        midterm_p.start_date = date(2026, 8, 17)
        midterm_p.end_date = date(2026, 10, 16)
        midterm_p.school_year = "2026-2027"
        period_repo.save(midterm_p)

    if not finals_p:
        finals_p = period_repo.save(GradingPeriod(
            name="Finals",
            start_date=date(2026, 10, 19),
            end_date=date(2026, 12, 18),
            school_year="2026-2027",
            semester="1st"
        ))
    else:
        finals_p.start_date = date(2026, 10, 19)
        finals_p.end_date = date(2026, 12, 18)
        finals_p.school_year = "2026-2027"
        period_repo.save(finals_p)

    # 5. Grade percentages for class offering (Quizzes: 20%, Lab: 30%, Exams: 50%)
    existing_percentages = perc_repo.find_by_offering(offering.offering_id)
    perc_map = {p.component_type: p for p in existing_percentages}

    if "Quiz" not in perc_map:
        perc_quiz = perc_repo.save(GradePercentage(
            offering_id=offering.offering_id, component_type="Quiz", percentage=20.0
        ))
    else:
        perc_quiz = perc_map["Quiz"]

    if "Laboratory" not in perc_map:
        perc_lab = perc_repo.save(GradePercentage(
            offering_id=offering.offering_id, component_type="Laboratory", percentage=30.0
        ))
    else:
        perc_lab = perc_map["Laboratory"]

    if "Exam" not in perc_map:
        perc_exam = perc_repo.save(GradePercentage(
            offering_id=offering.offering_id, component_type="Exam", percentage=50.0
        ))
    else:
        perc_exam = perc_map["Exam"]

    # 6. Components for Midterm & Finals
    existing_comps = comp_repo.find_by_offering(offering.offering_id)
    comp_names = {c.name: c for c in existing_comps}

    # Midterm
    if "Midterm Quiz 1" not in comp_names:
        comp_repo.save(GradeComponent(
            grading_period_id=midterm_p.period_id, percentage_id=perc_quiz.percentage_id,
            name="Midterm Quiz 1", type="Quiz", max_score=50.0, description="OOP Principles & UML"
        ))
    if "Midterm Lab 1" not in comp_names:
        comp_repo.save(GradeComponent(
            grading_period_id=midterm_p.period_id, percentage_id=perc_lab.percentage_id,
            name="Midterm Lab 1", type="Laboratory", max_score=100.0, description="Domain Model Implementation"
        ))
    if "Midterm Exam" not in comp_names:
        comp_repo.save(GradeComponent(
            grading_period_id=midterm_p.period_id, percentage_id=perc_exam.percentage_id,
            name="Midterm Exam", type="Exam", max_score=100.0, description="Midterm Examination"
        ))

    # Finals
    if "Finals Quiz 2" not in comp_names:
        comp_repo.save(GradeComponent(
            grading_period_id=finals_p.period_id, percentage_id=perc_quiz.percentage_id,
            name="Finals Quiz 2", type="Quiz", max_score=50.0, description="Design Patterns & Repositories"
        ))
    if "Finals Project" not in comp_names:
        comp_repo.save(GradeComponent(
            grading_period_id=finals_p.period_id, percentage_id=perc_lab.percentage_id,
            name="Finals Project", type="Laboratory", max_score=100.0, description="GUI and DB Persistence"
        ))
    if "Final Exam" not in comp_names:
        comp_repo.save(GradeComponent(
            grading_period_id=finals_p.period_id, percentage_id=perc_exam.percentage_id,
            name="Final Exam", type="Exam", max_score=100.0, description="Comprehensive Finals Exam"
        ))

    # 7. Student Enrollments
    students = student_repo.find_all()
    if not students:
        s1 = student_repo.save(Student(first_name="Stefan Zuri", last_name="Modelo", email="smodelo@ndmu.edu.ph", program="BSCS 2", status="active"))
        s2 = student_repo.save(Student(first_name="Keinth Patrick", last_name="Morillo", email="kmorillo@ndmu.edu.ph", program="BSCS 2", status="active"))
        s3 = student_repo.save(Student(first_name="Andrae", last_name="Almodiente", email="aalmodiente@ndmu.edu.ph", program="BSCS 2", status="active"))
        students = [s1, s2, s3]

    enrollments = enroll_repo.find_by_offering(offering.offering_id)
    enrolled_student_ids = {e.student_id for e in enrollments}

    for st in students[:3]:
        if st.student_id not in enrolled_student_ids:
            en = enroll_repo.save(Enrollment(
                student_id=st.student_id,
                offering_id=offering.offering_id,
                enroll_date=date(2026, 8, 22),
                status="enrolled"
            ))
            enrollments.append(en)
        else:
            # ensure enrollment date is 2026
            for e in enrollments:
                if e.student_id == st.student_id:
                    e.enroll_date = date(2026, 8, 22)
                    enroll_repo.save(e)

    # 8. Component Scores with distinct Midterm and Finals performance
    all_comps = comp_repo.find_by_offering(offering.offering_id)
    student_score_map = [
        # Student 1: Stefan Zuri Modelo
        {
            "Midterm Quiz 1": 44.0,
            "Midterm Lab 1": 89.0,
            "Midterm Exam": 84.0,
            "Finals Quiz 2": 48.0,
            "Finals Project": 94.0,
            "Final Exam": 90.0,
        },
        # Student 2: Keinth Patrick Morillo
        {
            "Midterm Quiz 1": 47.0,
            "Midterm Lab 1": 96.0,
            "Midterm Exam": 92.0,
            "Finals Quiz 2": 49.0,
            "Finals Project": 98.0,
            "Final Exam": 95.0,
        },
        # Student 3: Andrae Almodiente
        {
            "Midterm Quiz 1": 39.0,
            "Midterm Lab 1": 82.0,
            "Midterm Exam": 78.0,
            "Finals Quiz 2": 41.0,
            "Finals Project": 86.0,
            "Final Exam": 81.0,
        },
    ]

    for idx, en in enumerate(enrollments[:3]):
        comp_scores = student_score_map[idx % len(student_score_map)]
        for comp in all_comps:
            actual = comp_scores.get(comp.name)
            if actual is None:
                actual = round(comp.max_score * 0.85, 1)
            score_repo.save(GradeComponentScore(
                enrollment_id=en.enrollment_id,
                component_id=comp.component_id,
                score=round(actual, 1),
                remarks="Recorded score",
                date_recorded=date(2026, 10, 6)
            ))

    # 9. Compute & Save Grades
    grades = grading_service.bulk_compute_class_grades(offering.offering_id)
    print(f"Sample data seeded successfully! Computed {len(grades)} grades for class {offering.class_code} (SY {offering.school_year}).")


if __name__ == "__main__":
    seed_all()
