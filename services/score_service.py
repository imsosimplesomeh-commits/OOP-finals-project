from repositories import ScoreRepository, EnrollmentRepository, GradeComponentRepository
from repositories import GradePercentageRepository, GradeRepository, GradingPeriodRepository
from services.grade_calculator import GradeCalculator
from services.grading_service import GradingService
from services.validation import number


class ScoreService:
    def __init__(self, score_repo=None, enrollment_repo=None, component_repo=None,
                 percentage_repo=None, grade_repo=None, period_repo=None):
        self.scores = score_repo or ScoreRepository()
        self.enrollments = enrollment_repo or EnrollmentRepository()
        self.components = component_repo or GradeComponentRepository()
        self.weights = percentage_repo or GradePercentageRepository()
        self.grades = grade_repo or GradeRepository()
        self.periods = period_repo or GradingPeriodRepository()
        self.grading = GradingService(self.enrollments, self.weights, self.components,
                                      self.scores, self.grades, self.periods)

    def get_scores(self, enrollment_id):
        return [(score, GradeCalculator.normalize_score(score.score, score.max_score))
                for score in self.scores.find_by_enrollment(enrollment_id)]

    def save(self, score):
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
        saved = self.scores.save(score)
        self.refresh_grade(enrollment)
        return saved

    def delete(self, score_id):
        score = self.scores.find_by_id(score_id)
        if not score:
            raise ValueError("Score not found. Refresh the list.")
        enrollment = self.enrollments.find_by_id(score.enrollment_id)
        self.scores.delete_by_id(score_id)
        self.refresh_grade(enrollment)

    def refresh_grade(self, enrollment):
        # keep an existing grade consistent when a score is corrected or removed
        if self.grades.find_by_enrollment(enrollment.enrollment_id):
            self.grading.generate_and_save_grade(enrollment.enrollment_id, enrollment.class_id)
