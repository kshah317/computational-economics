import math
import unittest

import numpy as np

import convergence as conv

# standard library unittest plus numpy only, run with: python -m unittest tests.py


class GrowthRateTests(unittest.TestCase):

    def test_growth_rate_formula(self):
        # a country that doubled over 33 years should show ln(2)/33 growth
        rows = [{"gdp_1990": 1000.0, "gdp_2023": 2000.0}]
        conv.add_growth_fields(rows)
        self.assertAlmostEqual(rows[0]["growth_rate"], math.log(2) / 33, places=6)

    def test_flat_gdp_has_zero_growth(self):
        rows = [{"gdp_1990": 5000.0, "gdp_2023": 5000.0}]
        conv.add_growth_fields(rows)
        self.assertAlmostEqual(rows[0]["growth_rate"], 0.0, places=8)

    def test_shrinking_gdp_is_negative_growth(self):
        rows = [{"gdp_1990": 2000.0, "gdp_2023": 1000.0}]
        conv.add_growth_fields(rows)
        self.assertLess(rows[0]["growth_rate"], 0.0)


class RegressionMathTests(unittest.TestCase):
    # sanity-checks the from-scratch OLS against a case with a known answer,
    # and the from-scratch p-value against standard t-table reference values

    def test_perfect_negative_line_recovers_exact_slope(self):
        # y = 10 - 2x exactly, no noise, regression should recover slope -2
        rows = []
        for i in range(1, 21):
            x = float(i)
            y = 10.0 - 2.0 * x
            rows.append({"log_gdp_1990": x, "growth_rate": y})
        result = conv.run_regression(rows)
        self.assertAlmostEqual(result.slope, -2.0, places=6)
        self.assertAlmostEqual(result.r_squared, 1.0, places=6)

    def test_flat_relationship_has_near_zero_slope(self):
        # y is constant regardless of x, slope should come out ~0
        rows = [{"log_gdp_1990": float(i), "growth_rate": 5.0} for i in range(1, 21)]
        result = conv.run_regression(rows)
        self.assertAlmostEqual(result.slope, 0.0, places=6)

    def test_p_value_matches_known_t_table_value(self):
        # t=2.042, dof=30 is a textbook value, two-tailed p is ~0.05
        p = conv.two_tailed_p_value(2.042, 30)
        self.assertAlmostEqual(p, 0.05, places=2)

    def test_p_value_is_one_when_t_stat_is_zero(self):
        self.assertAlmostEqual(conv.two_tailed_p_value(0.0, 30), 1.0, places=6)

    def test_p_value_shrinks_as_t_stat_grows(self):
        small_t = conv.two_tailed_p_value(1.0, 30)
        large_t = conv.two_tailed_p_value(5.0, 30)
        self.assertGreater(small_t, large_t)


class WeightedRegressionTests(unittest.TestCase):
    # the population-weighted robustness check reuses the same OLS math with
    # weights added in, these confirm the weighting actually does something
    # and reduces to plain OLS when every weight is equal

    def test_equal_weights_match_unweighted_regression(self):
        rows = []
        for i in range(1, 21):
            x = float(i)
            y = 10.0 - 2.0 * x + (0.3 if i % 3 == 0 else 0.0)  # a little noise
            rows.append({"log_gdp_1990": x, "growth_rate": y, "pop_1990": 1_000_000})
        unweighted = conv.run_regression(rows)
        weighted = conv.run_population_weighted_regression(rows)
        self.assertAlmostEqual(unweighted.slope, weighted.slope, places=6)
        self.assertAlmostEqual(unweighted.r_squared, weighted.r_squared, places=6)

    def test_heavily_weighted_point_pulls_the_fit_toward_it(self):
        # two clusters of points with opposite slopes; whichever cluster
        # gets the huge population weight should dominate the fitted slope
        rows = []
        for i in range(1, 11):
            # small-population cluster: slope of roughly +1
            rows.append({"log_gdp_1990": float(i), "growth_rate": float(i), "pop_1990": 1_000})
        for i in range(1, 11):
            # huge-population cluster: slope of roughly -1
            rows.append({"log_gdp_1990": float(i) + 20.0, "growth_rate": -float(i), "pop_1990": 1_000_000_000})
        weighted = conv.run_population_weighted_regression(rows)
        # the billion-person cluster should pull the weighted slope negative,
        # even though half the *countries* in the data have a positive slope
        self.assertLess(weighted.slope, 0.0)


class RankingTests(unittest.TestCase):

    def test_top_and_bottom_growers_are_correctly_ordered(self):
        rows = [
            {"country": "A", "growth_rate": 0.05},
            {"country": "B", "growth_rate": -0.02},
            {"country": "C", "growth_rate": 0.01},
        ]
        top, bottom = conv.top_and_bottom_growers(rows, n=1)
        self.assertEqual(top[0]["country"], "A")
        self.assertEqual(bottom[0]["country"], "B")


class EndToEndTests(unittest.TestCase):
    # loads the real bundled dataset and checks the whole pipeline holds up

    @classmethod
    def setUpClass(cls):
        cls.rows = conv.add_growth_fields(conv.load_countries())

    def test_bundled_dataset_has_a_reasonable_number_of_countries(self):
        self.assertGreater(len(self.rows), 100)

    def test_every_row_has_a_finite_growth_rate(self):
        for row in self.rows:
            self.assertTrue(np.isfinite(row["growth_rate"]))

    def test_regression_runs_without_error_on_real_data(self):
        result = conv.run_regression(self.rows)
        self.assertEqual(result.n, len(self.rows))
        self.assertTrue(np.isfinite(result.slope))
        self.assertTrue(0.0 <= result.p_value <= 1.0)

    def test_population_weighted_regression_runs_on_real_data(self):
        result = conv.run_population_weighted_regression(self.rows)
        self.assertEqual(result.n, len(self.rows))
        self.assertTrue(np.isfinite(result.slope))
        self.assertTrue(0.0 <= result.p_value <= 1.0)
        # not a strict requirement of the method, just a check that this
        # dataset actually shows the pattern the README talks about: the
        # population-weighted slope on this data is steeper than the
        # unweighted one, since China and India dominate the weighting
        unweighted = conv.run_regression(self.rows)
        self.assertLess(result.slope, unweighted.slope)


if __name__ == "__main__":
    unittest.main()
