import json
import math
import os
from dataclasses import dataclass
from typing import List

import numpy as np

# this is the actual convergence test: does a country's starting income level
# (1990) predict how fast it grew over the next 33 years? if poorer countries
# grew faster on average, the slope of that relationship comes out negative,
# which is the textbook definition of "beta convergence." everything here is
# plain numpy, no statsmodels or scipy, including the significance test.

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "gdp_per_capita_1990_2023.json")
START_YEAR = 1990
END_YEAR = 2023
SPAN_YEARS = END_YEAR - START_YEAR


@dataclass
class RegressionResult:
    # everything a reader needs to judge the regression at a glance
    n: int
    slope: float
    intercept: float
    slope_std_err: float
    t_stat: float
    p_value: float
    r_squared: float


def load_countries() -> List[dict]:
    # reads the bundled snapshot, each row already has gdp_1990 and gdp_2023
    with open(DATA_PATH, "r", encoding="utf-8") as handle:
        return json.load(handle)


def add_growth_fields(rows: List[dict]) -> List[dict]:
    # log difference divided by years is the standard way economists compute
    # an annualized, continuously compounded growth rate, it is well behaved
    # even when growth is uneven year to year, unlike a simple percent change
    for row in rows:
        row["log_gdp_1990"] = math.log(row["gdp_1990"])
        row["growth_rate"] = (math.log(row["gdp_2023"]) - math.log(row["gdp_1990"])) / SPAN_YEARS
    return rows


def _log_beta(a: float, b: float) -> float:
    # log of the beta function, built from math.lgamma so the incomplete
    # beta function below stays numerically stable for large inputs
    return math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)


def _betacf(a: float, b: float, x: float, max_iter: int = 200, eps: float = 1e-10) -> float:
    # Lentz's continued fraction for the incomplete beta function, this is
    # the same core algorithm scipy uses internally, written out by hand so
    # the project has no dependency beyond numpy
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < eps:
        d = eps
    d = 1.0 / d
    h = d
    for m in range(1, max_iter):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < eps:
            d = eps
        c = 1.0 + aa / c
        if abs(c) < eps:
            c = eps
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < eps:
            d = eps
        c = 1.0 + aa / c
        if abs(c) < eps:
            c = eps
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < eps:
            break
    return h


def _regularized_incomplete_beta(a: float, b: float, x: float) -> float:
    # I_x(a, b), bounded between 0 and 1, switches which side of the
    # continued fraction converges fastest depending on where x sits
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    front = math.exp(math.log(x) * a + math.log(1.0 - x) * b - _log_beta(a, b))
    if x < (a + 1.0) / (a + b + 2.0):
        return front * _betacf(a, b, x) / a
    return 1.0 - front * _betacf(b, a, 1.0 - x) / b


def two_tailed_p_value(t_stat: float, degrees_of_freedom: int) -> float:
    # p-value for a two-sided t-test, computed from the incomplete beta
    # function above instead of importing scipy.stats
    x = degrees_of_freedom / (degrees_of_freedom + t_stat ** 2)
    return _regularized_incomplete_beta(degrees_of_freedom / 2.0, 0.5, x)


def run_regression(rows: List[dict]) -> RegressionResult:
    # a single-predictor OLS regression, growth_rate on log(gdp_1990),
    # this is the classic Barro-style "beta convergence" specification
    x = np.array([r["log_gdp_1990"] for r in rows])
    y = np.array([r["growth_rate"] for r in rows])
    n = len(rows)

    x_mean, y_mean = x.mean(), y.mean()
    slope = np.sum((x - x_mean) * (y - y_mean)) / np.sum((x - x_mean) ** 2)
    intercept = y_mean - slope * x_mean

    predicted = intercept + slope * x
    residuals = y - predicted
    sse = np.sum(residuals ** 2)
    sst = np.sum((y - y_mean) ** 2)
    r_squared = 1.0 - sse / sst

    degrees_of_freedom = n - 2
    residual_variance = sse / degrees_of_freedom
    slope_std_err = math.sqrt(residual_variance / np.sum((x - x_mean) ** 2))
    t_stat = slope / slope_std_err
    p_value = two_tailed_p_value(t_stat, degrees_of_freedom)

    return RegressionResult(
        n=n, slope=slope, intercept=intercept, slope_std_err=slope_std_err,
        t_stat=t_stat, p_value=p_value, r_squared=r_squared,
    )


def top_and_bottom_growers(rows: List[dict], n: int = 8) -> tuple:
    # the ranking view: who actually caught up the fastest, and who fell
    # behind, regardless of what the average trend line says
    ranked = sorted(rows, key=lambda r: r["growth_rate"], reverse=True)
    return ranked[:n], ranked[-n:]


def interpret(result: RegressionResult) -> str:
    # plain-language readout, since the whole point is a result someone can
    # understand without knowing what a beta coefficient normally means
    direction = "converging" if result.slope < 0 else "diverging"
    significant = result.p_value < 0.05
    confidence = "statistically significant" if significant else "not statistically significant"
    return (
        f"slope = {result.slope:.5f} ({direction}), {confidence} at the 5% level "
        f"(p = {result.p_value:.4f}, n = {result.n} countries, R-squared = {result.r_squared:.3f})"
    )


def plot_convergence(rows: List[dict], result: RegressionResult, out_path: str) -> None:
    # scatter of starting income vs growth rate, with the fitted line drawn
    # through it, this is the picture that makes convergence (or its
    # absence) visible at a glance
    import matplotlib
    matplotlib.use("Agg")  # no display in this environment, just save the file
    import matplotlib.pyplot as plt

    x = np.array([r["log_gdp_1990"] for r in rows])
    y = np.array([r["growth_rate"] for r in rows])

    fig, ax = plt.subplots(figsize=(9, 6))
    ax.scatter(x, y, alpha=0.6, s=28, color="#2c6e91", edgecolor="white", linewidth=0.4)

    line_x = np.linspace(x.min(), x.max(), 100)
    line_y = result.intercept + result.slope * line_x
    ax.plot(line_x, line_y, color="#c0392b", linewidth=2, label="fitted trend")

    ax.set_xlabel("log GDP per capita, 1990 (starting income)")
    ax.set_ylabel(f"annualized growth rate, {START_YEAR}-{END_YEAR}")
    ax.set_title("Do poorer countries grow faster? (Beta Convergence, 1990-2023)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    countries = add_growth_fields(load_countries())
    regression = run_regression(countries)
    print(interpret(regression))
    plot_path = os.path.join(os.path.dirname(__file__), "convergence_plot.png")
    plot_convergence(countries, regression, plot_path)
    print(f"saved plot to {plot_path}")
