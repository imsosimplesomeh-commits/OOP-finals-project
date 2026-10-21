# grade_calculator.py - all grading math for the finals project
# rule: forms and repositories never compute grades, they call this file only.

from decimal import Decimal, ROUND_HALF_UP

# (lowest percentage in the band, grade point) - checked from highest to lowest
# this is the scale from the CRUD test case document, kept in ONE place only
GRADE_SCALE = [
    (97.0, 1.00),
    (94.0, 1.25),
    (91.0, 1.50),
    (88.0, 1.75),
    (85.0, 2.00),
    (82.0, 2.25),
    (79.0, 2.50),
    (76.0, 2.75),
    (75.0, 3.00),
]
FAILING_POINT = 5.00
PASSING_POINT = 3.00

# Overall = Midterm x 40% + Finals x 60%; the UI reads these, never its own numbers
MIDTERM_WEIGHT = 40
FINALS_WEIGHT = 60

# when Finals is missing, the Midterm percent is shown as a provisional overall
SHOW_MIDTERM_ONLY_OVERALL = True

# period and grade states
COMPLETE = "Complete"
INCOMPLETE = "Incomplete"
NOT_SET = "N/A"
MIDTERM_ONLY = "Midterm only"


def round_half_up(value, places=2):
    # normal school rounding (2.345 -> 2.35), python's round() can surprise you
    step = Decimal(1).scaleb(-places)
    return float(Decimal(str(value)).quantize(step, rounding=ROUND_HALF_UP))


class GradeCalculator:
    @staticmethod
    def normalize_score(score, max_score):
        # raw score -> percentage (0 to 100)
        if max_score <= 0:
            raise ValueError("Max score must be greater than 0.")
        if score < 0:
            raise ValueError("Score cannot be negative.")
        if score > max_score:
            raise ValueError(f"Score {score:g} is above the maximum of {max_score:g}.")
        return score / max_score * 100

    @staticmethod
    def validate_weights(weights):
        # weights = the percentages of ONE grading period, they must total 100
        if not weights:
            return False, "No weights entered."
        for w in weights:
            if w is None:
                return False, "Weight cannot be blank."
            if w < 0:
                return False, "Weight cannot be negative."
        total = sum(weights)
        if abs(total - 100) > 0.001:
            return False, f"Weights total {total:g}%, they must total 100%."
        return True, "OK"

    @classmethod
    def compute_period_grade(cls, items):
        # items = list of (score, max_score, weight) for one period
        # returns the percentage, or None if a score is still missing (incomplete)
        if not items:
            return None
        total = 0.0
        for score, max_score, weight in items:
            if score is None:
                return None  # never treat a missing score as 0
            total += cls.normalize_score(score, max_score) * weight / 100
        # round(.., 6) only removes float noise; we do NOT round to 2 decimals here
        # because 96.995 must still land in the 1.25 band
        return round(total, 6)

    @classmethod
    def period_result(cls, items):
        # items = (score, max_score, weight) for every component of one period
        # returns (state, percentage); a missing score or weight is never treated as 0
        if not items:
            return NOT_SET, None
        valid, _ = cls.validate_weights([weight for _, _, weight in items])
        if not valid or any(score is None for score, _, _ in items):
            return INCOMPLETE, None
        return COMPLETE, cls.compute_period_grade(items)

    @classmethod
    def overall_result(cls, midterm, finals):
        # midterm and finals are (state, percentage) pairs; returns (overall, status)
        midterm_state, midterm_grade = midterm
        finals_state, finals_grade = finals
        if midterm_state != COMPLETE:
            return None, INCOMPLETE
        if finals_state == COMPLETE:
            return cls.compute_overall_grade(midterm_grade, finals_grade), COMPLETE
        if SHOW_MIDTERM_ONLY_OVERALL:
            return midterm_grade, MIDTERM_ONLY
        return None, INCOMPLETE

    @staticmethod
    def status_of(grade):
        # status of a saved grade row, so screens and reports agree with the database
        if grade is None or grade.overall_grade is None:
            return INCOMPLETE
        if grade.finals_grade is None:
            return MIDTERM_ONLY
        return COMPLETE

    @staticmethod
    def formula_text():
        return f"Overall = Midterm {MIDTERM_WEIGHT}% + Finals {FINALS_WEIGHT}%"

    @staticmethod
    def compute_overall_grade(midterm, finals, midterm_weight=MIDTERM_WEIGHT, finals_weight=FINALS_WEIGHT):
        if midterm is None or finals is None:
            return None
        return round((midterm * midterm_weight + finals * finals_weight)
                     / (midterm_weight + finals_weight), 6)

    @staticmethod
    def to_grade_point(percentage):
        # use the UNROUNDED percentage: 96.99 -> 1.25, 74.99 -> 5.00
        if percentage is None:
            return None
        for lowest, point in GRADE_SCALE:
            if percentage >= lowest:
                return point
        return FAILING_POINT

    @staticmethod
    def remarks_for(grade_point):
        if grade_point is None:
            return "Incomplete"
        return "Passed" if grade_point <= PASSING_POINT else "Failed"

    @staticmethod
    def weighted_average(rows):
        # rows = list of (grade_point, units); GWA = sum(point * units) / total units
        rows = [(p, u) for p, u in rows if p is not None]
        total_units = sum(u for _, u in rows)
        if total_units == 0:
            return None
        return round_half_up(sum(p * u for p, u in rows) / total_units, 2)
