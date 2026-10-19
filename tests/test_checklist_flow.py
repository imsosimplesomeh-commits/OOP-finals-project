import json
import os
import unittest
from datetime import date
from unittest.mock import patch
from uuid import uuid4

import psycopg2
from psycopg2 import sql

import db
from models import Student, Teacher, Subject, ClassOffering, GradeComponent, GradeComponentScore
from repositories import (
    StudentRepository, TeacherRepository, SubjectRepository, ClassRepository,
    EnrollmentRepository, GradingPeriodRepository, GradeComponentRepository,
    GradePercentageRepository, ScoreRepository, GradeRepository, AuditRepository,
)
from repositories.report_repository import ReportRepository
from services.student_service import StudentService
from services.teacher_service import TeacherService
from services.subject_service import SubjectService
from services.class_service import ClassService
from services.enrollment_service import EnrollmentService
from services.configuration_service import ConfigurationService
from services.score_service import ScoreService
from services.report_service import ReportService
from services.grade_calculator import GradeCalculator


# run with: python -m unittest tests.test_checklist_flow -v
# GUI confirmations and a full application restart still need a manual demo.
ROW_COUNTS = {
    "students": 5, "teachers": 2, "subjects": 2, "class_offerings": 2,
    "enrollments": 4, "grading_periods": 2, "grade_components": 6,
    "grade_percentages": 12, "grade_component_scores": 24, "grades": 4,
}
RAW_SCORES = ([40, 90, 57, 45, 85, 80], [20, 60, 55, 30, 70, 65],
              [50, 100, 100, 48, 95, 92])
EXPECTED = [(80.50, 83.50, 82.30, 2.50, 2.25, "Passed"),
            (53.50, 65.50, 60.70, 5.00, 5.00, "Failed"),
            (100.00, 93.70, 96.22, 1.00, 1.25, "Passed")]


