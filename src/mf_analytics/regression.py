"""Single-factor CAPM OLS using aligned periodic excess returns."""
import numpy as np
import pandas as pd


def capm_regression(fund_returns: pd.Series, market_returns: pd.Series,
                    risk_free_periodic=0.0, periods_per_year: int = 252) -> dict:
    data = pd.concat([fund_returns.rename("fund"), market_returns.rename("market")], axis=1).dropna()
    if np.isscalar(risk_free_periodic):
        rf = float(risk_free_periodic)
        data["fund_excess"] = data["fund"] - rf
        data["market_excess"] = data["market"] - rf
    else:
        rf = risk_free_periodic.reindex(data.index)
        data["fund_excess"] = data["fund"] - rf
        data["market_excess"] = data["market"] - rf
        data = data.dropna()
    n = len(data)
    empty = {"n_obs": n, "alpha_periodic": np.nan, "alpha_annualized": np.nan,
             "beta": np.nan, "r_squared": np.nan, "alpha_pvalue": np.nan, "beta_pvalue": np.nan}
    if n < 3 or data["market_excess"].var(ddof=1) == 0:
        return empty
    x = data["market_excess"].to_numpy(float)
    y = data["fund_excess"].to_numpy(float)
    X = np.column_stack([np.ones(n), x])
    coef, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
    fitted = X @ coef
    residuals = y - fitted
    ss_res = float(residuals @ residuals)
    ss_tot = float(((y - y.mean()) ** 2).sum())
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else np.nan
    alpha_p = beta_p = np.nan
    try:
        from scipy import stats
        dof = n - 2
        mse = ss_res / dof
        covariance = mse * np.linalg.inv(X.T @ X)
        se = np.sqrt(np.diag(covariance))
        tstats = coef / se
        alpha_p = float(2 * stats.t.sf(abs(tstats[0]), dof))
        beta_p = float(2 * stats.t.sf(abs(tstats[1]), dof))
    except (ImportError, ValueError, np.linalg.LinAlgError, FloatingPointError):
        pass
    return {"n_obs": n, "alpha_periodic": float(coef[0]),
            "alpha_annualized": float((1 + coef[0]) ** periods_per_year - 1),
            "beta": float(coef[1]), "r_squared": float(r2),
            "alpha_pvalue": alpha_p, "beta_pvalue": beta_p}
