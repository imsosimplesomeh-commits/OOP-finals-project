# test_grade_calculator.py - grade math checked against the numbers in SPEC.md
# Run from the project folder: python -m unittest discover tests

import unittest
from unittest.mock import patch

from models import Grade
from services import grade_calculator
from services.grade_calculator import (
    GradeCalculator as GC, COMPLETE, INCOMPLETE, NOT_SET, MIDTERM_ONLY,
)

MAX_SCORES = (50, 100, 100)
WEIGHTS = (20, 30, 50)
RECALC_MIDTERM_WEIGHTS = (30, 30, 40)

# raw scores from SPEC.md: (midterm quiz, lab, exam), (final quiz, lab, exam)
SCORES = {
    "Juan": ((40, 90, 75), (45, 85, 80)),
    "Pedro": ((20, 60, 55), (30, 70, 65)),
    "Ana": ((50, 100, 100), (48, 95, 92)),
}


def items(scores, weights=WEIGHTS):
    return list(zip(scores, MAX_SCORES, weights))


def period(scores, weights=WEIGHTS):
    return GC.period_result(items(scores, weights))


class TestCheckpointGrades(unittest.TestCase):
    def assertGrade(self, actual, expected):
        # SPEC accepts differences of +/- 0.01 from rounding
        self.assertAlmostEqual(actual, expected, delta=0.01)

    def test_worked_example_juan_midterm(self):
        # (40/50 x 100) x 20% + 90 x 30% + 75 x 50% = 16 + 27 + 37.5
        self.assertGrade(GC.compute_period_grade(items(SCORES["Juan"][0])), 80.50)

    def test_expected_grades_with_20_30_50(self):
        expected = {"Juan": (80.50, 83.50, 82.30), "Pedro": (53.50, 65.50, 60.70), "Ana": (100.00, 93.70, 96.22)}
        for name, (midterm, finals, overall) in expected.items():
            with self.subTest(name):
                mid = period(SCORES[name][0])
                fin = period(SCORES[name][1])
                self.assertEqual(mid[0], COMPLETE)
                self.assertGrade(mid[1], midterm)
                self.assertGrade(fin[1], finals)
                total, status = GC.overall_result(mid, fin)
                self.assertGrade(total, overall)
                self.assertEqual(status, COMPLETE)

    def test_expected_grade_points_and_remarks(self):
        expected = {"Juan": (2.50, 2.25, 2.25, "Passed"), "Pedro": (5.00, 5.00, 5.00, "Failed"),
                    "Ana": (1.00, 1.50, 1.25, "Passed")}
        for name, (mid_point, fin_point, overall_point, remarks) in expected.items():
            with self.subTest(name):
                mid = period(SCORES[name][0])
                fin = period(SCORES[name][1])
                total, _ = GC.overall_result(mid, fin)
                self.assertEqual(GC.to_grade_point(mid[1]), mid_point)
                self.assertEqual(GC.to_grade_point(fin[1]), fin_point)
                self.assertEqual(GC.to_grade_point(total), overall_point)
                self.assertEqual(GC.remarks_for(GC.to_grade_point(total)), remarks)

    def test_recalculation_with_30_30_40(self):
        expected = {"Juan": (81.00, 2.50, 82.50, 2.25), "Pedro": (52.00, 5.00, 60.10, 5.00),
                    "Ana": (100.00, 1.00, 96.22, 1.25)}
        for name, (midterm, mid_point, overall, overall_point) in expected.items():
            with self.subTest(name):
                mid = period(SCORES[name][0], RECALC_MIDTERM_WEIGHTS)
                total, _ = GC.overall_result(mid, period(SCORES[name][1]))
                self.assertGrade(mid[1], midterm)
                self.assertEqual(GC.to_grade_point(mid[1]), mid_point)
                self.assertGrade(total, overall)
                self.assertEqual(GC.to_grade_point(total), overall_point)

    def test_pathfit_example(self):
        mid = period((45, 90, 90))
        fin = period((45, 90, 90))
        total, status = GC.overall_result(mid, fin)
        self.assertGrade(total, 90.00)
        self.assertEqual(GC.to_grade_point(total), 1.75)
        self.assertEqual(GC.remarks_for(1.75), "Passed")
        self.assertEqual(status, COMPLETE)


