"""
chi_utils.py
------------
Chi-square test ki saari calculation yahan hai (formulas ke saath).
Hum pehle khud calculate karte hain, phir scipy se verify karte hain.
"""
import numpy as np
import pandas as pd
from scipy.stats import chi2, chi2_contingency


def get_expected(obs: pd.DataFrame) -> pd.DataFrame:
    """E = (row total x column total) / grand total"""
    o = obs.values.astype(float)
    exp = np.outer(o.sum(axis=1), o.sum(axis=0)) / o.sum()
    return pd.DataFrame(exp, index=obs.index, columns=obs.columns)


def get_contributions(obs: pd.DataFrame, exp: pd.DataFrame) -> pd.DataFrame:
    """Har cell ka (O - E)^2 / E"""
    return (obs.astype(float) - exp) ** 2 / exp


def chi_square_stat(obs: pd.DataFrame, exp: pd.DataFrame) -> float:
    """chi2 = sum of (O - E)^2 / E"""
    return float(get_contributions(obs, exp).values.sum())


def get_df(obs: pd.DataFrame) -> int:
    """df = (rows - 1) x (columns - 1)"""
    r, c = obs.shape
    return (r - 1) * (c - 1)


def get_critical(alpha: float, df: int) -> float:
    """Critical value: right-tail area = alpha"""
    return float(chi2.ppf(1 - alpha, df))


def get_p_value(stat: float, df: int) -> float:
    """p-value = P(chi2 >= calculated value)"""
    return float(chi2.sf(stat, df))


def cramers_v(stat: float, n: float, shape: tuple) -> float:
    """Effect size (0 = no relation, 1 = perfect relation)"""
    k = min(shape[0] - 1, shape[1] - 1)
    return float(np.sqrt(stat / (n * k))) if k > 0 and n > 0 else float("nan")


def validate_table(obs: pd.DataFrame):
    """Bekaar tables par error do (zero row/column, negative numbers wagairah)."""
    if obs.shape[0] < 2 or obs.shape[1] < 2:
        raise ValueError("Table must have at least 2 rows and 2 columns.")
    o = obs.values.astype(float)
    if np.isnan(o).any() or (o < 0).any():
        raise ValueError("Counts must be non-negative numbers.")
    if o.sum() == 0:
        raise ValueError("The table is empty (all counts are zero).")
    if (o.sum(axis=1) == 0).any() or (o.sum(axis=0) == 0).any():
        raise ValueError("A row or column has a total of zero - remove it or add data.")


def run_test(obs: pd.DataFrame, alpha: float = 0.05) -> dict:
    """Poora test ek saath chalao aur result dictionary me do."""
    obs = obs.astype(int)
    validate_table(obs)
    exp = get_expected(obs)
    contrib = get_contributions(obs, exp)
    stat = chi_square_stat(obs, exp)
    df = get_df(obs)
    crit = get_critical(alpha, df)
    p = get_p_value(stat, df)
    n = int(obs.values.sum())

    # scipy se cross-check
    s_stat, s_p, s_df, _ = chi2_contingency(obs.values, correction=False)
    verified = bool(np.isclose(stat, s_stat) and np.isclose(p, s_p) and df == s_df)

    result = {
        "observed": obs, "expected": exp, "contrib": contrib,
        "chi2": stat, "df": df, "critical": crit, "p": p, "alpha": alpha,
        "n": n, "reject": bool(stat > crit),
        "cramers_v": cramers_v(stat, n, obs.shape),
        "verified": verified,
        "min_expected": float(exp.values.min()),
        "cells_below_5": int((exp.values < 5).sum()),
        "yates_chi2": None, "yates_p": None,
    }
    if obs.shape == (2, 2):  # Yates correction sirf 2x2 me
        y_stat, y_p, _, _ = chi2_contingency(obs.values, correction=True)
        result["yates_chi2"], result["yates_p"] = float(y_stat), float(y_p)
    return result
