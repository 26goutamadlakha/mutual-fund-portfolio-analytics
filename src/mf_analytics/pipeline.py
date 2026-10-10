"""End-to-end pipeline that transforms NAV and benchmark inputs into analyst-ready outputs."""
from pathlib import Path
import sqlite3
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from .metrics import metrics_for_fund, returns_from_prices, drawdown_series, rolling_compound_returns
from .regression import capm_regression
from .portfolio import optimize_portfolio
from .validation import validate_nav, validate_benchmark


def _write(df, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=True if df.index.name == "date" else False)


def run_pipeline(root: Path, periods_per_year=252, risk_free_annual=0.04, rolling_window=63):
    root = Path(root)
    data_dir = root / "data" / "sample"
    out = root / "outputs"
    pbi = out / "powerbi"
    pbi.mkdir(parents=True, exist_ok=True)

    nav = validate_nav(pd.read_csv(data_dir / "nav.csv"))
    benchmark = validate_benchmark(pd.read_csv(data_dir / "benchmark.csv"))
    meta_path = data_dir / "fund_metadata.csv"
    metadata = pd.read_csv(meta_path) if meta_path.exists() else pd.DataFrame()

    issues = []
    for frame_name, frame in [("nav", nav), ("benchmark", benchmark)]:
        issues.append({"dataset": frame_name, "rows": len(frame), "min_date": frame.date.min(),
                       "max_date": frame.date.max(), "missing_values": int(frame.isna().sum().sum())})
    pd.DataFrame(issues).to_csv(out / "data_quality_report.csv", index=False)

    prices = nav.pivot(index="date", columns="fund_name", values="nav").sort_index()
    all_benchmarks = benchmark.pivot(index="date", columns="benchmark_name", values="close").sort_index()
    benchmark_name = str(all_benchmarks.columns[0])
    market_prices = all_benchmarks[benchmark_name].dropna()
    market_returns = market_prices.pct_change(fill_method=None)
    returns = returns_from_prices(prices)

    metric_rows = []
    wealth = prices.div(prices.apply(lambda s: s.dropna().iloc[0]), axis=1) * 100
    wealth.index.name = "date"
    drawdowns = wealth.apply(drawdown_series)
    drawdowns.index.name = "date"
    rolling = rolling_compound_returns(returns, rolling_window)
    returns_out = returns.copy(); returns_out.index.name = "date"
    rolling_out = rolling.copy(); rolling_out.index.name = "date"

    for fund in prices.columns:
        metric = metrics_for_fund(prices[fund], returns[fund], risk_free_annual, periods_per_year)
        metric["fund_name"] = fund
        if not metadata.empty and "fund_name" in metadata:
            row = metadata[metadata["fund_name"] == fund]
            if not row.empty:
                for col in ["scheme_code", "category", "benchmark_name"]:
                    if col in row.columns:
                        metric[col] = row.iloc[0][col]
        metric_rows.append(metric)
    metrics = pd.DataFrame(metric_rows)

    comparisons = []
    for fund in prices.columns:
        meta_row = metadata[metadata["fund_name"] == fund] if "fund_name" in metadata else pd.DataFrame()
        bench_label = str(meta_row.iloc[0]["benchmark_name"]) if len(meta_row) and "benchmark_name" in meta_row else benchmark_name
        if bench_label not in all_benchmarks.columns:
            bench_label = benchmark_name
        common = pd.concat([prices[fund].rename("fund"), all_benchmarks[bench_label].rename("benchmark")], axis=1).dropna()
        if len(common) >= 2:
            fund_ret = common.fund.iloc[-1] / common.fund.iloc[0] - 1
            bench_ret = common.benchmark.iloc[-1] / common.benchmark.iloc[0] - 1
        else:
            fund_ret = bench_ret = np.nan
        comparisons.append({"fund_name": fund, "benchmark_name": bench_label, "common_observations": len(common),
                            "fund_total_return": fund_ret, "benchmark_total_return": bench_ret,
                            "active_return_pp": (fund_ret - bench_ret) * 100 if pd.notna(fund_ret) and pd.notna(bench_ret) else np.nan})
    comparison = pd.DataFrame(comparisons)

    corr = returns.corr()
    capm_rows = []
    rf_periodic = (1 + risk_free_annual) ** (1 / periods_per_year) - 1
    for fund in returns.columns:
        result = capm_regression(returns[fund], market_returns, rf_periodic, periods_per_year)
        result["fund_name"] = fund
        result["benchmark_name"] = benchmark_name
        capm_rows.append(result)
    capm = pd.DataFrame(capm_rows)

    aligned = returns.dropna()
    pca_explained = pd.DataFrame()
    pca_loadings = pd.DataFrame()
    if aligned.shape[1] >= 2 and aligned.shape[0] >= 3:
        standardized = StandardScaler().fit_transform(aligned)
        model = PCA(n_components=min(aligned.shape[1], aligned.shape[0]))
        model.fit(standardized)
        pca_explained = pd.DataFrame({"component": [f"PC{i+1}" for i in range(len(model.explained_variance_ratio_))],
                                      "explained_variance_ratio": model.explained_variance_ratio_,
                                      "cumulative_explained_variance": np.cumsum(model.explained_variance_ratio_)})
        pca_loadings = pd.DataFrame(model.components_.T, index=aligned.columns,
                                    columns=[f"PC{i+1}" for i in range(model.n_components_)])
        pca_loadings.index.name = "fund_name"
        pca_loadings = pca_loadings.reset_index()

    opt_weights = pd.DataFrame()
    opt_summary = pd.DataFrame()
    frontier = pd.DataFrame()
    try:
        opt_weights, opt_summary, frontier = optimize_portfolio(aligned, risk_free_annual, 0.60, periods_per_year)
    except (ValueError, RuntimeError) as exc:
        opt_summary = pd.DataFrame([{"status": "not_available", "reason": str(exc)}])

    scenarios = []
    beta_map = dict(zip(capm.get("fund_name", []), capm.get("beta", [])))
    for shock in [-0.20, -0.10, -0.05, 0.05, 0.10]:
        for fund in prices.columns:
            beta = beta_map.get(fund, np.nan)
            scenarios.append({"fund_name": fund, "market_shock": shock, "beta_used": beta,
                              "estimated_market_related_move": beta * shock if pd.notna(beta) else np.nan,
                              "interpretation": "illustrative beta shock; not a forecast"})
    stress = pd.DataFrame(scenarios)

    market_63d = (1 + market_returns).rolling(63, min_periods=63).apply(np.prod, raw=True) - 1
    vol_63d = market_returns.rolling(63, min_periods=63).std() * np.sqrt(periods_per_year)
    high_vol_threshold = vol_63d.quantile(0.75)
    regimes = pd.DataFrame({"date": market_returns.index, "market_return": market_returns.values,
                            "rolling_63d_market_return": market_63d.values, "rolling_63d_annualized_volatility": vol_63d.values})
    regimes["regime"] = np.where(vol_63d >= high_vol_threshold, "High volatility",
                         np.where(market_63d < 0, "Bear/negative 63d return", "Bull/positive 63d return"))
    regimes.loc[market_63d.isna(), "regime"] = "Insufficient history"

    outputs = {
        "fund_metrics.csv": metrics, "benchmark_comparison.csv": comparison,
        "rolling_returns.csv": rolling_out.reset_index(), "fund_returns.csv": returns_out.reset_index(),
        "fund_wealth_index.csv": wealth.reset_index(), "drawdowns.csv": drawdowns.reset_index(),
        "correlation_matrix.csv": corr.reset_index(names="fund_name"),
        "capm_regression.csv": capm, "pca_explained_variance.csv": pca_explained,
        "pca_loadings.csv": pca_loadings, "portfolio_weights.csv": opt_weights,
        "portfolio_summary.csv": opt_summary, "efficient_frontier.csv": frontier,
        "stress_test_results.csv": stress, "regime_analysis.csv": regimes
    }
    for filename, frame in outputs.items():
        frame.to_csv(out / filename, index=False)
        frame.to_csv(pbi / filename, index=False)

    # Keep queryable analysis results in SQLite; replace tables on every run.
    with sqlite3.connect(out / "mutual_fund_analytics.db") as conn:
        nav.to_sql("nav_history", conn, if_exists="replace", index=False)
        benchmark.to_sql("benchmark_history", conn, if_exists="replace", index=False)
        metadata.to_sql("fund_metadata", conn, if_exists="replace", index=False)
        for filename, frame in outputs.items():
            frame.to_sql(filename.removesuffix(".csv").replace("-", "_"), conn, if_exists="replace", index=False)

    # Excel is a cross-check surface, not an independent source of truth.
    with pd.ExcelWriter(out / "validation_workbook.xlsx", engine="openpyxl") as writer:
        metrics.to_excel(writer, sheet_name="Fund Metrics", index=False)
        comparison.to_excel(writer, sheet_name="Benchmark", index=False)
        capm.to_excel(writer, sheet_name="CAPM", index=False)
        corr.to_excel(writer, sheet_name="Correlation")
        opt_weights.to_excel(writer, sheet_name="Weights", index=False)
        stress.to_excel(writer, sheet_name="Stress", index=False)

    print(f"Pipeline complete. Outputs written to {out}")
    print(f"Input basis: synthetic sample data under {data_dir}")
    print("Replace sample data and re-run before reporting real-world findings.")