class TestGradeScale(unittest.TestCase):
    def test_boundaries_use_unrounded_percentage(self):
        cases = [(100, 1.00), (97.00, 1.00), (96.99, 1.25), (94.00, 1.25), (93.99, 1.50),
                 (82.00, 2.25), (81.99, 2.50), (75.00, 3.00), (74.99, 5.00), (0, 5.00)]
        for percentage, point in cases:
            with self.subTest(percentage):
                self.assertEqual(GC.to_grade_point(percentage), point)

    def test_value_just_below_97_is_not_rounded_up(self):
        self.assertEqual(GC.to_grade_point(96.995), 1.25)

    def test_remarks_follow_grade_point(self):
        self.assertEqual(GC.remarks_for(3.00), "Passed")
        self.assertEqual(GC.remarks_for(5.00), "Failed")
        self.assertEqual(GC.remarks_for(None), "Incomplete")


class TestValidation(unittest.TestCase):
    def test_weights_must_total_100(self):
        self.assertTrue(GC.validate_weights([20, 30, 50])[0])
        self.assertFalse(GC.validate_weights([20, 30, 40])[0])

    def test_negative_or_blank_weight_rejected(self):
        self.assertFalse(GC.validate_weights([-20, 70, 50])[0])
        self.assertFalse(GC.validate_weights([None, 50, 50])[0])

    def test_score_above_max_or_negative_rejected(self):
        with self.assertRaises(ValueError):
            GC.normalize_score(55, 50)
        with self.assertRaises(ValueError):
            GC.normalize_score(-5, 50)


class TestPeriodStates(unittest.TestCase):
    def test_period_without_components_is_not_set(self):
        self.assertEqual(GC.period_result([]), (NOT_SET, None))

    def test_missing_score_is_incomplete_not_zero(self):
        # SC-07: Ana's Final Quiz deleted
        self.assertEqual(GC.period_result(items((None, 95, 92))), (INCOMPLETE, None))

    def test_missing_or_bad_weight_is_incomplete(self):
        self.assertEqual(GC.period_result(items((45, 85, 80), (20, 30, None))), (INCOMPLETE, None))
        self.assertEqual(GC.period_result(items((45, 85, 80), (20, 30, 40))), (INCOMPLETE, None))

    def test_midterm_only_overall_when_finals_missing(self):
        mid = period(SCORES["Juan"][0])
        for finals in [(NOT_SET, None), (INCOMPLETE, None)]:
            with self.subTest(finals[0]):
                total, status = GC.overall_result(mid, finals)
                self.assertAlmostEqual(total, 80.50, delta=0.01)
                self.assertEqual(status, MIDTERM_ONLY)
                self.assertEqual(GC.remarks_for(GC.to_grade_point(total)), "Passed")

    def test_midterm_only_can_be_switched_off(self):
        with patch.object(grade_calculator, "SHOW_MIDTERM_ONLY_OVERALL", False):
            self.assertEqual(GC.overall_result(period(SCORES["Juan"][0]), (NOT_SET, None)), (None, INCOMPLETE))

    def test_incomplete_midterm_gives_no_overall(self):
        self.assertEqual(GC.overall_result((INCOMPLETE, None), period(SCORES["Juan"][1])), (None, INCOMPLETE))

    def test_status_of_saved_grade(self):
        self.assertEqual(GC.status_of(Grade(midterm_grade=81, finals_grade=83.5, overall_grade=82.5)), COMPLETE)
        self.assertEqual(GC.status_of(Grade(midterm_grade=81, overall_grade=81)), MIDTERM_ONLY)
        self.assertEqual(GC.status_of(Grade()), INCOMPLETE)
        self.assertEqual(GC.status_of(None), INCOMPLETE)

    def test_formula_text_comes_from_constants(self):
        self.assertEqual(GC.formula_text(), "Overall = Midterm 40% + Finals 60%")


class TestWeightedAverage(unittest.TestCase):
    def test_rp04_gwa_is_2_05(self):
        # (2.25 x 3 + 1.75 x 2) / 5 = 10.25 / 5
        self.assertEqual(GC.weighted_average([(2.25, 3), (1.75, 2)]), 2.05)

    def test_gwa_rounds_half_up(self):
        self.assertEqual(GC.weighted_average([(2.25, 1), (2.00, 1)]), 2.13)


if __name__ == "__main__":
    unittest.main()
