import sys
import unittest
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from mf_analytics.metrics import returns_from_prices, max_drawdown, cagr
from mf_analytics.regression import capm_regression


class TestMetrics(unittest.TestCase):
    def test_returns(self):
        idx = pd.date_range("2024-01-01", periods=3)
        prices = pd.DataFrame({"A": [100, 110, 121]}, index=idx)
        result = returns_from_prices(prices)
        self.assertAlmostEqual(result["A"].iloc[1], 0.1, places=8)
        self.assertAlmostEqual(result["A"].iloc[2], 0.1, places=8)

    def test_drawdown(self):
        prices = pd.Series([100, 120, 90], index=pd.date_range("2024-01-01", periods=3))
        self.assertAlmostEqual(max_drawdown(prices), -0.25, places=8)

    def test_cagr(self):
        prices = pd.Series([100, 121], index=pd.to_datetime(["2020-01-01", "2022-01-01"]))
        self.assertAlmostEqual(cagr(prices), 0.10, places=3)

    def test_beta(self):
        idx = pd.date_range("2024-01-01", periods=5)
        market = pd.Series([-.02, -.01, 0, .01, .02], index=idx)
        fund = 2 * market + .001
        result = capm_regression(fund, market, risk_free_periodic=0)
        self.assertAlmostEqual(result["beta"], 2.0, places=8)
        self.assertAlmostEqual(result["alpha_periodic"], .001, places=8)


if __name__ == "__main__":
    unittest.main()
