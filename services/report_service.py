from decimal import Decimal

from repositories.report_repository import ReportRepository
from repositories.student_repository import StudentRepository


def grade_text(value):
    return f"{value:.2f}" if value is not None else "Incomplete"


class ReportService:
    def __init__(self, report_repo=None, student_repo=None):
        self.report_repo = report_repo or ReportRepository()
        self.student_repo = student_repo or StudentRepository()

    def _class_report(self, class_id, grade_sheet=False):
        header = self.report_repo.find_class_header(class_id)
        if header is None:
            raise ValueError(f"Class offering '{class_id}' not found.")
        students = self.report_repo.find_class_students(class_id)
        rows = []
        for number, student in enumerate(students, 1):
            row = [number, student["student_name"], student["program"]]
            if grade_sheet:
                row.extend([grade_text(student["midterm_equiv"]), grade_text(student["final_equiv"])])
            rows.append(row)
        teacher = header["teacher_name"]
        if not grade_sheet:
            teacher += f", {header['department']}"
        return {
            "title": "Grade Sheet" if grade_sheet else "Class List",
            "header": [
                f"Subject: {header['subject_code']} - {header['subject_name']}    Section: {header['section'] or 'N/A'}",
                f"Teacher: {teacher}",
                f"Term: {header['semester']} Semester, SY {header['school_year']}",
            ] + ([] if grade_sheet else [f"Schedule / Room: {header['schedule'] or 'N/A'}, {header['room'] or 'N/A'}"]),
            "columns": ["No.", "Student", "Course", "MG", "FG"] if grade_sheet else ["No.", "Student Name", "Course"],
            "rows": rows,
            "summary": [],
        }

    def generate_class_list_report(self, offering_id):
        return self._class_report(offering_id)

    def generate_grade_sheet_report(self, offering_id):
        return self._class_report(offering_id, grade_sheet=True)

    def generate_student_grade_report(self, student_id, school_year=None, semester=None):
        student = self.student_repo.find_by_id(student_id)
        if student is None:
            raise ValueError(f"Student '{student_id}' not found.")
        subjects = self.report_repo.find_student_subjects(student_id)
        # keep one term together so units and averages describe the same term
        if subjects:
            school_year = school_year or subjects[0]["school_year"]
            semester = semester or subjects[0]["semester"]
        subjects = [s for s in subjects if s["school_year"] == school_year and s["semester"] == semester]
        total_units = sum(s["units"] for s in subjects)
        complete = bool(subjects) and all(s["final_equiv"] is not None for s in subjects)
        gwa = None
        if complete and total_units:
            points = sum(Decimal(str(s["final_equiv"])) * s["units"] for s in subjects)
            gwa = points / total_units
        year = student.year_level
        suffix = "th" if year and 10 <= year % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get((year or 0) % 10, "th")
        return {
            "title": "Student Grade",
            "header": [
                f"Student Name: {student.full_name}    Course: {student.program}    Year: {year}{suffix}",
                f"Term: {semester} Semester, SY {school_year}" if subjects else "Term: No enrolled subjects",
            ],
            "columns": ["No.", "Subject Code", "Description", "Teacher", "Units", "F Grade"],
            "rows": [[i, s["subject_code"], s["subject_name"], s["teacher_name"], s["units"], grade_text(s["final_equiv"])]
                     for i, s in enumerate(subjects, 1)],
            "summary": [f"Total Units: {total_units}    No. of Subjects: {len(subjects)}",
                        f"Grade Weighted Average: {grade_text(gwa) if subjects else 'N/A'}"],
            "total_units": total_units,
            "subject_count": len(subjects),
            "gwa": grade_text(gwa) if subjects else "N/A",
        }
