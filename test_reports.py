import re
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path
from unittest.mock import Mock

from models import Student, Teacher, Subject, ClassOffering, Enrollment, Grade
from repositories.enrollment_repository import EnrollmentRepository
from repositories.grade_repository import GradeRepository
from repositories.report_repository import ReportRepository
from services.report_service import ReportService
import test_system
from ui.report_document import export_pdf, report_text


class TestSavedReports(unittest.TestCase):
    setUp = test_system.TestRepositoriesAndServices.setUp
    connect = test_system.TestRepositoriesAndServices.connect
    remove_schema = test_system.TestRepositoriesAndServices.remove_schema

    def make_reports(self):
        self.teacher_repo.save(Teacher(teacher_id="T-1001", first_name="Maria", last_name="Santos",
                                      department="Information Technology Department"))
        subject = self.subject_repo.save(Subject(subject_code="CSPC 103", subject_name="Object Oriented Programming", units=3))
        offering = self.class_repo.save(ClassOffering(
            class_code="CSPC103-A", subject_id=subject.subject_id, teacher_id="T-1001",
            section="A", school_year="2026-2027", semester="1st", schedule="TTh 1:00-2:30", room="CS-202"))
        enrollments = EnrollmentRepository(self.connect)
        grades = GradeRepository(self.connect)
        for number, first, last, mg, fg in [
            (2, "Pedro", "Reyes", 5, 5), (1, "Juan", "Dela Cruz", 2.5, 2.25), (3, "Ana", "Garcia", 1, 1.25)
        ]:
            student_id = f"2026-{number:04d}"
            self.student_repo.save(Student(student_id=student_id, first_name=first, last_name=last, program="BSCS", year_level=2))
            enrollment = enrollments.save(Enrollment(student_id=student_id, class_id=offering.class_id))
            # stored equivalents deliberately differ from the percentages to catch recalculation
            grades.save(Grade(enrollment_id=enrollment.enrollment_id, midterm_grade=0, overall_grade=0,
                              midterm_equiv=mg, final_equiv=fg, remarks="Passed"))
        self.teacher_repo.save(Teacher(teacher_id="T-1002", first_name="Jose", last_name="Ramos", department="Physical Education Department"))
        subject = self.subject_repo.save(Subject(subject_code="PATHFIT 3", subject_name="Physical Activity Towards Health and Fitness 3", units=2))
        other = self.class_repo.save(ClassOffering(class_code="PATHFIT3-A", subject_id=subject.subject_id,
            teacher_id="T-1002", section="A", school_year="2026-2027", semester="1st"))
        enrollment = enrollments.save(Enrollment(student_id="2026-0001", class_id=other.class_id))
        grades.save(Grade(enrollment_id=enrollment.enrollment_id, midterm_equiv=1.75, final_equiv=1.75))
        return ReportService(ReportRepository(self.connect), self.student_repo), offering

    def test_rp01_rp02_saved_class_reports(self):
        service, offering = self.make_reports()
        report = service.generate_class_list_report(offering.class_id)
        self.assertEqual(report["columns"], ["No.", "Student Name", "Course"])
        self.assertEqual(report["rows"], [[1, "Dela Cruz, Juan", "BSCS"], [2, "Garcia, Ana", "BSCS"], [3, "Reyes, Pedro", "BSCS"]])
        self.assertIn("Maria Santos, Information Technology Department", report_text(report))
        self.assertIn("TTh 1:00-2:30, CS-202", report_text(report))
        report = service.generate_grade_sheet_report(offering.class_id)
        self.assertEqual(report["columns"], ["No.", "Student", "Course", "MG", "FG"])
        self.assertEqual([r[-2:] for r in report["rows"]], [["2.50", "2.25"], ["1.00", "1.25"], ["5.00", "5.00"]])

    def test_rp03_rp04_saved_units_and_gwa(self):
        service, _ = self.make_reports()
        report = service.generate_student_grade_report("2026-0001")
        self.assertEqual(report["columns"], ["No.", "Subject Code", "Description", "Teacher", "Units", "F Grade"])
        self.assertEqual([r[1:] for r in report["rows"]], [
            ["CSPC 103", "Object Oriented Programming", "Maria Santos", 3, "2.25"],
            ["PATHFIT 3", "Physical Activity Towards Health and Fitness 3", "Jose Ramos", 2, "1.75"]])
        self.assertEqual((report["total_units"], report["subject_count"], report["gwa"]), (5, 2, "2.05"))
        self.assertIn("Year: 2nd", report_text(report))


