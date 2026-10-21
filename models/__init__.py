# models/__init__.py - domain models matching the uml class diagram

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional


@dataclass
class Student:
    student_id: Optional[str] = None
    first_name: str = ""
    last_name: str = ""
    email: Optional[str] = None
    program: Optional[str] = None
    year_level: Optional[int] = None
    status: str = "Active"

    @property
    def full_name(self) -> str:
        return f"{self.last_name}, {self.first_name}".strip(", ")


@dataclass
class Teacher:
    teacher_id: Optional[str] = None
    first_name: str = ""
    last_name: str = ""
    email: Optional[str] = None
    department: Optional[str] = None
    status: str = "Active"

    @property
    def full_name(self) -> str:
        return f"{self.last_name}, {self.first_name}".strip(", ")


@dataclass
class Subject:
    subject_id: Optional[str] = None
    subject_code: str = ""
    subject_name: str = ""
    description: Optional[str] = None
    units: int = 3


@dataclass
class ClassOffering:
    class_id: Optional[str] = None
    class_code: str = ""
    schedule: Optional[str] = None
    section: Optional[str] = None
    school_year: str = ""
    semester: str = ""
    room: Optional[str] = None
    subject_id: str = ""
    teacher_id: str = ""

    # extra info from joins
    subject_code: Optional[str] = None
    subject_name: Optional[str] = None
    teacher_name: Optional[str] = None


@dataclass
class GradingPeriod:
    period_id: Optional[str] = None
    name: str = ""
    period_order: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    school_year: str = ""
    semester: str = ""


@dataclass
class GradePercentage:
    percentage_id: Optional[str] = None
    class_id: str = ""
    component_id: str = ""
    percentage: float = 0.0


@dataclass
class GradeComponent:
    component_id: Optional[str] = None
    period_id: str = ""
    name: str = ""
    type: str = ""
    max_score: float = 100.0
    description: Optional[str] = None

    # extra info from joins
    period_name: Optional[str] = None
    percentage_value: Optional[float] = None


@dataclass
class Enrollment:
    enrollment_id: Optional[str] = None
    student_id: str = ""
    class_id: str = ""
    enroll_date: Optional[date] = None
    status: str = "Enrolled"

    # extra info from joins
    student_name: Optional[str] = None
    student_email: Optional[str] = None
    student_program: Optional[str] = None
    class_code: Optional[str] = None
    subject_name: Optional[str] = None


@dataclass
class GradeComponentScore:
    score_id: Optional[str] = None
    enrollment_id: str = ""
    component_id: str = ""
    score: float = 0.0
    remarks: Optional[str] = None
    date_recorded: Optional[date] = None

    component_name: Optional[str] = None
    max_score: Optional[float] = None
    component_type: Optional[str] = None


@dataclass
class Grade:
    grade_id: Optional[str] = None
    enrollment_id: str = ""
    overall_grade: Optional[float] = None
    midterm_equiv: Optional[float] = None
    final_equiv: Optional[float] = None
    remarks: Optional[str] = None
    date_encoded: Optional[date] = None
    midterm_grade: Optional[float] = None
    finals_grade: Optional[float] = None


@dataclass
class AuditLog:
    log_id: Optional[str] = None
    table_name: str = ""
    record_id: str = ""
    action: str = ""
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    changed_by: str = ""
    changed_at: Optional[datetime] = None
