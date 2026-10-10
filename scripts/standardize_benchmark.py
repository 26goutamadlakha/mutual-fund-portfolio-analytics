#!/usr/bin/env python3
"""Normalize index CSVs to date,benchmark_name,close for the analytics pipeline."""
import argparse
from pathlib import Path
import pandas as pd


def standardize(input_path, output_path, date_col, close_col, benchmark_name):
    source = pd.read_csv(input_path)
    for col in (date_col, close_col):
        if col not in source.columns:
            raise ValueError(f"Column {col!r} is not present. Available: {list(source.columns)}")
    out = pd.DataFrame({
        "date": pd.to_datetime(source[date_col], errors="coerce").dt.strftime("%Y-%m-%d"),
        "benchmark_name": benchmark_name,
        "close": pd.to_numeric(source[close_col], errors="coerce"),
    })
    if out["date"].isna().any() or out["close"].isna().any() or (out["close"] <= 0).any():
        raise ValueError("Invalid dates or non-positive/non-numeric close values found.")
    if out.duplicated(["date", "benchmark_name"]).any():
        raise ValueError("Duplicate dates for this benchmark found.")
    out = out.sort_values("date")
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(destination, index=False)
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_csv")
    parser.add_argument("--output", default="data/real/benchmark.csv")
    parser.add_argument("--date-col", default="date")
    parser.add_argument("--close-col", default="close")
    parser.add_argument("--benchmark-name", required=True)
    args = parser.parse_args()
    out = standardize(args.input_csv, args.output, args.date_col, args.close_col, args.benchmark_name)
    print(f"Wrote {len(out)} benchmark observations to {args.output}")


if __name__ == "__main__":
    main()
