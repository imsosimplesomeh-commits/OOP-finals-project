import os
import json
import unittest
from uuid import uuid4
from unittest.mock import patch

import psycopg2
from psycopg2 import sql

import db
from models import (
    Student, Teacher, Subject, ClassOffering, Enrollment, GradingPeriod,
    GradeComponent, GradePercentage, GradeComponentScore,
)
from repositories import (
    AuditRepository, StudentRepository, TeacherRepository, SubjectRepository, ClassRepository,
    EnrollmentRepository, GradingPeriodRepository, GradeComponentRepository,
    GradePercentageRepository, ScoreRepository, GradeRepository,
)


from services.score_service import ScoreService
from services.configuration_service import ConfigurationService


class TestAuditLog(unittest.TestCase):
    def setUp(self):
        if not os.environ.get("PGDATABASE_TEST"):
            self.skipTest("set PGDATABASE_TEST to run database tests")
        self.config = dict(db.DB_CONFIG, dbname=os.environ["PGDATABASE_TEST"])
        if self.config["dbname"] == db.DB_CONFIG["dbname"]:
            raise ValueError("PGDATABASE_TEST must name a separate test database.")
        self.schema = "audit_test_" + uuid4().hex
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

    def add_audit_records(self):
        self.add_records()
        self.audit = AuditRepository(self.connect)
        self.config_service = ConfigurationService(self.classes, self.periods, self.components, self.weights, self.scores)
        self.score_service = ScoreService(self.scores, self.enrollments, self.components, self.weights, self.grades, self.periods)
        self.grading = self.score_service.grading
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
            self.weights.save(GradePercentage(class_id=self.offering.class_id,
                                             component_id=component.component_id, percentage=weight))
            self.grade_components.append(component)
        self.saved_scores = []
        for component, value in zip(self.grade_components, [40, 90, 57, 45, 85, 80]):
            self.saved_scores.append(self.scores.save(GradeComponentScore(
                enrollment_id=self.enrollment.enrollment_id, component_id=component.component_id, score=value,
            )))
        self.grade = self.grading.generate_and_save_grade(self.enrollment.enrollment_id, self.offering.class_id)

    def snapshot(self):
        return (
            self.query("SELECT * FROM grade_component_scores ORDER BY score_id"),
            self.query("SELECT * FROM grade_percentages ORDER BY percentage_id"),
            self.query("SELECT * FROM grades ORDER BY grade_id"),
            self.query("SELECT * FROM audit_log ORDER BY log_id"),
        )

    def reject_actor(self):
        self.query("ALTER TABLE audit_log ADD CONSTRAINT reject_actor CHECK (changed_by <> %s)", ("fail",))

    def reject_grade_audit(self):
        self.query(
            "ALTER TABLE audit_log ADD CONSTRAINT reject_grade_audit "
            "CHECK (table_name <> %s OR changed_by <> %s)", ("GRADE", "fail"),
        )

    def test_score_correction_delete_and_reentry_record_real_values(self):
        self.add_audit_records()
        score = self.saved_scores[2]
        score.score = 75
        self.score_service.save(score, changed_by="tester")
        updates = [row for row in self.audit.find_all()
                   if row.table_name == "GRADE_COMPONENT_SCORE" and row.record_id == score.score_id]
        latest = updates[-1]
        self.assertEqual((latest.action, latest.changed_by), ("UPDATE", "tester"))
        self.assertEqual(json.loads(latest.old_value)["score"], 57)
        self.assertEqual(json.loads(latest.new_value)["score"], 75)
        self.assertIsNotNone(latest.changed_at)
        grade = self.grades.find_by_enrollment(self.enrollment.enrollment_id)
        self.assertEqual((grade.midterm_grade, grade.overall_grade), (80.5, 82.3))
        quiz = self.saved_scores[3]
        self.score_service.delete(quiz.score_id, changed_by="tester")
        deleted = [row for row in self.audit.find_all() if row.table_name == "GRADE_COMPONENT_SCORE"][-1]
        self.assertEqual((deleted.action, deleted.record_id), ("DELETE", quiz.score_id))
        self.assertEqual(json.loads(deleted.old_value)["score"], 45)
        self.assertIsNone(deleted.new_value)
        incomplete = self.grades.find_by_enrollment(self.enrollment.enrollment_id)
        self.assertEqual((incomplete.finals_grade, incomplete.final_equiv, incomplete.remarks), (None, None, "Incomplete"))
        reentered = self.score_service.save(GradeComponentScore(
            enrollment_id=self.enrollment.enrollment_id, component_id=quiz.component_id, score=45,
        ), changed_by="tester")
        inserted = [row for row in self.audit.find_all() if row.table_name == "GRADE_COMPONENT_SCORE"][-1]
        self.assertEqual((inserted.action, inserted.record_id), ("INSERT", reentered.score_id))
        self.assertIsNone(inserted.old_value)
        self.assertEqual(json.loads(inserted.new_value)["score"], 45)
        self.assertEqual(self.grades.find_by_enrollment(self.enrollment.enrollment_id).overall_grade, 82.3)

    def test_recalculation_audits_changed_weights_and_grade_points(self):
        self.add_audit_records()
        score = self.saved_scores[2]
        score.score = 75
        self.score_service.save(score, changed_by="tester")
        raw_before = self.query("SELECT * FROM grade_component_scores ORDER BY score_id")
        ids = [component.component_id for component in self.grade_components[:3]]
        self.config_service.save_weights(self.offering.class_id, self.period.period_id,
                                         list(zip(ids, [30, 30, 40])), changed_by="tester")
        self.grading.bulk_compute_class_grades(self.offering.class_id, changed_by="tester")
        weight_updates = [row for row in self.audit.find_all()
                          if row.table_name == "GRADE_PERCENTAGE" and row.action == "UPDATE"]
        self.assertEqual(len(weight_updates), 2)
        self.assertEqual([(json.loads(row.old_value)["percentage"], json.loads(row.new_value)["percentage"])
                          for row in weight_updates], [(20, 30), (50, 40)])
        updated = [row for row in self.audit.find_all() if row.table_name == "GRADE"][-1]
        old, new = json.loads(updated.old_value), json.loads(updated.new_value)
        self.assertEqual((old["midterm_grade"], old["overall_grade"]), (80.5, 82.3))
        self.assertEqual((new["midterm_grade"], new["overall_grade"], new["midterm_equiv"], new["final_equiv"]),
                         (81, 82.5, 2.5, 2.25))
        self.assertEqual(updated.changed_by, "tester")
        self.assertEqual(self.query("SELECT * FROM grade_component_scores ORDER BY score_id"), raw_before)
        self.assertEqual(len(self.grades.find_all()), 1)

    def test_repository_deletes_log_each_table(self):
        self.add_audit_records()
        self.scores.delete_by_id(self.saved_scores[0].score_id, changed_by="tester")
        self.weights.delete_by_id(self.weight.percentage_id, changed_by="tester")
        self.grades.delete_by_id(self.grade.grade_id, changed_by="tester")
        deleted = [row for row in self.audit.find_all() if row.action == "DELETE"]
        self.assertEqual({row.table_name for row in deleted}, {"GRADE_COMPONENT_SCORE", "GRADE_PERCENTAGE", "GRADE"})
        self.assertTrue(all(row.old_value is not None and row.new_value is None for row in deleted))
        self.assertTrue(all(row.changed_by == "tester" for row in deleted))
        before = self.snapshot()
        self.assertFalse(self.scores.delete_by_id(self.saved_scores[0].score_id))
        self.assertFalse(self.weights.delete_by_id(self.weight.percentage_id))
        self.assertFalse(self.grades.delete_by_id(self.grade.grade_id))
        self.assertEqual(self.snapshot(), before)

    def test_default_actor_uses_current_account(self):
        self.add_audit_records()
        self.saved_scores[0].score = 41
        with patch("repositories.audit_repository.getpass.getuser", return_value="demo-user"):
            self.scores.save(self.saved_scores[0])
        self.assertEqual(self.audit.find_all()[-1].changed_by, "demo-user")

    def test_score_insert_is_rolled_back_when_audit_fails(self):
        self.add_audit_records()
        self.scores.delete_by_id(self.saved_scores[0].score_id)
        self.reject_actor()
        before = self.snapshot()
        with self.assertRaises(psycopg2.errors.CheckViolation):
            self.score_service.save(GradeComponentScore(
                enrollment_id=self.enrollment.enrollment_id,
                component_id=self.saved_scores[0].component_id, score=40,
            ), changed_by="fail")
        self.assertEqual(self.snapshot(), before)

    def test_score_update_is_rolled_back_when_audit_fails(self):
        self.add_audit_records()
        self.reject_actor()
        before = self.snapshot()
        self.saved_scores[2].score = 75
        with self.assertRaises(psycopg2.errors.CheckViolation):
            self.score_service.save(self.saved_scores[2], changed_by="fail")
        self.assertEqual(self.snapshot(), before)

    def test_grade_audit_failure_rolls_back_score_and_both_logs(self):
        self.add_audit_records()
        self.reject_grade_audit()
        before = self.snapshot()
        self.saved_scores[2].score = 75
        with self.assertRaises(psycopg2.errors.CheckViolation):
            self.score_service.save(self.saved_scores[2], changed_by="fail")
        self.assertEqual(self.snapshot(), before)

    def test_grade_audit_failure_rolls_back_score_deletion(self):
        self.add_audit_records()
        self.reject_grade_audit()
        before = self.snapshot()
        with self.assertRaises(psycopg2.errors.CheckViolation):
            self.score_service.delete(self.saved_scores[3].score_id, changed_by="fail")
        self.assertEqual(self.snapshot(), before)

    def test_later_weight_audit_failure_rolls_back_whole_period(self):
        self.add_audit_records()
        exam_weight = next(weight for weight in self.weights.find_all()
                           if weight.component_id == self.grade_components[2].component_id)
        self.query(
            "ALTER TABLE audit_log ADD CONSTRAINT reject_weight_audit "
            "CHECK (table_name <> %s OR record_id <> %s OR changed_by <> %s)",
            ("GRADE_PERCENTAGE", exam_weight.percentage_id, "fail"),
        )
        before = self.snapshot()
        ids = [component.component_id for component in self.grade_components[:3]]
        with self.assertRaises(psycopg2.errors.CheckViolation):
            self.config_service.save_weights(self.offering.class_id, self.period.period_id,
                                             list(zip(ids, [30, 30, 40])), changed_by="fail")
        self.assertEqual(self.snapshot(), before)

    def test_direct_deletes_roll_back_when_audit_fails(self):
        self.add_audit_records()
        self.reject_actor()
        before = self.snapshot()
        for repo, record_id in [(self.scores, self.saved_scores[0].score_id),
                                (self.weights, self.weight.percentage_id), (self.grades, self.grade.grade_id)]:
            with self.subTest(repository=type(repo).__name__):
                with self.assertRaises(psycopg2.errors.CheckViolation):
                    repo.delete_by_id(record_id, changed_by="fail")
                self.assertEqual(self.snapshot(), before)

    def test_direct_grade_and_weight_updates_roll_back_when_audit_fails(self):
        self.add_audit_records()
        self.reject_actor()
        before = self.snapshot()
        self.grade.overall_grade = 50
        self.weight.percentage = 30
        for repo, record in [(self.grades, self.grade), (self.weights, self.weight)]:
            with self.subTest(repository=type(repo).__name__):
                with self.assertRaises(psycopg2.errors.CheckViolation):
                    repo.save(record, changed_by="fail")
                self.assertEqual(self.snapshot(), before)

    def test_bulk_grade_audit_failure_rolls_back_prior_student(self):
        self.add_audit_records()
        self.students.save(Student(student_id="2026-0002", first_name="Zed", last_name="Zulu", program="BSCS", year_level=2))
        enrollment = self.enrollments.save(Enrollment(student_id="2026-0002", class_id=self.offering.class_id))
        for component in self.grade_components:
            self.scores.save(GradeComponentScore(enrollment_id=enrollment.enrollment_id,
                                                 component_id=component.component_id, score=40))
        ids = [component.component_id for component in self.grade_components[:3]]
        self.config_service.save_weights(self.offering.class_id, self.period.period_id, list(zip(ids, [30, 30, 40])))
        self.query(
            "ALTER TABLE audit_log ADD CONSTRAINT reject_second_grade_audit "
            "CHECK (table_name <> %s OR changed_by <> %s OR new_value::jsonb->>'enrollment_id' <> %s)",
            ("GRADE", "fail", enrollment.enrollment_id),
        )
        before = self.snapshot()
        with self.assertRaises(psycopg2.errors.CheckViolation):
            self.grading.bulk_compute_class_grades(self.offering.class_id, changed_by="fail")
        self.assertEqual(self.snapshot(), before)

    def test_unchanged_saves_do_not_add_false_changes(self):
        self.add_audit_records()
        before = self.query("SELECT * FROM audit_log ORDER BY log_id")
        self.score_service.save(self.saved_scores[0], changed_by="tester")
        self.weights.save(self.weight, changed_by="tester")
        self.grades.save(self.grade, changed_by="tester")
        self.assertEqual(self.query("SELECT * FROM audit_log ORDER BY log_id"), before)

