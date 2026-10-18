# test_system.py - Unit and Integration Tests for CSPC 103 Finals Project

import os
import unittest
from uuid import uuid4
from unittest.mock import patch

import psycopg2
from psycopg2 import sql

import db
from models import Student, Teacher, Subject, ClassOffering
from services.grade_calculator import GradeCalculator
from repositories import (
    StudentRepository, TeacherRepository, SubjectRepository, ClassRepository,
)


class TestGradeCalculator(unittest.TestCase):
    def test_normalize_score_standard(self):
        # 45 out of 50 should be 90%
        norm = GradeCalculator.normalize_score(45.0, 50.0)
        self.assertEqual(norm, 90.0)

    def test_normalize_score_zero(self):
        norm = GradeCalculator.normalize_score(0.0, 100.0)
        self.assertEqual(norm, 0.0)

    def test_normalize_score_negative_raises_error(self):
        with self.assertRaises(ValueError):
            GradeCalculator.normalize_score(-5.0, 100.0)

    def test_normalize_score_exceeding_max_raises_error(self):
        with self.assertRaises(ValueError):
            GradeCalculator.normalize_score(105.0, 100.0)

    def test_normalize_score_zero_max_raises_error(self):
        with self.assertRaises(ValueError):
            GradeCalculator.normalize_score(50.0, 0.0)

    def test_compute_period_grade_single_component(self):
        items = [(40.0, 50.0, 50.0), (90.0, 100.0, 50.0)]
        self.assertEqual(GradeCalculator.compute_period_grade(items), 85.0)

    def test_compute_period_grade_weighted(self):
        items = [(40.0, 50.0, 20.0), (90.0, 100.0, 30.0), (84.0, 100.0, 50.0)]
        self.assertEqual(GradeCalculator.compute_period_grade(items), 85.0)

    def test_compute_final_grade(self):
        final = GradeCalculator.compute_overall_grade(85.0, 90.0)
        self.assertEqual(final, 88.0)

    def test_remarks_and_rating(self):
        self.assertEqual(GradeCalculator.remarks_for(GradeCalculator.to_grade_point(75.0)), "Passed")
        for percentage, point in [
            (75, 3.00), (77, 2.75), (80, 2.50), (83, 2.25), (86, 2.00),
            (89, 1.75), (92, 1.50), (95, 1.25), (98, 1.00),
            (74.9, 5.00), (74.99, 5.00), (65, 5.00), (0, 5.00),
        ]:
            with self.subTest(percentage=percentage):
                self.assertEqual(GradeCalculator.to_grade_point(percentage), point)
        self.assertEqual(GradeCalculator.remarks_for(GradeCalculator.to_grade_point(74.9)), "Failed")


class TestRepositoriesAndServices(unittest.TestCase):
    def setUp(self):
        if not os.environ.get("PGDATABASE_TEST"):
            self.skipTest("set PGDATABASE_TEST to run database tests")
        self.config = dict(db.DB_CONFIG, dbname=os.environ["PGDATABASE_TEST"])
        if self.config["dbname"] == db.DB_CONFIG["dbname"]:
            raise ValueError("PGDATABASE_TEST must name a separate test database.")
        self.schema = "system_test_" + uuid4().hex
        conn = psycopg2.connect(**self.config)
        try:
            with conn, conn.cursor() as cur:
                cur.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(self.schema)))
        finally:
            conn.close()
        self.addCleanup(self.remove_schema)
        with patch("db.get_connection", self.connect):
            db.init_db()
        self.student_repo = StudentRepository(self.connect)
        self.teacher_repo = TeacherRepository(self.connect)
        self.subject_repo = SubjectRepository(self.connect)
        self.class_repo = ClassRepository(self.connect)

    def connect(self):
        return psycopg2.connect(**self.config, options="-c search_path=" + self.schema)

    def remove_schema(self):
        # remove only this test's schema, including after a failed assertion
        conn = psycopg2.connect(**self.config)
        try:
            with conn, conn.cursor() as cur:
                cur.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(self.schema)))
        finally:
            conn.close()

    def test_student_retrieval(self):
        self.student_repo.save(Student(
            student_id="2026-0001", first_name="Juan", last_name="Dela Cruz",
            program="BSCS", year_level=2,
        ))
        students = self.student_repo.find_all()
        self.assertEqual(len(students), 1)
        self.assertEqual(students[0].student_id, "2026-0001")
        found = self.student_repo.find_by_id("2026-0001")
        self.assertIsNotNone(found)
        self.assertEqual((found.first_name, found.last_name), ("Juan", "Dela Cruz"))
        self.assertEqual((found.program, found.year_level), ("BSCS", 2))

    def test_class_offering_retrieval(self):
        teacher = self.teacher_repo.save(Teacher(
            teacher_id="T-1001", first_name="Maria", last_name="Santos",
            department="Computer Studies Department",
        ))
        subject = self.subject_repo.save(Subject(
            subject_code="CSPC 103", subject_name="Object Oriented Programming", units=3,
        ))
        saved = self.class_repo.save(ClassOffering(
            class_code="CSPC103-A", subject_id=subject.subject_id,
            teacher_id=teacher.teacher_id, section="A",
            school_year="2026-2027", semester="1st",
        ))
        offerings = self.class_repo.find_all()
        self.assertEqual(len(offerings), 1)
        self.assertEqual(offerings[0].class_id, saved.class_id)
        found = self.class_repo.find_by_id(saved.class_id)
        self.assertIsNotNone(found)
        self.assertEqual(found.subject_code, "CSPC 103")
        self.assertEqual(found.subject_name, "Object Oriented Programming")
        self.assertEqual(found.teacher_name, "Santos, Maria")
        self.assertEqual((found.subject_id, found.teacher_id), (subject.subject_id, "T-1001"))


if __name__ == "__main__":
    unittest.main()
