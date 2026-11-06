"""Placing limited flexible hydro energy against the deficits of one month.

All functions take the deficit before flexible hydro, D_t = max(0, N_t - K) >= 0 (MW), for
the half-hours of ONE month, in any order: the results do not depend on the order.

- ``water_fill``: one resource (lakes), closed form. Used for the baseline.
- ``min_shortfall_lp``: any number of resources, by linear programming (HiGHS). Used for
  the flexible pumped-storage variant, and in the tests as an independent reference.
"""

from __future__ import annotations

import numpy as np
from scipy import sparse
from scipy.optimize import linprog

from src.adequacy.data import DT_H

SHORTFALL_TOL_MW = 1e-3  # below 1 kW a half-hour is not counted as short (numerical noise)
BISECTION_STEPS = 100  # halving [0, max D] 100 times reaches floating-point resolution


def covered_energy(deficit: np.ndarray, cap: float, theta: float, dt: float = DT_H) -> float:
    """F(theta) = dt * sum_t min(cap, max(0, D_t - theta)): lake energy used at level theta (MWh)."""
    return float(dt * np.minimum(cap, np.maximum(0.0, deficit - theta)).sum())


def water_fill(
    deficit: np.ndarray, cap: float, budget: float, dt: float = DT_H
) -> tuple[np.ndarray, float]:
    """Lake output l_t (MW) that shaves the highest deficits first, and the level theta.

    l_t = min(cap, max(0, D_t - theta)), with
    - theta = 0 if F(0) <= budget (the budget does not bind), otherwise
    - theta = the smallest theta >= 0 with F(theta) <= budget; F is continuous, so then
      F(theta) = budget: the whole budget is used.

    ``cap`` and ``budget`` may be ``np.inf``.
    """
    deficit = np.asarray(deficit, dtype=float)
    if deficit.size == 0 or covered_energy(deficit, cap, 0.0, dt) <= budget:
        theta = 0.0
    else:
        # F is non-increasing in theta. Invariant: F(lo) > budget and F(hi) <= budget
        # (F(max D) = 0 <= budget). Returning hi guarantees the budget is respected.
        lo, hi = 0.0, float(deficit.max())
        for _ in range(BISECTION_STEPS):
            mid = 0.5 * (lo + hi)
            if covered_energy(deficit, cap, mid, dt) <= budget:
                hi = mid
            else:
                lo = mid
        theta = hi
    lake = np.minimum(cap, np.maximum(0.0, deficit - theta))
    return lake, theta


def min_shortfall_lp(
    deficit: np.ndarray, resources: list[tuple[float, float]], objective: str, dt: float = DT_H
) -> np.ndarray:
    """Shortfall s_t (MW) of an optimal joint allocation of several energy-limited resources.

    ``resources`` is a list of (power limit MW, energy budget MWh); either may be ``np.inf``.
    Variables: x[r, t] in [0, cap_r] for each resource r, s_t >= 0, and z for "peak".

        x[1, t] + ... + x[k, t] + s_t = D_t          for every t   (supply meets the deficit)
        dt * sum_t x[r, t] <= budget_r              for every r   (energy budget)

    objective "energy": minimise dt * sum_t s_t (unmet energy).
    objective "peak":   minimise z subject to s_t <= z (largest shortfall).

    The equality with s_t >= 0 also forbids supplying more than the deficit.
    Only the optimal objective value is meaningful: several allocations can reach it.
    """
    D = np.asarray(deficit, dtype=float)
    n, k = D.size, len(resources)
    peak = objective == "peak"
    if objective not in ("energy", "peak"):
        raise ValueError(f"objective must be 'energy' or 'peak', not {objective!r}")
    # Variable layout: [x[0, :], ..., x[k-1, :], s[:], (z)].
    n_var = k * n + n + int(peak)
    c = np.zeros(n_var)
    if peak:
        c[-1] = 1.0
    else:
        c[k * n:k * n + n] = dt

    eye = sparse.identity(n, format="csr")
    blocks = [eye] * (k + 1)  # one identity per resource, then one for s
    if peak:
        blocks.append(sparse.csr_matrix((n, 1)))  # z does not appear in the balance
    a_eq = sparse.hstack(blocks, format="csr")

    ub_rows, b_ub = [], []
    for r, (_, budget) in enumerate(resources):
        if np.isfinite(budget):
            row = np.zeros(n_var)
            row[r * n:(r + 1) * n] = dt
            ub_rows.append(sparse.csr_matrix(row))
            b_ub.append(budget)
    if peak:
        # s_t - z <= 0 for every t.
        ub_rows.append(sparse.hstack(
            [sparse.csr_matrix((n, k * n)), eye, -np.ones((n, 1))], format="csr"))
        b_ub.extend([0.0] * n)
    a_ub = sparse.vstack(ub_rows, format="csr") if ub_rows else None

    bounds = [(0.0, cap if np.isfinite(cap) else None) for cap, _ in resources for _ in range(n)]
    bounds += [(0.0, None)] * (n + int(peak))
    res = linprog(c, A_ub=a_ub, b_ub=b_ub or None, A_eq=a_eq, b_eq=D,
                  bounds=bounds, method="highs")
    if res.status != 0:
        raise RuntimeError(f"LP not solved to optimality: {res.message}")
    # HiGHS can return values like -1e-12 for a variable at its zero bound.
    return np.maximum(res.x[k * n:k * n + n], 0.0)


def shortfall_metrics(shortfall: np.ndarray, dt: float = DT_H) -> dict:
    """Unmet energy (MWh), peak shortfall (MW) and hours short of a shortfall series."""
    s = np.asarray(shortfall, dtype=float)
    return {
        "unmet_mwh": float(s.sum() * dt),
        "peak_mw": float(s.max()) if s.size else 0.0,
        "hours_short": float((s > SHORTFALL_TOL_MW).sum() * dt),
    }
