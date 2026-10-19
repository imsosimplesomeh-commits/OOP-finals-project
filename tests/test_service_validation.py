import os
import unittest
from uuid import uuid4
from unittest.mock import patch

import psycopg2
from psycopg2 import sql

import db
from models import (
    Student, Teacher, Subject, ClassOffering,
    GradeComponent, GradeComponentScore,
)
from repositories import (
    StudentRepository, TeacherRepository, SubjectRepository, ClassRepository,
    EnrollmentRepository, GradingPeriodRepository, GradeComponentRepository,
    GradePercentageRepository, ScoreRepository, GradeRepository,
)
from services.student_service import StudentService
from services.teacher_service import TeacherService
from services.subject_service import SubjectService
from services.class_service import ClassService
from services.configuration_service import ConfigurationService
from services.enrollment_service import EnrollmentService
from services.score_service import ScoreService


class TestServiceValidation(unittest.TestCase):
    def setUp(self):
        if not os.environ.get("PGDATABASE_TEST"):
            self.skipTest("set PGDATABASE_TEST to run database tests")
        self.config = dict(db.DB_CONFIG, dbname=os.environ["PGDATABASE_TEST"])
        if self.config["dbname"] == db.DB_CONFIG["dbname"]:
            raise ValueError("PGDATABASE_TEST must name a separate test database.")
        self.schema = "validation_test_" + uuid4().hex
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

    def make_services(self):
        self.student_service = StudentService(self.students, self.enrollments)
        self.teacher_service = TeacherService(self.teachers, self.classes)
        self.subject_service = SubjectService(self.subjects, self.classes)
        self.class_service = ClassService(self.classes, self.subjects, self.teachers, self.enrollments, self.weights)
        self.config_service = ConfigurationService(self.classes, self.periods, self.components, self.weights, self.scores)
        self.enrollment_service = EnrollmentService(self.enrollments, self.students, self.classes, self.scores, self.grades)
        self.score_service = ScoreService(self.scores, self.enrollments, self.components, self.weights, self.grades, self.periods)

    def add_class(self):
        self.make_services()
        teacher = self.teacher_service.add(Teacher(
            teacher_id="T-1001", first_name="Maria", last_name="Santos", department="Computer Studies Department",
        ))
        subject = self.subject_service.save(Subject(subject_code="CSPC 103", subject_name="Object Oriented Programming", units=3))
        return self.class_service.save(ClassOffering(
            class_code="CSPC103-A", teacher_id=teacher.teacher_id, subject_id=subject.subject_id,
            section="A", school_year="2026-2027", semester="1st",
        ))

    def add_student(self, student_id="2026-0001"):
        return self.student_service.add(Student(
            student_id=student_id, first_name="Juan", last_name="Dela Cruz", program="BSCS", year_level=2,
        ))

    def add_quiz(self, offering, name="Midterm", order=1):
        period = self.config_service.add_period(name, order)
        component = self.config_service.add_component(GradeComponent(
            period_id=period.period_id, name=name + " Quiz", type="Quiz", max_score=50,
        ))
        self.config_service.save_weights(offering.class_id, period.period_id, [(component.component_id, 100)])
        return period, component

    def test_student_required_fields_and_duplicate_number(self):
        self.make_services()
        saved = self.add_student()
        self.assertIsNone(saved.email)
        with self.assertRaisesRegex(ValueError, "already exists"):
            self.add_student()
        for field, value in [("student_id", ""), ("first_name", " "), ("last_name", ""),
                             ("program", ""), ("year_level", ""), ("year_level", "0")]:
            with self.subTest(field=field, value=value):
                student = Student(student_id="2026-0002", first_name="Ana", last_name="Garcia", program="BSCS", year_level=2)
                setattr(student, field, value)
                with self.assertRaises(ValueError):
                    self.student_service.add(student)
        self.assertEqual(len(self.students.find_all()), 1)
        saved.program = "BSIT"
        self.student_service.update(saved, "2026-0001")
        self.assertEqual(self.students.find_by_id("2026-0001").program, "BSIT")
        saved.student_id = "2026-0002"
        with self.assertRaisesRegex(ValueError, "cannot be changed"):
            self.student_service.update(saved, "2026-0001")

    def test_teacher_duplicate_and_required_fields(self):
        self.make_services()
        teacher = self.teacher_service.add(Teacher(
            teacher_id="T-1001", first_name="Maria", last_name="Santos", department="Computer Studies Department",
        ))
        self.assertIsNone(teacher.email)
        with self.assertRaisesRegex(ValueError, "already exists"):
            self.teacher_service.add(teacher)
        for field in ("teacher_id", "first_name", "last_name", "department"):
            record = Teacher(teacher_id="T-1002", first_name="Jose", last_name="Ramos", department="PE")
            setattr(record, field, " ")
            with self.assertRaises(ValueError):
                self.teacher_service.add(record)
        teacher.department = "Information Technology Department"
        self.teacher_service.update(teacher, "T-1001")
        self.assertEqual(self.teachers.find_by_id("T-1001").department, teacher.department)

    def test_subject_units_duplicates_and_unused_deletion(self):
        self.make_services()
        subject = self.subject_service.save(Subject(subject_code="CSPC 103", subject_name="OOP", units="3"))
        for units in ("", "0", "-1", "2.5", "NaN"):
            with self.assertRaises(ValueError):
                self.subject_service.save(Subject(subject_code="TEMP", subject_name="Temporary", units=units))
        with self.assertRaisesRegex(ValueError, "already exists"):
            self.subject_service.save(Subject(subject_code="CSPC 103", subject_name="Duplicate", units=3))
        subject.description = "Object-oriented analysis, design and programming in Java"
        self.subject_service.save(subject)
        self.assertEqual(self.subjects.find_by_id(subject.subject_id).description, subject.description)
        temporary = self.subject_service.save(Subject(subject_code="TEMP", subject_name="Temporary", units=1))
        self.subject_service.delete(temporary.subject_id)
        self.assertIsNone(self.subjects.find_by_id(temporary.subject_id))

    def test_class_required_fields_and_duplicate_code(self):
        offering = self.add_class()
        for field in ("class_code", "subject_id", "teacher_id", "school_year", "semester", "section"):
            record = ClassOffering(class_code="TEMP", subject_id=offering.subject_id, teacher_id="T-1001",
                                   section="B", school_year="2026-2027", semester="1st")
            setattr(record, field, "")
            with self.assertRaises(ValueError):
                self.class_service.save(record)
        with self.assertRaisesRegex(ValueError, "already exists"):
            self.class_service.save(ClassOffering(class_code="CSPC103-A", subject_id=offering.subject_id,
                                                 teacher_id="T-1001", section="A", school_year="2026-2027", semester="1st"))
        offering.room, offering.schedule = "CS-202", "TTh 1:00-2:30"
        self.class_service.save(offering)
        found = self.classes.find_by_id(offering.class_id)
        self.assertEqual((found.room, found.schedule), ("CS-202", "TTh 1:00-2:30"))

    def test_enrollment_rejections_status_and_empty_removal(self):
        offering = self.add_class()
        self.add_student()
        success, _, enrollment = self.enrollment_service.enroll_student("2026-0001", offering.class_id)
        self.assertTrue(success)
        success, message, _ = self.enrollment_service.enroll_student("2026-0001", offering.class_id)
        self.assertFalse(success)
        self.assertIn("already enrolled", message)
        self.assertFalse(self.enrollment_service.enroll_student("2026-9999", offering.class_id)[0])
        self.enrollment_service.update_status(enrollment.enrollment_id, "Dropped")
        self.enrollment_service.update_status(enrollment.enrollment_id, "Enrolled")
        self.assertEqual(self.enrollments.find_by_id(enrollment.enrollment_id).status, "Enrolled")
        self.enrollment_service.remove_enrollment(enrollment.enrollment_id)
        self.assertEqual(self.enrollments.find_all(), [])
        self.assertIsNotNone(self.students.find_by_id("2026-0001"))

    def test_parent_deletes_name_the_dependencies(self):
        offering = self.add_class()
        self.add_student()
        self.enrollment_service.enroll_student("2026-0001", offering.class_id)
        for service, record_id, dependency in [
            (self.student_service, "2026-0001", "enrollments"),
            (self.teacher_service, "T-1001", "CSPC103-A"),
            (self.subject_service, offering.subject_id, "CSPC103-A"),
            (self.class_service, offering.class_id, "enrollments"),
        ]:
            with self.assertRaisesRegex(ValueError, dependency):
                service.delete(record_id)
        self.assertEqual(len(self.enrollments.find_all()), 1)
        self.assertEqual(len(self.classes.find_all()), 1)
        self.add_student("2026-0099")
        self.student_service.delete("2026-0099")
        self.assertIsNone(self.students.find_by_id("2026-0099"))

    def test_period_and_component_validation(self):
        self.make_services()
        for name, order in [("", 1), ("Midterm", ""), ("Finals", 1), ("Midterm", 0)]:
            with self.assertRaises(ValueError):
                self.config_service.add_period(name, order)
        period = self.config_service.add_period("Midterm", "1")
        with self.assertRaisesRegex(ValueError, "already exists"):
            self.config_service.add_period("Midterm", 1)
        for maximum in ("", "0", "-1", "NaN", "Infinity"):
            with self.assertRaises(ValueError):
                self.config_service.add_component(GradeComponent(period_id=period.period_id, name="Quiz", type="Quiz", max_score=maximum))
        with self.assertRaises(ValueError):
            self.config_service.add_component(GradeComponent(period_id=period.period_id, name="", type="Quiz", max_score=50))

    def test_weights_reject_invalid_period_without_changing_saved_rows(self):
        offering = self.add_class()
        period = self.config_service.add_period("Midterm", 1)
        components = [self.config_service.add_component(GradeComponent(
            period_id=period.period_id, name=name, type=kind, max_score=maximum,
        )) for name, kind, maximum in [("Quiz", "Quiz", 50), ("Lab", "Laboratory", 100), ("Exam", "Exam", 100)]]
        ids = [component.component_id for component in components]
        self.config_service.save_weights(offering.class_id, period.period_id, list(zip(ids, [20, 30, 50])))
        before = self.query("SELECT * FROM grade_percentages ORDER BY percentage_id")
        for weights in [[20, 30, 40], [-10, 60, 50], [20, None, 80], [20, "", 80],
                        ["NaN", 0, 100], ["Infinity", 0, 0], [33.333, 33.333, 33.334]]:
            with self.subTest(weights=weights):
                with self.assertRaises(ValueError):
                    self.config_service.save_weights(offering.class_id, period.period_id, list(zip(ids, weights)))
                self.assertEqual(self.query("SELECT * FROM grade_percentages ORDER BY percentage_id"), before)
        self.config_service.save_weights(offering.class_id, period.period_id, list(zip(ids, [30, 30, 40])))
        self.assertEqual([w.percentage for w in self.weights.find_by_offering(offering.class_id)], [30, 30, 40])
        self.assertEqual(len(self.weights.find_all()), 3)

    def test_weight_repository_rolls_back_the_whole_period(self):
        offering = self.add_class()
        _, component = self.add_quiz(offering)
        with self.assertRaises(psycopg2.IntegrityError):
            self.weights.save_period(offering.class_id, [(component.component_id, 50), (999999, 50)])
        self.assertEqual(self.weights.find_all()[0].percentage, 100)

    def test_score_range_enrollment_and_safe_deletes(self):
        offering = self.add_class()
        self.add_student()
        _, component = self.add_quiz(offering)
        enrollment = self.enrollment_service.enroll_student("2026-0001", offering.class_id)[2]
        for value in ("", "-5", "55", "NaN", "Infinity"):
            with self.assertRaises(ValueError):
                self.score_service.save(GradeComponentScore(enrollment_id=enrollment.enrollment_id, component_id=component.component_id, score=value))
        saved = self.score_service.save(GradeComponentScore(enrollment_id=enrollment.enrollment_id, component_id=component.component_id, score=40))
        corrected = self.score_service.save(GradeComponentScore(enrollment_id=enrollment.enrollment_id, component_id=component.component_id, score=45))
        self.assertEqual(saved.score_id, corrected.score_id)
        with self.assertRaisesRegex(ValueError, "scores"):
            self.config_service.delete_component(component.component_id)
        with self.assertRaisesRegex(ValueError, "scores"):
            self.enrollment_service.remove_enrollment(enrollment.enrollment_id)
        self.enrollment_service.update_status(enrollment.enrollment_id, "Dropped")
        with self.assertRaisesRegex(ValueError, "enrolled"):
            self.score_service.save(GradeComponentScore(enrollment_id=enrollment.enrollment_id, component_id=component.component_id, score=40))
        self.assertEqual(self.scores.find_by_id(saved.score_id).score, 45)
        self.score_service.delete(saved.score_id)
        self.enrollment_service.remove_enrollment(enrollment.enrollment_id)
        with self.assertRaisesRegex(ValueError, "enrolled"):
            self.score_service.save(GradeComponentScore(enrollment_id=enrollment.enrollment_id, component_id=component.component_id, score=40))
        self.assertEqual(self.scores.find_all(), [])

    def test_score_changes_refresh_existing_grade_and_preserve_zero(self):
        offering = self.add_class()
        self.add_student()
        _, midterm = self.add_quiz(offering)
        _, finals = self.add_quiz(offering, "Finals", 2)
        enrollment = self.enrollment_service.enroll_student("2026-0001", offering.class_id)[2]
        self.score_service.save(GradeComponentScore(enrollment_id=enrollment.enrollment_id, component_id=midterm.component_id, score=40))
        saved = self.score_service.save(GradeComponentScore(enrollment_id=enrollment.enrollment_id, component_id=finals.component_id, score=45))
        grade = self.score_service.grading.generate_and_save_grade(enrollment.enrollment_id, offering.class_id)
        self.score_service.delete(saved.score_id)
        found = self.grades.find_by_enrollment(enrollment.enrollment_id)
        self.assertEqual((found.finals_grade, found.final_equiv, found.remarks), (None, None, "Incomplete"))
        self.score_service.save(GradeComponentScore(enrollment_id=enrollment.enrollment_id, component_id=finals.component_id, score=0))
        self.assertEqual(self.grades.find_by_enrollment(enrollment.enrollment_id).finals_grade, 0)
        self.score_service.save(GradeComponentScore(enrollment_id=enrollment.enrollment_id, component_id=finals.component_id, score=45))
        found = self.grades.find_by_enrollment(enrollment.enrollment_id)
        self.assertEqual((found.grade_id, found.overall_grade), (grade.grade_id, 86))
        self.assertEqual(len(self.grades.find_all()), 1)