class TestChecklistFlow(unittest.TestCase):
    def setUp(self):
        database = os.environ.get("PGDATABASE_TEST")
        if not database:
            self.skipTest("set PGDATABASE_TEST to a separate test database")
        if database == db.DB_CONFIG["dbname"]:
            raise ValueError("PGDATABASE_TEST must name a separate test database.")
        self.config = dict(db.DB_CONFIG, dbname=database)
        self.schema = "checklist_test_" + uuid4().hex
        conn = psycopg2.connect(**self.config)
        try:
            with conn, conn.cursor() as cur:
                cur.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(self.schema)))
        finally:
            conn.close()
        self.addCleanup(self.remove_schema)
        with patch("db.get_connection", self.connect):
            db.init_db()
        self.make_services()

    def connect(self):
        return psycopg2.connect(**self.config, options="-c search_path=" + self.schema)

    def remove_schema(self):
        # only this rehearsal's generated schema is removed
        conn = psycopg2.connect(**self.config)
        try:
            with conn, conn.cursor() as cur:
                cur.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(self.schema)))
        finally:
            conn.close()

    def make_services(self):
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
        self.audit = AuditRepository(self.connect)
        self.student = StudentService(self.students, self.enrollments)
        self.teacher = TeacherService(self.teachers, self.classes)
        self.subject = SubjectService(self.subjects, self.classes)
        self.offering = ClassService(self.classes, self.subjects, self.teachers,
                                     self.enrollments, self.weights)
        self.enrollment = EnrollmentService(self.enrollments, self.students, self.classes,
                                            self.scores, self.grades)
        self.configuration = ConfigurationService(self.classes, self.periods, self.components,
                                                   self.weights, self.scores)
        self.score = ScoreService(self.scores, self.enrollments, self.components,
                                  self.weights, self.grades, self.periods)
        self.grading = self.score.grading
        self.report = ReportService(ReportRepository(self.connect), self.students)

    def rows(self, table):
        conn = self.connect()
        try:
            with conn, conn.cursor() as cur:
                cur.execute(sql.SQL("SELECT * FROM {} ORDER BY 1").format(sql.Identifier(table)))
                return cur.fetchall()
        finally:
            conn.close()

    def snapshot(self):
        conn = self.connect()
        try:
            with conn, conn.cursor() as cur:
                saved = {}
                for table in (*ROW_COUNTS, "audit_log"):
                    cur.execute(sql.SQL("SELECT * FROM {} ORDER BY 1").format(sql.Identifier(table)))
                    saved[table] = cur.fetchall()
                return saved
        finally:
            conn.close()

    def reject(self, message, action, *args):
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, message):
            action(*args)
        self.assertEqual(self.snapshot(), before)

    def add_student(self, number, first, last, program="BSCS", year=2):
        return self.student.add(Student(student_id=number, first_name=first, last_name=last,
                                        program=program, year_level=year))

    def enroll(self, number, class_id):
        success, message, saved = self.enrollment.enroll_student(number, class_id)
        self.assertTrue(success, message)
        self.assertIsNotNone(saved)
        return saved

    def save_score(self, enrollment_id, component_index, value):
        return self.score.save(GradeComponentScore(
            enrollment_id=enrollment_id,
            component_id=self.component_list[component_index].component_id, score=value,
        ), changed_by="checklist-tester")

    def set_weights(self, class_id, period_index, values):
        components = self.component_list[period_index * 3:period_index * 3 + 3]
        return self.configuration.save_weights(class_id, self.period_list[period_index].period_id,
            [(c.component_id, value) for c, value in zip(components, values)],
            changed_by="checklist-tester")

    def class_grades(self):
        return [self.grades.find_by_enrollment(e.enrollment_id) for e in self.enrollment_list]

    def case_st01(self):
        for number, first, last, program in [
            ("2026-0001", "Juan", "Dela Cruz", "BSCS"),
            ("2026-0002", "Pedro", "Reyes", "BSCS"),
            ("2026-0003", "Ana", "Garcia", "BSIT"),
        ]:
            saved = self.add_student(number, first, last, program)
            self.assertEqual(self.student.find_by_id(number), saved)
            self.assertIsNone(saved.email)
        self.assertEqual(len(self.student.find_all()), 3)

    def case_st02(self):
        self.reject("already exists", self.add_student, "2026-0001", "Other", "Student")

    def case_st03(self):
        for number, first, last in [("", "Juan", "Dela Cruz"),
                                    ("2026-0010", "", "Test"), ("2026-0010", "Test", "")]:
            self.reject("required", self.add_student, number, first, last)

    def case_st04(self):
        self.assertEqual([s.student_id for s in self.student.search("Reyes")], ["2026-0002"])
        saved = self.student.find_by_id("2026-0002")
        self.assertEqual((saved.first_name, saved.last_name, saved.program, saved.year_level),
                         ("Pedro", "Reyes", "BSCS", 2))

    def case_st05(self):
        saved = self.student.find_by_id("2026-0003")
        saved.program = "BSCS"
        self.student.update(saved, saved.student_id)
        self.assertEqual(self.student.find_by_id(saved.student_id), saved)

    def case_st06(self):
        self.add_student("2026-0099", "Lea", "Ramos", "BSIT", 1)
        self.student.delete("2026-0099")
        self.assertIsNone(self.student.find_by_id("2026-0099"))

    def case_st07(self):
        self.reject("enrollment", self.student.delete, "2026-0001")

    def case_te01(self):
        saved = self.teacher.add(Teacher(teacher_id="T-1001", first_name="Maria", last_name="Santos",
                                         department="Computer Studies Department"))
        self.assertEqual(self.teacher.find_by_id("T-1001"), saved)

    def case_te02(self):
        self.reject("already exists", self.teacher.add, Teacher(
            teacher_id="T-1001", first_name="Maria", last_name="Santos", department="Test"))
        self.reject("required", self.teacher.add, Teacher(
            teacher_id="T-1099", first_name="", last_name="Santos", department="Test"))

    def case_te03(self):
        self.assertEqual([(t.teacher_id, t.first_name, t.last_name, t.department)
                          for t in self.teacher.find_all()],
                         [("T-1001", "Maria", "Santos", "Computer Studies Department")])

    def case_te04(self):
        saved = self.teacher.find_by_id("T-1001")
        saved.department = "Information Technology Department"
        self.teacher.update(saved, saved.teacher_id)
        self.assertEqual(self.teacher.find_by_id(saved.teacher_id), saved)

    def case_te05(self):
        self.reject("class CSPC103-A", self.teacher.delete, "T-1001")

    def case_su01(self):
        self.main_subject = self.subject.save(Subject(
            subject_code="CSPC 103", subject_name="Object Oriented Programming", units=3))
        self.assertEqual(self.subject.find_by_id(self.main_subject.subject_id), self.main_subject)

    def case_su02(self):
        self.reject("already exists", self.subject.save, Subject(
            subject_code="CSPC 103", subject_name="Duplicate", units=3))
        for units in (0, -1):
            self.reject("positive whole number", self.subject.save, Subject(
                subject_code="TEMP", subject_name="Temporary", units=units))

    def case_su03(self):
        self.assertEqual(self.subject.find_all(), [self.main_subject])

    def case_su04(self):
        self.main_subject.description = "Object-oriented analysis, design and programming in Java"
        self.subject.save(self.main_subject)
        self.assertEqual(self.subject.find_by_id(self.main_subject.subject_id), self.main_subject)

    def case_su05(self):
        temporary = self.subject.save(Subject(subject_code="TEMP", subject_name="Temporary", units=1))
        self.subject.delete(temporary.subject_id)
        self.assertIsNone(self.subject.find_by_id(temporary.subject_id))

    def dependent_subject(self):
        self.reject("class CSPC103-A", self.subject.delete, self.main_subject.subject_id)

    def case_cl01(self):
        self.main_class = self.offering.save(ClassOffering(
            class_code="CSPC103-A", subject_id=self.main_subject.subject_id, teacher_id="T-1001",
            section="A", school_year="2026-2027", semester="1st",
            schedule="MWF 9:00–10:00", room="CS-201"))
        saved = self.offering.find_by_id(self.main_class.class_id)
        self.assertEqual((saved.subject_id, saved.teacher_id, saved.section, saved.school_year,
                          saved.semester, saved.schedule, saved.room),
                         (self.main_subject.subject_id, "T-1001", "A", "2026-2027", "1st",
                          "MWF 9:00–10:00", "CS-201"))

    def case_cl02(self):
        for field in ("teacher_id", "subject_id", "school_year", "semester"):
            values = dict(class_code="TEMP", teacher_id="T-1001", subject_id=self.main_subject.subject_id,
                          section="A", school_year="2026-2027", semester="1st")
            values[field] = ""
            self.reject("required", self.offering.save, ClassOffering(**values))

    def case_cl03(self):
        saved = [c for c in self.offering.find_all() if c.teacher_id == "T-1001"]
        self.assertEqual(len(saved), 1)
        self.assertEqual(saved[0].class_id, self.main_class.class_id)
        self.assertEqual((saved[0].subject_code, saved[0].subject_name),
                         ("CSPC 103", "Object Oriented Programming"))

    def case_cl04(self):
        saved = self.offering.find_by_id(self.main_class.class_id)
        saved.room, saved.schedule = "CS-202", "TTh 1:00–2:30"
        self.offering.save(saved)
        reopened = self.offering.find_by_id(saved.class_id)
        self.assertEqual((reopened.room, reopened.schedule), (saved.room, saved.schedule))

    def case_cl05(self):
        self.reject("enrollment", self.offering.delete, self.main_class.class_id)

    def case_en01(self):
        self.enrollment_list = [self.enroll(number, self.main_class.class_id)
                                for number in ("2026-0001", "2026-0002", "2026-0003")]
        self.assertEqual(len(self.rows("enrollments")), 3)
        for saved in self.enrollment_list:
            self.assertEqual((saved.class_id, saved.enroll_date, saved.status),
                             (self.main_class.class_id, date.today(), "Enrolled"))

    def rejected_enrollment(self, number, message):
        before = self.snapshot()
        success, text, saved = self.enrollment.enroll_student(number, self.main_class.class_id)
        self.assertFalse(success)
        self.assertIn(message, text)
        self.assertIsNone(saved)
        self.assertEqual(self.snapshot(), before)

    def case_en02(self):
        self.rejected_enrollment("2026-0001", "already enrolled")

    def case_en03(self):
        self.rejected_enrollment("2026-9999", "does not exist")

    def case_en04(self):
        saved = self.enrollment.get_class_enrollments(self.main_class.class_id)
        self.assertEqual({(e.student_id, e.status) for e in saved},
                         {(e.student_id, "Enrolled") for e in self.enrollment_list})

    def case_en05(self):
        saved = self.enrollment_list[1]
        before = self.rows("grade_component_scores")
        for status in ("Dropped", "Enrolled"):
            self.enrollment.update_status(saved.enrollment_id, status)
            reopened = self.enrollment.get_student_enrollments(saved.student_id)
            self.assertEqual(reopened[0].status, status)
            self.assertEqual(self.rows("grade_component_scores"), before)

    def case_en06(self):
        self.add_student("2026-0098", "Carlo", "Mendoza", "BSIT", 1)
        self.removed_enrollment = self.enroll("2026-0098", self.main_class.class_id)
        self.enrollment.remove_enrollment(self.removed_enrollment.enrollment_id)
        self.assertEqual(self.enrollment.get_student_enrollments("2026-0098"), [])
        self.assertIsNotNone(self.student.find_by_id("2026-0098"))

    def dependent_enrollment(self):
        self.reject("scores", self.enrollment.remove_enrollment, self.enrollment_list[0].enrollment_id)

    def case_gp01(self):
        self.period_list = [self.configuration.add_period(name, order, "2026-2027", "1st")
                            for name, order in [("Midterm", 1), ("Finals", 2)]]
        self.assertEqual(self.configuration.get_periods(), self.period_list)

    def case_gc01(self):
        self.component_list = []
        for period, prefix in zip(self.period_list, ["Midterm", "Final"]):
            for suffix, kind, maximum in [("Quiz", "Quiz", 50),
                                          ("Laboratory/Project", "Laboratory", 100),
                                          ("Examination", "Exam", 100)]:
                saved = self.configuration.add_component(GradeComponent(
                    period_id=period.period_id, name=prefix + " " + suffix, type=kind, max_score=maximum))
                self.component_list.append(saved)
        self.assertEqual(len(self.configuration.get_components()), 6)

    def case_gw01(self):
        for index in (0, 1):
            self.set_weights(self.main_class.class_id, index, [20, 30, 50])
        self.assertEqual(len(self.configuration.get_weights(self.main_class.class_id)), 6)

    def case_gw02(self):
        self.reject("100", self.set_weights, self.main_class.class_id, 0, [20, 30, 40])

    def case_gw03(self):
        for values in ([-20, 30, 90], ["", 30, 70]):
            self.reject(".+", self.set_weights, self.main_class.class_id, 0, values)

    def case_gc02(self):
        saved = self.configuration.get_class_components(self.main_class.class_id)
        self.assertEqual({(c.component_id, c.period_id, c.name, c.max_score) for c in saved},
                         {(c.component_id, c.period_id, c.name, c.max_score) for c in self.component_list})
        self.assertEqual({w.component_id: w.percentage for w in
                          self.configuration.get_weights(self.main_class.class_id)},
                         dict(zip([c.component_id for c in self.component_list], [20, 30, 50] * 2)))

    def case_gc03(self):
        self.reject("scores", self.configuration.delete_component, self.component_list[0].component_id)

    def case_sc01(self):
        for enrollment, values in zip(self.enrollment_list, RAW_SCORES):
            for index, value in enumerate(values):
                self.save_score(enrollment.enrollment_id, index, value)
        self.assertEqual(len(self.rows("grade_component_scores")), 18)
        self.check_scores(RAW_SCORES)

    def case_sc02(self):
        self.reject(".+", self.save_score, self.enrollment_list[0].enrollment_id, 0, 55)

    def case_sc03(self):
        self.reject(".+", self.save_score, self.enrollment_list[0].enrollment_id, 0, -5)

    def case_sc04(self):
        self.reject("enrolled", self.save_score, self.removed_enrollment.enrollment_id, 0, 20)

    def check_scores(self, expected):
        for enrollment, values in zip(self.enrollment_list, expected):
            saved = [s for s, normalized in self.score.get_scores(enrollment.enrollment_id)]
            self.assertEqual({s.component_id: s.score for s in saved},
                             dict(zip([c.component_id for c in self.component_list], values)))
            self.assertTrue(all(s.date_recorded == date.today() for s in saved))

    def case_sc05(self):
        self.make_services()
        self.check_scores(RAW_SCORES)

    def case_sc06(self):
        before = self.scores.find_by_enrollment_and_component(
            self.enrollment_list[0].enrollment_id, self.component_list[2].component_id)
        saved = self.save_score(self.enrollment_list[0].enrollment_id, 2, 75)
        self.assertEqual(saved.score_id, before.score_id)
        self.assertEqual(len(self.rows("grade_component_scores")), 18)
        grade = self.grading.generate_and_save_grade(saved.enrollment_id, self.main_class.class_id,
                                                     changed_by="checklist-tester")
        self.assertAlmostEqual(grade.midterm_grade, 80.50, delta=0.01)

    def case_sc07(self):
        enrollment_id = self.enrollment_list[2].enrollment_id
        self.grading.generate_and_save_grade(enrollment_id, self.main_class.class_id)
        saved = self.scores.find_by_enrollment_and_component(enrollment_id, self.component_list[3].component_id)
        self.score.delete(saved.score_id, changed_by="checklist-tester")
        incomplete = self.grades.find_by_enrollment(enrollment_id)
        self.assertEqual((incomplete.finals_grade, incomplete.overall_grade, incomplete.final_equiv,
                          incomplete.remarks), (None, None, None, "Incomplete"))
        self.save_score(enrollment_id, 3, 48)
        self.assertAlmostEqual(self.grades.find_by_enrollment(enrollment_id).finals_grade, 93.70, delta=0.01)

    def case_gr01(self):
        self.grading.bulk_compute_class_grades(self.main_class.class_id, changed_by="checklist-tester")
        for grade, expected in zip(self.class_grades(), EXPECTED):
            self.assertAlmostEqual(grade.midterm_grade, expected[0], delta=0.01)
            self.assertEqual(grade.midterm_equiv, expected[3])

    def case_gr02(self):
        self.grading.bulk_compute_class_grades(self.main_class.class_id, changed_by="checklist-tester")
        for grade, expected in zip(self.class_grades(), EXPECTED):
            self.assertAlmostEqual(grade.finals_grade, expected[1], delta=0.01)
            self.assertEqual(GradeCalculator.to_grade_point(grade.finals_grade),
                             {83.5: 2.25, 65.5: 5.0, 93.7: 1.5}[expected[1]])
            self.assertAlmostEqual(grade.overall_grade, expected[2], delta=0.01)
            self.assertEqual((grade.final_equiv, grade.remarks), expected[4:])

    def case_gr03(self):
        raw_before = self.rows("grade_component_scores")
        ids_before = [g.grade_id for g in self.class_grades()]
        self.set_weights(self.main_class.class_id, 0, [30, 30, 40])
        self.grading.bulk_compute_class_grades(self.main_class.class_id, changed_by="checklist-tester")
        for grade, midterm, overall, expected in zip(self.class_grades(), [81, 52, 100],
                                                    [82.5, 60.1, 96.22], EXPECTED):
            self.assertAlmostEqual(grade.midterm_grade, midterm, delta=0.01)
            self.assertAlmostEqual(grade.overall_grade, overall, delta=0.01)
            self.assertEqual((grade.midterm_equiv, grade.final_equiv, grade.remarks), expected[3:])
        self.assertEqual([g.grade_id for g in self.class_grades()], ids_before)
        self.assertEqual(len(self.rows("grades")), 3)
        self.assertEqual(self.rows("grade_component_scores"), raw_before)

    def case_gr04(self):
        logs = self.audit.find_all()
        for table in ("GRADE_COMPONENT_SCORE", "GRADE_PERCENTAGE", "GRADE"):
            changed = [log for log in logs if log.table_name == table and log.action == "UPDATE"]
            self.assertTrue(changed, table)
            for log in changed:
                self.assertTrue(log.record_id)
                self.assertEqual(log.changed_by, "checklist-tester")
                self.assertIsNotNone(log.changed_at)
                self.assertNotEqual(json.loads(log.old_value), json.loads(log.new_value))
        correction = [log for log in logs if log.table_name == "GRADE_COMPONENT_SCORE"
                      and log.action == "UPDATE"]
        self.assertTrue(any(json.loads(log.old_value)["score"] == 57 and
                            json.loads(log.new_value)["score"] == 75 for log in correction))

    def report_setup(self):
        self.teacher.add(Teacher(teacher_id="T-1002", first_name="Jose", last_name="Ramos",
                                 department="Physical Education Department"))
        subject = self.subject.save(Subject(subject_code="PATHFIT 3",
            subject_name="Physical Activity Towards Health and Fitness 3", units=2))
        offering = self.offering.save(ClassOffering(class_code="PATHFIT3-A", subject_id=subject.subject_id,
            teacher_id="T-1002", section="A", school_year="2026-2027", semester="1st",
            schedule="TTh 3:00–5:00", room="Gym"))
        enrollment = self.enroll("2026-0001", offering.class_id)
        for index in (0, 1):
            self.set_weights(offering.class_id, index, [20, 30, 50])
        for index, value in enumerate([45, 90, 90, 45, 90, 90]):
            self.save_score(enrollment.enrollment_id, index, value)
        self.grading.bulk_compute_class_grades(offering.class_id, changed_by="checklist-tester")
        grade = self.grades.find_by_enrollment(enrollment.enrollment_id)
        self.assertEqual((grade.midterm_grade, grade.finals_grade, grade.overall_grade,
                          grade.midterm_equiv, grade.final_equiv, grade.remarks),
                         (90, 90, 90, 1.75, 1.75, "Passed"))

    def case_rp01(self):
        report = self.report.generate_class_list_report(self.main_class.class_id)
        self.assertEqual(report["columns"], ["No.", "Student Name", "Course"])
        self.assertEqual(report["rows"], [[1, "Dela Cruz, Juan", "BSCS"],
            [2, "Garcia, Ana", "BSCS"], [3, "Reyes, Pedro", "BSCS"]])
        header = "\n".join(report["header"])
        for text in ("CSPC 103", "Object Oriented Programming", "Section: A",
                     "Maria Santos, Information Technology Department", "1st Semester", "2026-2027",
                     "TTh 1:00–2:30", "CS-202"):
            self.assertIn(text, header)

    def case_rp02(self):
        report = self.report.generate_grade_sheet_report(self.main_class.class_id)
        self.assertEqual(report["columns"], ["No.", "Student", "Course", "MG", "FG"])
        self.assertEqual(report["rows"], [[1, "Dela Cruz, Juan", "BSCS", "2.50", "2.25"],
            [2, "Garcia, Ana", "BSCS", "1.00", "1.25"], [3, "Reyes, Pedro", "BSCS", "5.00", "5.00"]])

    def case_rp03(self):
        report = self.report.generate_student_grade_report("2026-0001")
        self.assertEqual(report["columns"], ["No.", "Subject Code", "Description", "Teacher", "Units", "F Grade"])
        self.assertEqual(report["rows"], [
            [1, "CSPC 103", "Object Oriented Programming", "Maria Santos", 3, "2.25"],
            [2, "PATHFIT 3", "Physical Activity Towards Health and Fitness 3", "Jose Ramos", 2, "1.75"]])
        self.assertIn("Student Name: Dela Cruz, Juan    Course: BSCS    Year: 2nd", report["header"])

    def case_rp04(self):
        report = self.report.generate_student_grade_report("2026-0001")
        self.assertEqual((report["total_units"], report["subject_count"], report["gwa"]), (5, 2, "2.05"))
        self.assertEqual(report["summary"], ["Total Units: 5    No. of Subjects: 2",
                                             "Grade Weighted Average: 2.05"])

    def case_ps01(self):
        before = self.snapshot()
        report = self.report.generate_grade_sheet_report(self.main_class.class_id)
        # services use fresh connections; rebuild them to check persisted data
        self.make_services()
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.report.generate_grade_sheet_report(self.main_class.class_id), report)

    def case_ps02(self):
        self.add_student("2026-0004", "Kevin", "O'Brien", "BSIT", 1)
        self.assertEqual(self.student.find_by_id("2026-0004").last_name, "O'Brien")
        before = self.snapshot()
        self.assertEqual(self.student.search("' OR '1'='1"), [])
        self.assertEqual([s.student_id for s in self.student.search("O'Brien")], ["2026-0004"])
        self.assertEqual(self.snapshot(), before)

    def test_checklist_in_order(self):
        # postponed checks follow the dependency instructions in the checklist
        cases = [
            ("ST-01", self.case_st01), ("ST-02", self.case_st02), ("ST-03", self.case_st03),
            ("ST-04", self.case_st04), ("ST-05", self.case_st05), ("ST-06", self.case_st06),
            ("TE-01", self.case_te01), ("TE-02", self.case_te02), ("TE-03", self.case_te03),
            ("TE-04", self.case_te04), ("SU-01", self.case_su01), ("SU-02", self.case_su02),
            ("SU-03", self.case_su03), ("SU-04", self.case_su04), ("SU-05", self.case_su05),
            ("CL-01", self.case_cl01), ("TE-05", self.case_te05), ("SU-05", self.dependent_subject),
            ("CL-02", self.case_cl02), ("CL-03", self.case_cl03), ("CL-04", self.case_cl04),
            ("EN-01", self.case_en01), ("ST-07", self.case_st07), ("CL-05", self.case_cl05),
            ("EN-02", self.case_en02), ("EN-03", self.case_en03), ("EN-04", self.case_en04),
            ("EN-05", self.case_en05), ("EN-06", self.case_en06), ("GP-01", self.case_gp01),
            ("GC-01", self.case_gc01), ("GW-01", self.case_gw01), ("GW-02", self.case_gw02),
            ("GW-03", self.case_gw03), ("GC-02", self.case_gc02), ("SC-01", self.case_sc01),
            ("GC-03", self.case_gc03), ("EN-06", self.dependent_enrollment),
            ("SC-02", self.case_sc02), ("SC-03", self.case_sc03), ("SC-04", self.case_sc04),
            ("SC-05", self.case_sc05), ("SC-06", self.case_sc06), ("SC-07", self.case_sc07),
            ("GR-01", self.case_gr01), ("GR-02", self.case_gr02), ("GR-03", self.case_gr03),
            ("GR-04", self.case_gr04), ("report setup", self.report_setup),
            ("RP-01", self.case_rp01), ("RP-02", self.case_rp02), ("RP-03", self.case_rp03),
            ("RP-04", self.case_rp04), ("PS-01", self.case_ps01), ("PS-02", self.case_ps02),
        ]
        for case_id, action in cases:
            with self.subTest(case_id=case_id, phase=action.__name__):
                action()
        for table, expected in ROW_COUNTS.items():
            with self.subTest(case_id="Appendix row counts", table=table):
                self.assertEqual(len(self.rows(table)), expected)
        with self.subTest(case_id="Appendix row counts", table="audit_log"):
            self.assertGreaterEqual(len(self.rows("audit_log")), 7)


if __name__ == "__main__":
    unittest.main()
