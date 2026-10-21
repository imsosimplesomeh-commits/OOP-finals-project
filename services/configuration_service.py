from models import GradingPeriod
from repositories import ClassRepository, GradingPeriodRepository, GradeComponentRepository
from repositories import GradePercentageRepository, ScoreRepository
from services.grade_calculator import GradeCalculator
from services.validation import required, positive_integer, number


class ConfigurationService:
    def __init__(self):
        self.classes = ClassRepository()
        self.periods = GradingPeriodRepository()
        self.components = GradeComponentRepository()
        self.weights = GradePercentageRepository()
        self.scores = ScoreRepository()

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

    def delete_component(self, component_id, changed_by=None):
        # scores are never deleted silently; weights of an unscored component go with it
        component = self.components.find_by_id(component_id)
        if not component:
            raise ValueError("Component not found. Refresh the list.")
        scored = [score for score in self.scores.find_all() if score.component_id == str(component_id)]
        if scored:
            raise ValueError(f"Cannot delete {component.name} because {len(scored)} score(s) depend on it.")
        return self.components.delete_by_id(component_id, changed_by=changed_by)

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
