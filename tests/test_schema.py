import os
import unittest
from uuid import uuid4
from unittest.mock import patch

import psycopg2
from psycopg2 import sql

import db
from models import (
    Student, Teacher, Subject, ClassOffering, Enrollment, GradingPeriod,
    GradeComponent, GradePercentage, GradeComponentScore, Grade,
)
from repositories import (
    StudentRepository, TeacherRepository, SubjectRepository, ClassRepository,
    EnrollmentRepository, GradingPeriodRepository, GradeComponentRepository,
    GradePercentageRepository, ScoreRepository, GradeRepository,
)
from services.grading_service import GradingService


class TestChecklistSchema(unittest.TestCase):
    def setUp(self):
        if not os.environ.get("PGDATABASE_TEST"):
            self.skipTest("set PGDATABASE_TEST to run database tests")
        self.config = dict(db.DB_CONFIG, dbname=os.environ["PGDATABASE_TEST"])
        self.schema = "schema_test_" + uuid4().hex
        conn = psycopg2.connect(**self.config)
        try:
            with conn, conn.cursor() as cur:
                cur.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(self.schema)))
        finally:
            conn.close()
        self.addCleanup(self.remove_schema)
        with patch("db.get_connection", self.connect):
            db.init_db()
        self.students = StudentRepository(self.connect)
        self.teachers = TeacherRepository(self.connect)
        self.subjects = SubjectRepository(self.connect)
        self.classes = ClassRepository(self.connect)
        self.enrollments = EnrollmentRepository(self.connect)
        self.periods = GradingPeriodRepository(self.connect)
        self.components = GradeComponentRepository(self.connect)
        self.weights = GradePercentageRepository(self.connect)
        self.scores = ScoreRepository(self.connect)
        self.grades = GradeRepository(self.connect)

    def connect(self):
        return psycopg2.connect(**self.config, options="-c search_path=" + self.schema)

    def remove_schema(self):
        # only the schema created by this test is removed
        conn = psycopg2.connect(**self.config)
        try:
            with conn, conn.cursor() as cur:
                cur.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(self.schema)))
        finally:
            conn.close()

    def query(self, statement, params=()):
        conn = self.connect()
        try:
            with conn, conn.cursor() as cur:
                cur.execute(statement, params)
                return cur.fetchall() if cur.description else []
        finally:
            conn.close()

    def add_records(self):
        self.student = self.students.save(Student(
            student_id="2026-0001", first_name="Juan", last_name="Dela Cruz",
            program="BSCS", year_level=2,
        ))
        self.teacher = self.teachers.save(Teacher(
            teacher_id="T-1001", first_name="Maria", last_name="Santos",
            department="Computer Studies Department",
        ))
        self.subject = self.subjects.save(Subject(
            subject_code="CSPC 103", subject_name="Object Oriented Programming", units=3,
        ))
        self.offering = self.classes.save(ClassOffering(
            class_code="CSPC103-A", subject_id=self.subject.subject_id,
            teacher_id=self.teacher.teacher_id, section="A",
            school_year="2026-2027", semester="1st",
        ))
        self.enrollment = self.enrollments.save(Enrollment(
            student_id=self.student.student_id, class_id=self.offering.class_id,
        ))
        self.period = self.periods.save(GradingPeriod(
            name="Midterm", period_order=1, school_year="2026-2027", semester="1st",
        ))
        self.component = self.components.save(GradeComponent(
            period_id=self.period.period_id, name="Midterm Quiz", type="Quiz", max_score=50,
        ))
        self.weight = self.weights.save(GradePercentage(
            class_id=self.offering.class_id, component_id=self.component.component_id, percentage=20,
        ))

    def test_empty_schema_and_repeat_setup(self):
        with patch("db.get_connection", self.connect):
            db.init_db()
        tables = self.query(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = %s",
            (self.schema,),
        )
        self.assertEqual({row[0] for row in tables}, {
            "students", "teachers", "subjects", "class_offerings", "enrollments",
            "grading_periods", "grade_components", "grade_percentages",
            "grade_component_scores", "grades", "audit_log",
        })
        for (table,) in tables:
            count = self.query(sql.SQL("SELECT COUNT(*) FROM {}").format(sql.Identifier(table)))
            self.assertEqual(count[0][0], 0)
        links = self.query(
            "SELECT confdeltype FROM pg_constraint WHERE connamespace = %s::regnamespace AND contype = %s",
            (self.schema, "f"),
        )
        self.assertEqual(len(links), 10)
        self.assertTrue(all(row[0] == "r" for row in links))

    def test_text_ids_optional_emails_and_updates(self):
        self.add_records()
        self.assertIsNone(self.students.find_by_id("2026-0001").email)
        self.assertEqual(self.students.find_all()[0].year_level, 2)
        self.assertIsNone(self.teachers.find_by_id("T-1001").email)
        self.student.program = "BSIT"
        self.students.save(self.student)
        self.teacher.department = "Information Technology Department"
        self.teachers.save(self.teacher)
        self.assertEqual(self.students.find_by_id("2026-0001").program, "BSIT")
        self.assertEqual(self.teachers.find_all()[0].department, self.teacher.department)
        self.assertEqual(len(self.students.search("Dela Cruz")), 1)
        self.assertEqual(len(self.teachers.search("Santos")), 1)
        self.students.save(Student(
            student_id="2026-0004", first_name="Kevin", last_name="O'Brien",
            program="BSIT", year_level=1, email="",
        ))
        self.assertEqual(len(self.students.search("O'Brien")), 1)
        self.assertEqual(self.students.search("' OR '1'='1"), [])
        with self.assertRaises(psycopg2.errors.UniqueViolation):
            self.query(
                "INSERT INTO students (student_id, first_name, last_name, program, year_level) VALUES (%s, %s, %s, %s, %s)",
                ("2026-0001", "Other", "Student", "BSCS", 2),
            )

    def test_class_and_enrollment_queries(self):
        self.add_records()
        self.offering.room = "CS-202"
        self.classes.save(self.offering)
        self.assertEqual(self.classes.find_by_id(self.offering.class_id).room, "CS-202")
        self.assertEqual(self.classes.find_all()[0].teacher_name, "Santos, Maria")
        self.assertEqual(len(self.enrollments.find_by_student("2026-0001")), 1)
        self.assertEqual(len(self.enrollments.find_by_offering(self.offering.class_id)), 1)
        self.assertIsNotNone(self.enrollments.find_by_student_and_offering("2026-0001", self.offering.class_id))
        self.enrollment.status = "Dropped"
        self.enrollments.save(self.enrollment)
        self.assertEqual(self.enrollments.find_by_id(self.enrollment.enrollment_id).status, "Dropped")
        with self.assertRaises(psycopg2.errors.UniqueViolation):
            self.enrollments.save(Enrollment(student_id="2026-0001", class_id=self.offering.class_id))
        with self.assertRaises(psycopg2.errors.ForeignKeyViolation):
            self.enrollments.save(Enrollment(student_id="2026-9999", class_id=self.offering.class_id))

    def test_component_weights_are_per_class(self):
        self.add_records()
        other = self.classes.save(ClassOffering(
            class_code="CSPC103-B", subject_id=self.subject.subject_id,
            teacher_id=self.teacher.teacher_id, school_year="2026-2027", semester="1st",
        ))
        self.weights.save(GradePercentage(class_id=other.class_id, component_id=self.component.component_id, percentage=30))
        self.assertEqual(self.components.find_by_offering(self.offering.class_id)[0].percentage_value, 20)
        self.assertEqual(self.components.find_by_offering(other.class_id)[0].percentage_value, 30)
        self.assertEqual(len(self.components.find_all()), 1)
        self.assertEqual(self.components.find_by_id(self.component.component_id).period_id, self.period.period_id)
        self.assertEqual(len(self.components.find_by_offering_and_period(other.class_id, self.period.period_id)), 1)
        self.component.max_score = 60
        self.components.save(self.component)
        self.assertEqual(self.components.find_by_id(self.component.component_id).max_score, 60)
        self.weight.percentage = 40
        self.weights.save(self.weight)
        self.assertEqual(self.weights.find_by_id(self.weight.percentage_id).percentage, 40)
        self.assertEqual(len(self.weights.find_all()), 2)
        self.assertEqual(self.weights.find_by_offering(other.class_id)[0].percentage, 30)
        with self.assertRaises(psycopg2.errors.UniqueViolation):
            self.weights.save(GradePercentage(class_id=other.class_id, component_id=self.component.component_id, percentage=50))

    def test_period_order_is_saved_and_used(self):
        self.periods.save(GradingPeriod(name="Finals", period_order=2, school_year="2026-2027", semester="1st"))
        midterm = self.periods.save(GradingPeriod(name="Midterm", period_order=1, school_year="2026-2027", semester="1st"))
        self.assertEqual([p.name for p in self.periods.find_all()], ["Midterm", "Finals"])
        self.assertEqual(len(self.periods.find_by_term("2026-2027", "1st")), 2)
        midterm.name = "Midterm Updated"
        self.periods.save(midterm)
        self.assertEqual(self.periods.find_by_id(midterm.period_id).name, "Midterm Updated")

    def test_grades_upsert_and_incomplete_values(self):
        self.add_records()
        score = self.scores.save(GradeComponentScore(enrollment_id=self.enrollment.enrollment_id, component_id=self.component.component_id, score=40))
        grade = self.grades.save(Grade(enrollment_id=self.enrollment.enrollment_id))
        self.assertIsNone(self.grades.find_by_id(grade.grade_id).overall_grade)
        grade.midterm_grade, grade.finals_grade, grade.overall_grade = 81, 83.5, 82.5
        grade.midterm_equiv, grade.final_equiv, grade.remarks = 2.5, 2.25, "Passed"
        saved = self.grades.save(grade)
        self.assertEqual(saved.grade_id, grade.grade_id)
        self.assertEqual(len(self.grades.find_all()), 1)
        found = self.grades.find_by_enrollment(self.enrollment.enrollment_id)
        self.assertEqual((found.midterm_equiv, found.final_equiv, found.overall_grade), (2.5, 2.25, 82.5))
        self.assertEqual(len(self.grades.find_by_offering(self.offering.class_id)), 1)
        self.assertEqual(self.scores.find_by_id(score.score_id).score, 40)

    def test_dependent_records_cannot_be_deleted(self):
        self.add_records()
        self.scores.save(GradeComponentScore(enrollment_id=self.enrollment.enrollment_id, component_id=self.component.component_id, score=40))
        self.weights.delete_by_id(self.weight.percentage_id)
        for repo, record_id in [
            (self.students, self.student.student_id), (self.teachers, self.teacher.teacher_id),
            (self.subjects, self.subject.subject_id), (self.classes, self.offering.class_id),
            (self.components, self.component.component_id), (self.enrollments, self.enrollment.enrollment_id),
        ]:
            with self.subTest(repository=type(repo).__name__):
                with self.assertRaises((psycopg2.errors.ForeignKeyViolation, psycopg2.errors.RestrictViolation)):
                    repo.delete_by_id(record_id)
        self.assertEqual(len(self.scores.find_all()), 1)
        self.assertEqual(len(self.enrollments.find_all()), 1)

    def test_required_year_level_and_audit_storage(self):
        with self.assertRaises(psycopg2.errors.NotNullViolation):
            self.students.save(Student(student_id="2026-0001", first_name="Juan", last_name="Dela Cruz", program="BSCS"))
        self.query(
            "INSERT INTO audit_log (table_name, record_id, action, old_value, new_value, changed_by) VALUES (%s, %s, %s, %s, %s, %s)",
            ("GRADE_COMPONENT_SCORE", "3", "UPDATE", "57", "75", "tester"),
        )
        row = self.query("SELECT record_id, old_value, new_value, changed_by, changed_at FROM audit_log")[0]
        self.assertEqual(row[:4], ("3", "57", "75", "tester"))
        self.assertIsNotNone(row[4])

    def add_grading_records(self):
        self.add_records()
        finals = self.periods.save(GradingPeriod(name="Finals", period_order=2))
        self.grade_components = [self.component]
        for period, name, kind, maximum, weight in [
            (self.period, "Midterm Laboratory/Project", "Laboratory", 100, 30),
            (self.period, "Midterm Examination", "Exam", 100, 50),
            (finals, "Final Quiz", "Quiz", 50, 20),
            (finals, "Final Laboratory/Project", "Laboratory", 100, 30),
            (finals, "Final Examination", "Exam", 100, 50),
        ]:
            component = self.components.save(GradeComponent(
                period_id=period.period_id, name=name, type=kind, max_score=maximum,
            ))
            self.weights.save(GradePercentage(
                class_id=self.offering.class_id, component_id=component.component_id,
                percentage=weight,
            ))
            self.grade_components.append(component)
        self.grade_enrollments = [self.enrollment]
        for number, first, last in [("2026-0002", "Pedro", "Reyes"), ("2026-0003", "Ana", "Garcia")]:
            self.students.save(Student(
                student_id=number, first_name=first, last_name=last, program="BSCS", year_level=2,
            ))
            self.grade_enrollments.append(self.enrollments.save(Enrollment(
                student_id=number, class_id=self.offering.class_id,
            )))
        for enrollment, scores in zip(self.grade_enrollments, [
            [40, 90, 75, 45, 85, 80], [20, 60, 55, 30, 70, 65], [50, 100, 100, 48, 95, 92],
        ]):
            for component, score in zip(self.grade_components, scores):
                self.scores.save(GradeComponentScore(
                    enrollment_id=enrollment.enrollment_id, component_id=component.component_id,
                    score=score,
                ))
        self.grading = GradingService(
            self.enrollments, self.weights, self.components, self.scores, self.grades, self.periods,
        )

    def test_service_saves_checklist_grades_and_recalculates(self):
        self.add_grading_records()
        raw_before = self.query("SELECT * FROM grade_component_scores ORDER BY score_id")
        self.assertTrue(self.grading.validate_percentages(self.offering.class_id)[0])
        self.grading.bulk_compute_class_grades(self.offering.class_id)
        grade_ids = [g.grade_id for g in self.grades.find_all()]
        for enrollment, expected in zip(self.grade_enrollments, [
            (80.5, 83.5, 82.3, 2.5, 2.25, "Passed"),
            (53.5, 65.5, 60.7, 5, 5, "Failed"),
            (100, 93.7, 96.22, 1, 1.25, "Passed"),
        ]):
            grade = self.grades.find_by_enrollment(enrollment.enrollment_id)
            self.assertEqual((grade.midterm_grade, grade.finals_grade, grade.overall_grade,
                              grade.midterm_equiv, grade.final_equiv, grade.remarks), expected)
        for weight in self.weights.find_by_offering(self.offering.class_id):
            if weight.component_id == self.grade_components[0].component_id:
                weight.percentage = 30
            elif weight.component_id == self.grade_components[2].component_id:
                weight.percentage = 40
            self.weights.save(weight)
        self.grading.bulk_compute_class_grades(self.offering.class_id)
        for enrollment, expected in zip(self.grade_enrollments, [(81, 82.5), (52, 60.1), (100, 96.22)]):
            grade = self.grades.find_by_enrollment(enrollment.enrollment_id)
            self.assertEqual((grade.midterm_grade, grade.overall_grade), expected)
        self.assertCountEqual([g.grade_id for g in self.grades.find_all()], grade_ids)
        self.assertEqual(self.query("SELECT * FROM grade_component_scores ORDER BY score_id"), raw_before)

    def test_service_missing_score_is_saved_as_null(self):
        self.add_grading_records()
        enrollment_id = self.grade_enrollments[2].enrollment_id
        original = self.grading.generate_and_save_grade(enrollment_id, self.offering.class_id)
        component_id = self.grade_components[3].component_id
        score = self.scores.find_by_enrollment_and_component(enrollment_id, component_id)
        self.scores.delete_by_id(score.score_id)
        self.grading.generate_and_save_grade(enrollment_id, self.offering.class_id)
        grade = self.grades.find_by_enrollment(enrollment_id)
        self.assertEqual((grade.midterm_grade, grade.midterm_equiv), (100, 1))
        self.assertEqual((grade.finals_grade, grade.overall_grade, grade.final_equiv), (None, None, None))
        self.assertEqual(grade.remarks, "Incomplete")
        self.assertEqual(self.query(
            "SELECT finals_grade IS NULL, overall_grade IS NULL FROM grades WHERE grade_id = %s",
            (grade.grade_id,),
        ), [(True, True)])
        self.scores.save(GradeComponentScore(enrollment_id=enrollment_id, component_id=component_id, score=48))
        self.grading.generate_and_save_grade(enrollment_id, self.offering.class_id)
        grade = self.grades.find_by_enrollment(enrollment_id)
        self.assertEqual((grade.grade_id, grade.finals_grade, grade.overall_grade), (original.grade_id, 93.7, 96.22))

    def test_service_uses_unrounded_percentage_for_grade_points(self):
        self.add_grading_records()
        for component in self.grade_components:
            component.max_score = 2000
            self.components.save(component)
            self.scores.save(GradeComponentScore(
                enrollment_id=self.enrollment.enrollment_id, component_id=component.component_id,
                score=1939.9,
            ))
        self.grading.generate_and_save_grade(self.enrollment.enrollment_id, self.offering.class_id)
        grade = self.grades.find_by_enrollment(self.enrollment.enrollment_id)
        self.assertEqual((grade.midterm_grade, grade.overall_grade), (97, 97))
        self.assertEqual((grade.midterm_equiv, grade.final_equiv), (1.25, 1.25))

    def test_service_checks_weights_per_period(self):
        self.add_grading_records()
        for weight in self.weights.find_by_offering(self.offering.class_id):
            if weight.component_id == self.grade_components[0].component_id:
                weight.percentage = 10
            elif weight.component_id == self.grade_components[3].component_id:
                weight.percentage = 30
            self.weights.save(weight)
        valid, message = self.grading.validate_percentages(self.offering.class_id)
        self.assertFalse(valid)
        self.assertIn("Midterm", message)
        with self.assertRaises(ValueError):
            self.grading.generate_and_save_grade(self.enrollment.enrollment_id, self.offering.class_id)
        self.assertEqual(self.grades.find_all(), [])
