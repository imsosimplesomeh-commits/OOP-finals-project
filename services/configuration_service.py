from models import GradingPeriod
from repositories import ClassRepository, GradingPeriodRepository, GradeComponentRepository
from repositories import GradePercentageRepository, ScoreRepository
from services.grade_calculator import GradeCalculator
from services.validation import required, positive_integer, number


class ConfigurationService:
    def __init__(self, class_repo=None, period_repo=None, component_repo=None,
                 percentage_repo=None, score_repo=None):
        self.classes = class_repo or ClassRepository()
        self.periods = period_repo or GradingPeriodRepository()
        self.components = component_repo or GradeComponentRepository()
        self.weights = percentage_repo or GradePercentageRepository()
        self.scores = score_repo or ScoreRepository()

    def get_periods(self):
        return self.periods.find_all()

    def get_components(self):
        return self.components.find_all()

    def get_class_components(self, class_id):
        return self.components.find_by_offering(class_id)

    def get_weights(self, class_id):
        return self.weights.find_by_offering(class_id)

    def add_period(self, name, order, school_year="", semester=""):
        name = required(name, "Period name")
        order = positive_integer(order, "Period order")
        if (order, name.lower()) not in ((1, "midterm"), (2, "finals")):
            raise ValueError("Use Midterm with order 1 or Finals with order 2.")
        for period in self.periods.find_all():
            if period.period_order == order or period.name.lower() == name.lower():
                raise ValueError("That grading period already exists.")
        return self.periods.save(GradingPeriod(name=name.capitalize(), period_order=order,
                                              school_year=school_year, semester=semester))

    def add_component(self, component):
        component.period_id = required(component.period_id, "Grading period")
        component.name = required(component.name, "Component name")
        component.type = required(component.type, "Component category")
        component.max_score = number(component.max_score, "Maximum score")
        if component.max_score <= 0 or component.max_score > 9999.99:
            raise ValueError("Maximum score must be greater than 0 and at most 9999.99.")
        if not self.periods.find_by_id(component.period_id):
            raise ValueError("The selected grading period does not exist.")
        if component.component_id:
            raise ValueError("Use a new component without an existing ID.")
        for existing in self.components.find_all():
            if existing.period_id == component.period_id and existing.name.lower() == component.name.lower():
                raise ValueError("That component already exists in this period.")
        return self.components.save(component)

    def delete_component(self, component_id):
        if not self.components.find_by_id(component_id):
            raise ValueError("Component not found. Refresh the list.")
        if any(score.component_id == str(component_id) for score in self.scores.find_all()):
            raise ValueError("Cannot delete this component because scores depend on it.")
        if any(weight.component_id == str(component_id) for weight in self.weights.find_all()):
            raise ValueError("Cannot delete this component because grading weights depend on it.")
        return self.components.delete_by_id(component_id)

    def save_weights(self, class_id, period_id, values, changed_by=None):
        if not class_id or not self.classes.find_by_id(class_id):
            raise ValueError("Select an existing class first.")
        if not period_id or not self.periods.find_by_id(period_id):
            raise ValueError("Select an existing grading period.")
        expected = {c.component_id for c in self.components.find_all() if c.period_id == str(period_id)}
        ids = [str(component_id) for component_id, _ in values]
        if not expected or set(ids) != expected or len(ids) != len(expected):
            raise ValueError("Enter one weight for every component in this period.")
        parsed = []
        for component_id, value in values:
            weight = number(value, "Weight")
            if weight != round(weight, 2):
                raise ValueError("Weights can have at most two decimal places.")
            parsed.append((str(component_id), weight))
        valid, message = GradeCalculator.validate_weights([weight for _, weight in parsed])
        if not valid:
            raise ValueError(message)
        self.weights.save_period(class_id, parsed, changed_by=changed_by)
        return "Period weights saved."

    def weight_summary(self, class_id):
        components = {c.component_id: c for c in self.components.find_all()}
        periods = self.periods.find_all()
        totals = {p.period_id: 0 for p in periods}
        for weight in self.weights.find_by_offering(class_id):
            totals[components[weight.component_id].period_id] += weight.percentage
        return " | ".join(f"{p.name}: {totals[p.period_id]:.2f}%" for p in periods)
