"""Performance and risk metrics. Returns are represented as decimals, not percentages."""
import numpy as np
import pandas as pd


def returns_from_prices(prices: pd.DataFrame) -> pd.DataFrame:
    return prices.sort_index().pct_change(fill_method=None)


def cagr(prices: pd.Series) -> float:
    s = prices.dropna()
    if len(s) < 2 or s.iloc[0] <= 0 or s.iloc[-1] <= 0:
        return np.nan
    days = (s.index[-1] - s.index[0]).days
    return float((s.iloc[-1] / s.iloc[0]) ** (365.25 / days) - 1) if days > 0 else np.nan


def annualized_volatility(r: pd.Series, periods_per_year: int = 252) -> float:
    x = r.dropna()
    return float(x.std(ddof=1) * np.sqrt(periods_per_year)) if len(x) > 1 else np.nan


def downside_deviation(r: pd.Series, mar_periodic: float = 0.0, periods_per_year: int = 252) -> float:
    x = r.dropna().to_numpy(dtype=float) - mar_periodic
    if not len(x):
        return np.nan
    downside = np.minimum(x, 0.0)
    return float(np.sqrt(np.mean(downside ** 2)) * np.sqrt(periods_per_year))


def sharpe_ratio(r: pd.Series, risk_free_annual: float = 0.04, periods_per_year: int = 252) -> float:
    x = r.dropna()
    if len(x) < 2:
        return np.nan
    rf_periodic = (1 + risk_free_annual) ** (1 / periods_per_year) - 1
    vol = x.std(ddof=1) * np.sqrt(periods_per_year)
    return float((x.mean() - rf_periodic) * periods_per_year / vol) if vol > 0 else np.nan


def sortino_ratio(r: pd.Series, mar_annual: float = 0.0, periods_per_year: int = 252) -> float:
    x = r.dropna()
    if not len(x):
        return np.nan
    mar_periodic = (1 + mar_annual) ** (1 / periods_per_year) - 1
    dd = downside_deviation(x, mar_periodic, periods_per_year)
    return float((x.mean() - mar_periodic) * periods_per_year / dd) if dd > 0 else np.nan


def drawdown_series(prices: pd.Series) -> pd.Series:
    s = prices.dropna()
    return s / s.cummax() - 1.0 if len(s) else s


def max_drawdown(prices: pd.Series) -> float:
    dd = drawdown_series(prices)
    return float(dd.min()) if len(dd) else np.nan


def recovery_days(prices: pd.Series) -> float:
    """Calendar days from peak before deepest trough until that peak is regained; NaN if not recovered."""
    s = prices.dropna()
    if len(s) < 2:
        return np.nan
    dd = s / s.cummax() - 1
    trough = dd.idxmin()
    peak_level = s.cummax().loc[trough]
    peak_dates = s.loc[:trough][s.loc[:trough] == peak_level].index
    if not len(peak_dates):
        return np.nan
    regained = s.loc[trough:][s.loc[trough:] >= peak_level]
    return float((regained.index[0] - peak_dates[-1]).days) if len(regained) else np.nan


def rolling_compound_returns(r: pd.DataFrame, window: int = 252) -> pd.DataFrame:
    return (1 + r).rolling(window, min_periods=window).apply(np.prod, raw=True) - 1


def metrics_for_fund(prices: pd.Series, r: pd.Series, risk_free_annual: float = 0.04,
                     periods_per_year: int = 252) -> dict:
    p = prices.dropna()
    return {
        "observations": int(r.dropna().shape[0]),
        "total_return": float(p.iloc[-1] / p.iloc[0] - 1) if len(p) > 1 else np.nan,
        "cagr": cagr(p),
        "annualized_mean_return": float(r.dropna().mean() * periods_per_year) if len(r.dropna()) else np.nan,
        "annualized_volatility": annualized_volatility(r, periods_per_year),
        "downside_deviation": downside_deviation(r, periods_per_year=periods_per_year),
        "sharpe_ratio": sharpe_ratio(r, risk_free_annual, periods_per_year),
        "sortino_ratio": sortino_ratio(r, 0.0, periods_per_year),
        "max_drawdown": max_drawdown(p),
        "drawdown_recovery_days": recovery_days(p),
    }
