# Mutual Fund Portfolio, Risk & Performance Analytics

An interview-oriented analytics project using **Python, SQL (SQLite), Excel, and Power BI**. It evaluates mutual-fund NAV history against benchmarks, computes performance and risk metrics, estimates CAPM alpha and beta, explores overlapping return patterns with PCA, compares constrained portfolio allocations, and stress-tests scenarios.

> **Data honesty:** `data/sample/` contains synthetic demonstration data. It is included so the pipeline runs reproducibly. It is not real market data and outputs generated from it are not investment findings. Replace it with validated public NAV and benchmark data before making real-world claims.

## Scope
- NAV-to-return calculations, cumulative and annualized returns, rolling returns
- Annualized volatility, downside deviation, Sharpe, Sortino, maximum drawdown and recovery diagnostics
- Fund-versus-benchmark comparisons
- Correlation matrix and PCA of fund returns
- CAPM OLS regression: alpha, beta, R-squared, p-values (where SciPy is available)
- Long-only mean-variance optimization with allocation constraints
- Scenario stress testing and historical bull/bear/high-volatility regime analysis
- SQLite schema and example business queries
- Excel validation workbook and Power BI-ready CSV exports

## Quick start
Requires Python 3.10 or newer.

```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
pip install -r requirements.txt
python run_pipeline.py
python -m unittest discover -s tests -v
```

The pipeline reads `data/sample/nav.csv`, `data/sample/benchmark.csv`, and `data/sample/fund_metadata.csv`, then writes analysis outputs under `outputs/` and creates an SQLite database.

## Use real data
1. Fetch NAV history from a documented provider such as AMFI India / MFAPI, and validate scheme identifiers and history coverage.
2. Obtain a suitable benchmark series, preferably total-return data where available, and standardize it using `scripts/standardize_benchmark.py`.
3. Map each fund to an appropriate benchmark and align observations by date. Do not silently forward-fill returns or invent missing values.
4. Review `outputs/data_quality_report.csv` before interpreting results.

### Input formats
- NAV: `date,scheme_code,fund_name,nav` (one row per fund/date)
- Benchmark: `date,benchmark_name,close` (one row per benchmark/date)
- Fund metadata: `scheme_code,fund_name,category,benchmark_name`

Dates use ISO `YYYY-MM-DD`; NAV and close must be positive numbers.

## Methodology and limitations
- Periodic simple returns are derived from NAV/index changes. For investor-return analysis, confirm whether distributions need to be included.
- Annualization assumes 252 trading observations per year by default; configure this for other frequencies.
- CAGR uses elapsed calendar days. Rolling returns use a 252-observation default window.
- Sharpe = annualized mean periodic excess return / annualized volatility.
- Sortino uses downside deviation relative to a configurable minimum acceptable return (default zero).
- Drawdown is measured from the running peak of a cumulative wealth index.
- CAPM regression uses aligned periodic excess returns and reports annualized alpha. Statistical inference depends on data quality and model assumptions.
- PCA is exploratory; components are not predictions or standalone fund-selection rules.
- Optimizer inputs are historical estimates and uncertain; constraints do not guarantee future performance.
- Stress tests are scenarios, not forecasts.

## Main outputs
- `outputs/fund_metrics.csv`, `outputs/benchmark_comparison.csv`, `outputs/rolling_returns.csv`
- `outputs/correlation_matrix.csv`, `outputs/pca_explained_variance.csv`, `outputs/pca_loadings.csv`
- `outputs/capm_regression.csv`
- `outputs/portfolio_weights.csv`, `outputs/portfolio_summary.csv`, `outputs/efficient_frontier.csv`
- `outputs/stress_test_results.csv`, `outputs/regime_analysis.csv`
- `outputs/data_quality_report.csv`, `outputs/validation_workbook.xlsx`
- `outputs/powerbi/`: tidy CSVs for Power BI import
- `outputs/mutual_fund_analytics.db`: SQLite database

## Power BI dashboard
Import CSVs from `outputs/powerbi/`. Suggested pages:
1. **Overview:** CAGR, volatility, Sharpe, maximum drawdown, excess return and slicers.
2. **Performance:** wealth index, rolling returns and benchmark comparison.
3. **Risk:** return-versus-volatility scatter, drawdown, Sharpe/Sortino.
4. **Diversification:** correlation heatmap and PCA explained variance.
5. **Portfolio & Stress:** allocation, risk/return and scenario comparisons.

A Power BI-ready data model and dashboard specification are included. A finished `.pbix` file is not included.

## Project structure
- `src/mf_analytics/`: reusable calculations, validation, regression, optimization, pipeline
- `scripts/`: NAV ingestion and benchmark standardization
- `sql/`: schema and example queries
- `data/sample/`: synthetic reproducible input data
- `outputs/`: generated reports
- `powerbi/`: dashboard specification
- `docs/`: data source notes
- `tests/`: unit tests

## License
MIT. Review data-provider terms separately before redistributing downloaded data.
