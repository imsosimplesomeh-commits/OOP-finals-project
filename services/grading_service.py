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

MIDTERM_ORDER = 1
FINALS_ORDER = 2


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
        # every component of each period, with this class's weight (None when not set yet)
        weights = self.get_class_percentage_weights(offering_id)
        periods = {str(p.period_id): p.period_order for p in self.period_repo.find_all()}
        groups = {MIDTERM_ORDER: [], FINALS_ORDER: []}
        for component in self.component_repo.find_all():
            order = periods.get(str(component.period_id))
            if order in groups:
                groups[order].append((component, weights.get(str(component.component_id))))
        return groups

    def period_has_components(self, period_order):
        # a period without components is "not set" (N/A), not incomplete
        periods = {str(p.period_id) for p in self.period_repo.find_all() if p.period_order == period_order}
        return any(str(c.period_id) in periods for c in self.component_repo.find_all())

    def compute_student_grades(self, enrollment_id, offering_id, connection=None):
        enrollment = self.enrollment_repo.find_by_id(enrollment_id)
        if enrollment is None or str(enrollment.class_id) != str(offering_id):
            raise ValueError("Select a student enrolled in this class.")
        groups = self._load_period_components(offering_id)
        scores = {str(s.component_id): s.score for s in self.score_repo.find_by_enrollment(enrollment_id, connection=connection)}
        results = {}
        for order, components in groups.items():
            items = [(scores.get(str(c.component_id)), c.max_score, weight) for c, weight in components]
            results[order] = self.calculator.period_result(items)
        overall, _ = self.calculator.overall_result(results[MIDTERM_ORDER], results[FINALS_ORDER])
        midterm = results[MIDTERM_ORDER][1]
        # convert before the database rounds percentages to two decimals
        final_equiv = self.calculator.to_grade_point(overall)
        return Grade(
            enrollment_id=enrollment_id,
            midterm_grade=midterm,
            finals_grade=results[FINALS_ORDER][1],
            overall_grade=overall,
            midterm_equiv=self.calculator.to_grade_point(midterm),
            final_equiv=final_equiv,
            remarks=self.calculator.remarks_for(final_equiv),
            date_encoded=date.today(),
        )

    def save_computed_grade(self, grade, changed_by=None, connection=None):
        return self.grade_repo.save(grade, changed_by=changed_by, connection=connection)

    def generate_and_save_grade(self, enrollment_id, offering_id, changed_by=None, connection=None):
        grade = self.compute_student_grades(enrollment_id, offering_id, connection)
        return self.save_computed_grade(grade, changed_by=changed_by, connection=connection)

    def bulk_compute_class_grades(self, offering_id, changed_by=None):
        # one transaction: either every student's grade is saved or none is
        enrollments = self.enrollment_repo.find_by_offering(offering_id)
        conn = get_connection()
        try:
            saved_grades = [
                self.generate_and_save_grade(e.enrollment_id, offering_id, changed_by=changed_by, connection=conn)
                for e in enrollments
            ]
            conn.commit()
            return saved_grades
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def get_class_grades(self, class_id):
        return self.grade_repo.find_by_offering(class_id)