class TestReportEdges(unittest.TestCase):
    def setUp(self):
        self.repo = Mock()
        self.students = Mock()
        self.students.find_by_id.return_value = Student(student_id="2026-0001", first_name="Juan", last_name="Dela Cruz", program="BSCS", year_level=2)
        self.service = ReportService(self.repo, self.students)
        self.subjects = [dict(subject_code="CSPC 103", subject_name="OOP", teacher_name="Maria Santos",
                              units=3, final_equiv=Decimal("2.25"), school_year="2026-2027", semester="1st")]

    def test_incomplete_grade_keeps_units_and_blocks_partial_gwa(self):
        self.repo.find_student_subjects.return_value = self.subjects + [dict(self.subjects[0], units=2, final_equiv=None)]
        report = self.service.generate_student_grade_report("2026-0001")
        self.assertEqual(report["rows"][1][-1], "Incomplete")
        self.assertEqual((report["total_units"], report["subject_count"], report["gwa"]), (5, 2, "Incomplete"))
        self.repo.find_class_header.return_value = dict(class_code="A", subject_code="CSPC 103", subject_name="OOP",
            section="A", teacher_name="Maria Santos", department="IT", school_year="2026-2027", semester="1st", schedule=None, room=None)
        self.repo.find_class_students.return_value = [dict(student_name="Dela Cruz, Juan", program="BSCS", midterm_equiv=None, final_equiv=None)]
        self.assertEqual(self.service.generate_grade_sheet_report(1)["rows"][0][-2:], ["Incomplete", "Incomplete"])

    def test_empty_and_missing_records(self):
        self.repo.find_student_subjects.return_value = []
        report = self.service.generate_student_grade_report("2026-0001")
        self.assertEqual((report["rows"], report["total_units"], report["gwa"]), ([], 0, "N/A"))
        self.students.find_by_id.return_value = None
        with self.assertRaises(ValueError):
            self.service.generate_student_grade_report("missing")
        self.repo.find_class_header.return_value = None
        with self.assertRaises(ValueError):
            self.service.generate_class_list_report(999)

    def test_different_terms_are_not_combined(self):
        self.repo.find_student_subjects.return_value = self.subjects + [dict(self.subjects[0], school_year="2025-2026")]
        self.assertEqual(self.service.generate_student_grade_report("2026-0001")["subject_count"], 1)
        report = self.service.generate_student_grade_report("2026-0001", "2025-2026", "1st")
        self.assertIn("2025-2026", report_text(report))

    def test_pdf_exports_all_layouts_and_multiple_pages(self):
        self.repo.find_student_subjects.return_value = self.subjects
        student = self.service.generate_student_grade_report("2026-0001")
        with tempfile.TemporaryDirectory() as folder:
            for columns in (["No.", "Student Name", "Course"], ["No.", "Student", "Course", "MG", "FG"], student["columns"]):
                report = dict(student, columns=columns, rows=[[1] + ["O'Brien <A&B> " * 3] * (len(columns) - 1)] * 100)
                path = Path(folder) / 'report.pdf'
                export_pdf(report, path)
                content = path.read_bytes()
                self.assertTrue(content.startswith(b"%PDF-"))
                self.assertTrue(content.rstrip().endswith(b"%%EOF"))
                self.assertGreater(len(re.findall(rb"/Type\s*/Page\b", content)), 1)


if __name__ == "__main__":
    unittest.main()

