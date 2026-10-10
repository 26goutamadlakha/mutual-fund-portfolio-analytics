import sys
import unittest
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from mf_analytics.validation import validate_nav, validate_benchmark


class TestInputValidation(unittest.TestCase):
    def test_nav_duplicate_rejected(self):
        nav = pd.DataFrame({"date": ["2024-01-01", "2024-01-01"], "scheme_code": ["1", "1"],
                            "fund_name": ["F", "F"], "nav": [100, 101]})
        with self.assertRaises(ValueError):
            validate_nav(nav)

    def test_nonpositive_nav_rejected(self):
        nav = pd.DataFrame({"date": ["2024-01-01"], "scheme_code": ["1"],
                            "fund_name": ["F"], "nav": [0]})
        with self.assertRaises(ValueError):
            validate_nav(nav)

    def test_valid_benchmark(self):
        df = pd.DataFrame({"date": ["2024-01-01"], "benchmark_name": ["Index"], "close": [100]})
        result = validate_benchmark(df)
        self.assertEqual(result.iloc[0]["close"], 100)


if __name__ == "__main__":
    unittest.main()
