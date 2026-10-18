# test_grade_numbers.py - checks our math against the numbers in Ma'am Brenda's
# CRUD test case document (GR-01 to GR-03, SC-07, RP-04). no database needed.
# run:  python -m unittest tests.test_grade_numbers -v

import unittest
from services.grade_calculator_v2 import GradeCalculator as GC

MID_MAX = [50, 100, 100]
FIN_MAX = [50, 100, 100]

STUDENTS = {
    # name: (mid scores, final scores)
    "Juan": ([40, 90, 75], [45, 85, 80]),
    "Pedro": ([20, 60, 55], [30, 70, 65]),
    "Ana": ([50, 100, 100], [48, 95, 92]),
}
# name: (mid%, fin%, overall%, mid gp, fin gp, overall gp)
EXPECTED = {
    "Juan": (80.50, 83.50, 82.30, 2.50, 2.25, 2.25),
    "Pedro": (53.50, 65.50, 60.70, 5.00, 5.00, 5.00),
    "Ana": (100.00, 93.70, 96.22, 1.00, 1.50, 1.25),
}
# after midterm weights change to 30/30/40: name: (mid%, overall%, mid gp, overall gp)
RECALC = {
    "Juan": (81.00, 82.50, 2.50, 2.25),
    "Pedro": (52.00, 60.10, 5.00, 5.00),
    "Ana": (100.00, 96.22, 1.00, 1.25),
}


def period(scores, maxes, weights):
    return GC.compute_period_grade(list(zip(scores, maxes, weights)))


class TestChecklistNumbers(unittest.TestCase):
    def test_gr01_gr02_original_weights(self):
        for name, (mid_s, fin_s) in STUDENTS.items():
            mid = period(mid_s, MID_MAX, [20, 30, 50])
            fin = period(fin_s, FIN_MAX, [20, 30, 50])
            overall = GC.compute_overall_grade(mid, fin)
            e = EXPECTED[name]
            self.assertAlmostEqual(mid, e[0], delta=0.01, msg=name)
            self.assertAlmostEqual(fin, e[1], delta=0.01, msg=name)
            self.assertAlmostEqual(overall, e[2], delta=0.01, msg=name)
            self.assertEqual(GC.to_grade_point(mid), e[3], name)
            self.assertEqual(GC.to_grade_point(fin), e[4], name)
            self.assertEqual(GC.to_grade_point(overall), e[5], name)

    def test_gr03_recalculation_keeps_raw_scores(self):
        for name, (mid_s, fin_s) in STUDENTS.items():
            mid = period(mid_s, MID_MAX, [30, 30, 40])
            fin = period(fin_s, FIN_MAX, [20, 30, 50])
            overall = GC.compute_overall_grade(mid, fin)
            e = RECALC[name]
            self.assertAlmostEqual(mid, e[0], delta=0.01, msg=name)
            self.assertAlmostEqual(overall, e[1], delta=0.01, msg=name)
            self.assertEqual(GC.to_grade_point(mid), e[2], name)
            self.assertEqual(GC.to_grade_point(overall), e[3], name)

    def test_pathfit_juan(self):
        mid = period([45, 90, 90], MID_MAX, [20, 30, 50])
        fin = period([45, 90, 90], FIN_MAX, [20, 30, 50])
        overall = GC.compute_overall_grade(mid, fin)
        self.assertAlmostEqual(overall, 90.00, delta=0.01)
        self.assertEqual(GC.to_grade_point(overall), 1.75)
        self.assertEqual(GC.remarks_for(1.75), "Passed")

    def test_sc07_missing_score_is_incomplete_not_zero(self):
        fin = period([None, 95, 92], FIN_MAX, [20, 30, 50])
        self.assertIsNone(fin)
        self.assertIsNone(GC.compute_overall_grade(100.0, fin))
        self.assertEqual(GC.remarks_for(GC.to_grade_point(fin)), "Incomplete")

    def test_scale_edges(self):
        self.assertEqual(GC.to_grade_point(96.99), 1.25)
        self.assertEqual(GC.to_grade_point(97.00), 1.00)
        self.assertEqual(GC.to_grade_point(75.00), 3.00)
        self.assertEqual(GC.to_grade_point(74.99), 5.00)
        self.assertEqual(GC.to_grade_point(96.995), 1.25)  # must not round up first

    def test_remarks(self):
        self.assertEqual(GC.remarks_for(3.00), "Passed")
        self.assertEqual(GC.remarks_for(5.00), "Failed")

    def test_rp04_weighted_average(self):
        self.assertEqual(GC.weighted_average([(2.25, 3), (1.75, 2)]), 2.05)
        # the two wrong answers the document warns about
        self.assertNotEqual(GC.weighted_average([(2.25, 3), (1.75, 2)]), 2.00)
        self.assertEqual(GC.weighted_average([]), None)

    def test_gw02_gw03_weight_validation(self):
        self.assertTrue(GC.validate_weights([20, 30, 50])[0])
        self.assertFalse(GC.validate_weights([20, 30, 40])[0])   # total 90
        self.assertFalse(GC.validate_weights([-10, 60, 50])[0])  # negative
        self.assertFalse(GC.validate_weights([20, None, 50])[0])  # blank

    def test_sc02_sc03_score_range(self):
        with self.assertRaises(ValueError):
            GC.normalize_score(55, 50)
        with self.assertRaises(ValueError):
            GC.normalize_score(-5, 100)


if __name__ == "__main__":
    unittest.main()
