# grading_service.py - service handling grade computations and persistence

from datetime import date
from db import get_connection
from models import Grade
from repositories.enrollment_repository import EnrollmentRepository
from repositories.grade_component_repository import GradeComponentRepository
from repositories.grade_percentage_repository import GradePercentageRepository
from repositories.grade_repository import GradeRepository
from repositories.grading_period_repository import GradingPeriodRepository
from repositories.score_repository import ScoreRepository
from services.grade_calculator import GradeCalculator
from services.validation import number


class GradingService:
    def __init__(self):
        self.enrollment_repo = EnrollmentRepository()
        self.percentage_repo = GradePercentageRepository()
        self.component_repo = GradeComponentRepository()
        self.score_repo = ScoreRepository()
        self.grade_repo = GradeRepository()
        self.period_repo = GradingPeriodRepository()
        self.calculator = GradeCalculator()

    def get_class_percentage_weights(self, offering_id):
        percentages = self.percentage_repo.find_by_offering(offering_id)
        return {str(p.component_id): p.percentage for p in percentages}

    def _load_period_components(self, offering_id):
        weights = self.get_class_percentage_weights(offering_id)
        components = self.component_repo.find_by_offering(offering_id)
        periods = {str(p.period_id): p for p in self.period_repo.find_all()}
        groups = {1: [], 2: []}
        for component in components:
            period = periods.get(str(component.period_id))
            if period is None or period.period_order not in groups:
                raise ValueError("Components must belong to Midterm or Finals.")
            weight = weights.get(str(component.component_id))
            groups[period.period_order].append((component, weight))
        for order, name in ((1, "Midterm"), (2, "Finals")):
            valid, message = self.calculator.validate_weights([w for _, w in groups[order]])
            if not valid:
                raise ValueError(f"{name}: {message}")
        return groups

    def validate_percentages(self, offering_id):
        try:
            self._load_period_components(offering_id)
        except ValueError as error:
            return False, str(error)
        return True, "Valid percentage configuration."

    def compute_student_grades(self, enrollment_id, offering_id, midterm_weight=40.0, finals_weight=60.0, connection=None):
        self.validate_overall_weights(midterm_weight, finals_weight)
        enrollment = self.enrollment_repo.find_by_id(enrollment_id)
        if enrollment is None or str(enrollment.class_id) != str(offering_id):
            raise ValueError("Select a student enrolled in this class.")
        groups = self._load_period_components(offering_id)
        scores = {str(s.component_id): s.score for s in self.score_repo.find_by_enrollment(enrollment_id, connection=connection)}
        period_grades = {}
        for order in (1, 2):
            items = []
            for component, weight in groups[order]:
                # an absent score must stay incomplete
                score = scores.get(str(component.component_id))
                items.append((score, component.max_score, weight))
            period_grades[order] = self.calculator.compute_period_grade(items)
        midterm = period_grades[1]
        finals = period_grades[2]
        overall = self.calculator.compute_overall_grade(midterm, finals)
        # convert before the database rounds percentages to two decimals
        midterm_equiv = self.calculator.to_grade_point(midterm)
        final_equiv = self.calculator.to_grade_point(overall)
        return Grade(
            enrollment_id=enrollment_id,
            midterm_grade=midterm,
            finals_grade=finals,
            overall_grade=overall,
            midterm_equiv=midterm_equiv,
            final_equiv=final_equiv,
            remarks=self.calculator.remarks_for(final_equiv),
            date_encoded=date.today(),
        )

    def save_computed_grade(self, grade, changed_by=None, connection=None):
        return self.grade_repo.save(grade, changed_by=changed_by, connection=connection)

    def generate_and_save_grade(self, enrollment_id, offering_id, midterm_weight=40.0, finals_weight=60.0,
                                changed_by=None, connection=None):
        grade = self.compute_student_grades(enrollment_id, offering_id, midterm_weight, finals_weight, connection)
        return self.save_computed_grade(grade, changed_by=changed_by, connection=connection)

    def bulk_compute_class_grades(self, offering_id, midterm_weight=40.0, finals_weight=60.0, changed_by=None):
        enrollments = self.enrollment_repo.find_by_offering(offering_id)
        conn = get_connection()
        try:
            saved_grades = []
            for enrollment in enrollments:
                grade = self.generate_and_save_grade(
                    enrollment.enrollment_id, offering_id, midterm_weight, finals_weight,
                    changed_by=changed_by, connection=conn,
                )
                saved_grades.append(grade)
            conn.commit()
            return saved_grades
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def get_class_grades(self, class_id):
        return self.grade_repo.find_by_offering(class_id)

    def validate_overall_weights(self, midterm, finals):
        midterm = number(midterm, "Midterm weight")
        finals = number(finals, "Finals weight")
        if midterm != 40 or finals != 60:
            raise ValueError("Overall weights must be 40% Midterm and 60% Finals.")
        return midterm, finals
