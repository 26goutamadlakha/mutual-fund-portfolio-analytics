"""Data loading and validation helpers."""
import pandas as pd


def validate_nav(nav: pd.DataFrame) -> pd.DataFrame:
    required = {"date", "scheme_code", "fund_name", "nav"}
    missing = required - set(nav.columns)
    if missing:
        raise ValueError(f"NAV input missing columns: {sorted(missing)}")
    out = nav.copy()
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    out["nav"] = pd.to_numeric(out["nav"], errors="coerce")
    if out["date"].isna().any() or out["nav"].isna().any():
        raise ValueError("NAV data contains invalid dates or non-numeric NAV values.")
    if (out["nav"] <= 0).any():
        raise ValueError("NAV values must be positive.")
    if out.duplicated(["date", "scheme_code"]).any():
        raise ValueError("Duplicate date/scheme_code rows found in NAV data.")
    return out.sort_values(["date", "scheme_code"])


def validate_benchmark(benchmark: pd.DataFrame) -> pd.DataFrame:
    required = {"date", "benchmark_name", "close"}
    missing = required - set(benchmark.columns)
    if missing:
        raise ValueError(f"Benchmark input missing columns: {sorted(missing)}")
    out = benchmark.copy()
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    out["close"] = pd.to_numeric(out["close"], errors="coerce")
    if out["date"].isna().any() or out["close"].isna().any() or (out["close"] <= 0).any():
        raise ValueError("Benchmark contains invalid dates or non-positive prices.")
    if out.duplicated(["date", "benchmark_name"]).any():
        raise ValueError("Duplicate date/benchmark_name rows found in benchmark data.")
    return out.sort_values(["date", "benchmark_name"])
