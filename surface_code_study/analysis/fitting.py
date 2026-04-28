"""
Fitting utilities for surface code error suppression analysis.

Provides functions to:
- Fit the suppression factor Λ from PL vs d data
- Estimate the threshold p_c by fitting the scaling law
- Extrapolate PL at arbitrary (p, d) from fitted parameters

Mathematical model
------------------
For a surface code under a 데ukurized noise model with MWPM decoding,
the logical error rate follows:

    P_L(p, d) ≈ Λ(d) · p^(α(d))

where α(d) = (d+1)/2 in the single-error-dominant regime.
In practice, for finite d, the effective exponent is close to (d+1)/2
and the prefactor Λ(d) captures platform-specific advantages.

For a fixed platform, the scaling is approximately:

    P_L ≈ Λ · p^((d+1)/2)

so that:
    log(P_L) = log(Λ) + ((d+1)/2) · log(p)

References
----------
Fowler et al., PRA 86, 032324 (2012) — Section III.A
Fowler & Gidney, arXiv:2109.07086 (2021) — threshold estimation
"""

from __future__ import annotations

import numpy as np
from scipy import optimize, stats


def fit_suppression_factor(
    pl_values: np.ndarray,
    d_values: np.ndarray,
    p: float,
    pl_stds: np.ndarray | None = None,
) -> tuple[float, float]:
    """
    Fit Λ from measurements of PL at multiple d.

    Uses the model: PL ≈ Λ · p^((d+1)/2)
    Implemented as weighted linear regression on log₁₀ values.

    Parameters
    ----------
    pl_values : array of shape (N,)
        Measured PL values.
    d_values : array of shape (N,)
        Corresponding code distances.
    p : float
        Physical error rate used in all measurements.
    pl_stds : array of shape (N,) or None
        Standard deviations of PL values. If None, equal weights are used.

    Returns
    -------
    lambda_val : float
        Fitted suppression factor Λ.
    lambda_std : float
        Standard error on Λ from the regression.
    """
    x = (d_values + 1) / 2.0         # theoretical slope variable
    y = np.log10(pl_values.clip(min=1e-15))
    log_p = np.log10(p)

    if pl_stds is not None:
        # Weight by inverse variance in log space
        weights = 1.0 / np.log(10) / pl_stds.clip(min=1e-15)
        weights /= weights.sum()
    else:
        weights = np.ones(len(x)) / len(x)

    # Weighted mean of intercept
    slope_fixed = log_p
    residuals = y - slope_fixed * x
    log_lambda = np.sum(weights * residuals)
    sigma_log_lam = np.sqrt(np.sum(weights**2 * (residuals - log_lambda)**2))

    lambda_val = 10**log_lambda
    lambda_std = lambda_val * sigma_log_lam * np.log(10)

    return lambda_val, lambda_std


def fit_threshold(
    pl_matrix: np.ndarray,      # shape (N_d, N_p)
    d_values: np.ndarray,
    p_values: np.ndarray,
    pl_stds: np.ndarray | None = None,  # same shape as pl_matrix
) -> tuple[float, float]:
    """
    Estimate the threshold p_c by examining where PL vs p curves
    for different d intersect.

    Uses the ansatz: P_L = A(p - p_c)^((d+1)/2) for p > p_c
    and fits p_c from the data using nonlinear least squares.

    Parameters
    ----------
    pl_matrix : array (N_d, N_p)
        PL values for each d (rows) and each p (columns).
    d_values : array (N_d,)
    p_values : array (N_p,)
    pl_stds : array (N_d, N_p) or None

    Returns
    -------
    p_c : float
        Estimated threshold.
    p_c_std : float
        Approximate standard error.

    Notes
    -----
    This is a rough estimate; proper threshold estimation requires
    finite-size scaling analysis (see Fowler & Gidney 2021).
    """
    # We use a simple crossing-point method:
    # At the threshold, PL is the same for all d (up to corrections).
    # We look for p where the PL curves for adjacent d intersect.
    # The intersection p* satisfies: Λ1·p^((d1+1)/2) ≈ Λ2·p^((d2+1)/2)
    # → p* = (Λ1/Λ2)^(2/(d2-d1))

    if pl_matrix.ndim != 2:
        raise ValueError("pl_matrix must be 2D: (N_d, N_p)")

    p_c_estimates = []
    for i in range(len(d_values) - 1):
        d1, d2 = d_values[i], d_values[i + 1]
        # Use the high-p end where both are in the detectable range
        mask = (pl_matrix[i] > 1e-6) & (pl_matrix[i + 1] > 1e-6)
        if mask.sum() < 2:
            continue

        p_high = p_values[mask]
        pl1 = pl_matrix[i][mask]
        pl2 = pl_matrix[i + 1][mask]

        # Estimate ratio of Λ values from the highest-p point
        ratio = pl1[-1] / pl2[-1]
        x = (d1 + 1) / 2.0 - (d2 + 1) / 2.0
        if ratio > 0 and x != 0:
            p_star = ratio ** (2.0 / (d1 - d2))
            p_c_estimates.append(p_star)

    if not p_c_estimates:
        return np.nan, np.nan

    p_c = np.median(p_c_estimates)
    p_c_std = np.std(p_c_estimates) if len(p_c_estimates) > 1 else np.nan
    return float(p_c), float(p_c_std)


def extrapolate_pl(
    lambda_val: float,
    p: float,
    d: int,
) -> float:
    """
    Predict PL at arbitrary (p, d) from a fitted Λ.

    Uses: PL ≈ Λ · p^((d+1)/2)

    Parameters
    ----------
    lambda_val : float
        Fitted suppression factor for the platform.
    p : float
        Physical error rate.
    d : int
        Code distance.

    Returns
    -------
    float
        Predicted PL.
    """
    exponent = (d + 1) / 2.0
    return lambda_val * (p ** exponent)
