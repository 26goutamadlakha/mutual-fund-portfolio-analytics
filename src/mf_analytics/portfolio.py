"""Constrained mean-variance portfolio optimization."""
import numpy as np
import pandas as pd
from scipy.optimize import minimize


def portfolio_stats(weights, mean_returns, cov, periods_per_year=252):
    w = np.asarray(weights, dtype=float)
    mu = np.asarray(mean_returns, dtype=float)
    c = np.asarray(cov, dtype=float)
    return float(w @ mu * periods_per_year), float(np.sqrt(max(w @ c @ w, 0.0)) * np.sqrt(periods_per_year))


def optimize_portfolio(returns: pd.DataFrame, risk_free_annual=0.04, max_weight=0.60, periods_per_year=252):
    clean = returns.dropna()
    if clean.shape[1] < 2 or len(clean) < 20:
        raise ValueError("Need at least two funds and 20 aligned return observations.")
    n = clean.shape[1]
    if max_weight * n < 1:
        raise ValueError("Infeasible constraints: number of funds * max_weight must be >= 1.")
    mu = clean.mean().to_numpy()
    cov = clean.cov().to_numpy()

    def neg_sharpe(w):
        ret, vol = portfolio_stats(w, mu, cov, periods_per_year)
        return -(ret - risk_free_annual) / vol if vol > 0 else 1e6

    constraints = [{"type": "eq", "fun": lambda w: w.sum() - 1}]
    bounds = [(0.0, max_weight)] * n
    result = minimize(neg_sharpe, np.repeat(1 / n, n), method="SLSQP",
                      bounds=bounds, constraints=constraints,
                      options={"maxiter": 2000, "ftol": 1e-12})
    if not result.success:
        raise RuntimeError("Optimization failed: " + result.message)
    ret, vol = portfolio_stats(result.x, mu, cov, periods_per_year)
    weights = pd.DataFrame({"fund_name": clean.columns, "weight": result.x})
    summary = pd.DataFrame([{
        "expected_annualized_return": ret, "annualized_volatility": vol,
        "sharpe_ratio": (ret - risk_free_annual) / vol if vol > 0 else np.nan,
        "risk_free_rate": risk_free_annual, "max_weight_constraint": max_weight,
        "observations": len(clean)
    }])
    frontier = []
    targets = np.linspace(float(mu.min() * periods_per_year), float(mu.max() * periods_per_year), 25)
    for target in targets:
        cons = [{"type": "eq", "fun": lambda w: w.sum() - 1},
                {"type": "eq", "fun": lambda w, t=target: w @ mu * periods_per_year - t}]
        rr = minimize(lambda w: portfolio_stats(w, mu, cov, periods_per_year)[1],
                      np.repeat(1 / n, n), method="SLSQP", bounds=bounds,
                      constraints=cons, options={"maxiter": 1000, "ftol": 1e-10})
        if rr.success:
            r, v = portfolio_stats(rr.x, mu, cov, periods_per_year)
            frontier.append({"target_return": target, "portfolio_return": r, "portfolio_volatility": v})
    return weights, summary, pd.DataFrame(frontier)
