# Power BI Dashboard Specification

Import tidy CSVs from `outputs/powerbi/` after running `python run_pipeline.py`.

## Model
Use `fund_metrics.csv` as one-row-per-fund summary. Use `fund_returns.csv`, `fund_wealth_index.csv`, `drawdowns.csv`, and `rolling_returns.csv` for time-series visuals. Add a date dimension and relate by date. Use fund metadata for category slicers once benchmark mapping and fund category values are validated.

## Page 1: Overview
- KPI cards: CAGR, total return, annualized volatility, Sharpe, Sortino, maximum drawdown.
- Fund category and period slicers.
- Table ranking funds by risk-adjusted performance, with caution that historical metrics do not predict future performance.

## Page 2: Performance
- Cumulative wealth indexed to 100.
- Rolling returns by fund.
- Benchmark total return vs fund total return and active return.

## Page 3: Risk
- Return-vs-volatility scatter.
- Drawdown time series.
- Sharpe/Sortino comparison.
- Recovery time where available.

## Page 4: Diversification
- Correlation matrix rendered as a heatmap.
- PCA explained variance bar chart and cumulative variance line.
- Explain that PCA is exploratory and correlation can change during stress.

## Page 5: Portfolio & Stress
- Constrained optimized weights.
- Portfolio estimated return, volatility and Sharpe.
- Beta-based scenario sensitivity chart, labelled illustrative not forecast.
- Historical regime summary; regime logic is a simple descriptive classification.

## Validation
- Check slicers and date filter context.
- Ensure percent fields are formatted as percentages while ratio fields remain numeric.
- Do not present synthetic demo outputs as actual market findings.
- This repo contains Power BI-ready data and this specification, not a .pbix file.
