from db import get_connection
from repositories import ScoreRepository, EnrollmentRepository, GradeComponentRepository
from repositories import GradePercentageRepository
from services.grade_calculator import GradeCalculator
from services.grading_service import GradingService
from services.validation import number


class ScoreService:
    def __init__(self):
        self.scores = ScoreRepository()
        self.enrollments = EnrollmentRepository()
        self.components = GradeComponentRepository()
        self.weights = GradePercentageRepository()
        self.grading = GradingService()

    def get_scores(self, enrollment_id):
        return [(score, GradeCalculator.normalize_score(score.score, score.max_score))
                for score in self.scores.find_by_enrollment(enrollment_id)]

    def save(self, score, changed_by=None):
        enrollment = self.enrollments.find_by_id(score.enrollment_id) if score.enrollment_id else None
        if not enrollment or enrollment.status.lower() != "enrolled":
            raise ValueError("Scores can only be entered for an enrolled student.")
        component = self.components.find_by_id(score.component_id) if score.component_id else None
        if not component:
            raise ValueError("Select an existing component.")
        class_weights = self.weights.find_by_offering(enrollment.class_id)
        if not any(weight.component_id == str(score.component_id) for weight in class_weights):
            raise ValueError("That component is not configured for this class.")
        score.score = number(score.score, "Score")
        GradeCalculator.normalize_score(score.score, component.max_score)
        conn = get_connection()
        try:
            saved = self.scores.save(score, changed_by=changed_by, connection=conn)
            self.refresh_grade(enrollment, changed_by=changed_by, connection=conn)
            conn.commit()
            return saved
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def delete(self, score_id, changed_by=None):
        score = self.scores.find_by_id(score_id)
        if not score:
            raise ValueError("Score not found. Refresh the list.")
        enrollment = self.enrollments.find_by_id(score.enrollment_id)
        conn = get_connection()
        try:
            self.scores.delete_by_id(score_id, changed_by=changed_by, connection=conn)
            self.refresh_grade(enrollment, changed_by=changed_by, connection=conn)
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def refresh_grade(self, enrollment, changed_by=None, connection=None):
        # the grade must see the score changes before the transaction commits;
        # saving it here keeps the grade viewable even before anyone presses Compute
        self.grading.generate_and_save_grade(
            enrollment.enrollment_id, enrollment.class_id, changed_by=changed_by, connection=connection,
        )
