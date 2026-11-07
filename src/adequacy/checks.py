"""Physical-consistency checks, Test B, and the comparison with observed net imports.

None of these validates the attribution. They test whether the reconstruction is
consistent with what France observably did (docs/adequacy_model.md, section 6).
"""

from __future__ import annotations

import pandas as pd

from src.adequacy.allocation import SHORTFALL_TOL_MW
from src.adequacy.data import DT_H, FOSSIL, GENERATION

TEST_B_THRESHOLD_MWH = 36_000.0  # 36 GWh, pre-registered in docs/check_protocol_v6.md, 8.3


def balance_residual(df: pd.DataFrame) -> dict:
    """Residual of C_t = sum_k P_k,t + pompage_t + ech_physiques_t (signs from check 1), MW."""
    residual = df["consommation"] - df[GENERATION].sum(axis=1) - df["pompage"] - df["ech_physiques"]
    return {
        "mean_mw": float(residual.mean()),
        "mean_abs_mw": float(residual.abs().mean()),
        "max_abs_mw": float(residual.abs().max()),
        "annual_twh": float(residual.sum() * DT_H / 1e6),
    }


def availability_vs_generation(availability: pd.DataFrame, df: pd.DataFrame) -> dict:
    """Raw half-hourly availability against observed generation, at matching intervals.

    ``availability`` has a ``ts_utc`` column and one column per technology, named like the
    eCO2mix generation columns (``nucleaire``, ``gaz``, ``charbon``, ``fioul``), in MW.
    Physically, availability >= generation in every interval. Run this BEFORE any monthly
    aggregation: it checks the reconstructed series itself, not the model.

    Rows flagged ``dst_pass_uncertain`` (the autumn repeated hour) are left out: their UTC
    instant, and so their matching interval, is not established (D26).
    """
    uncertain = df["dst_pass_uncertain"]
    merged = df.loc[~uncertain, ["ts_utc", "nucleaire", *FOSSIL]].merge(
        availability, on="ts_utc", how="inner", suffixes=("_gen", "_avail"))
    report = {"matched_half_hours": len(merged), "eco2mix_half_hours": len(df),
              "excluded_dst_pass_uncertain": int(uncertain.sum())}
    for tech in ["nucleaire", *FOSSIL]:
        if tech not in availability.columns:
            continue
        excess = (merged[f"{tech}_gen"] - merged[f"{tech}_avail"]).clip(lower=0.0)
        violating = excess > 0
        report[tech] = {
            "violating_half_hours": int(violating.sum()),
            "violation_energy_mwh": float(excess.sum() * DT_H),
            "largest_violation_mw": float(excess.max()) if len(excess) else 0.0,
        }
    return report


def hydro_capacity_check(capacity_mw: float, observed: pd.Series) -> dict:
    """A hydro power limit must be at least the highest observed output it has to allow."""
    highest = float(observed.max())
    return {"capacity_mw": capacity_mw, "highest_observed_mw": highest,
            "ok": capacity_mw >= highest}


def run_test_b(unmet_a1_mwh: float, configuration: str, pre_registered: bool) -> dict:
    """Test B (v6 section 8.3): modelled 2019 unmet energy <= 36 GWh.

    Pre-registered configuration: A1, ENTSO-E availability with monthly-mean aggregation,
    flexible pumped storage. Any other configuration is reported, with
    ``pre_registered=False``, as a sensitivity, not as the test.
    """
    return {
        "configuration": configuration,
        "pre_registered_configuration": pre_registered,
        "unmet_gwh": unmet_a1_mwh / 1e3,
        "threshold_gwh": TEST_B_THRESHOLD_MWH / 1e3,
        "within_tolerance": unmet_a1_mwh <= TEST_B_THRESHOLD_MWH,
    }


def import_comparison(shortfall: pd.Series, df: pd.DataFrame) -> dict:
    """Modelled shortfall of an actual year (A1 or A4) against observed net imports X_t.

    X_t = ``ech_physiques``: net physical imports (imports minus exports), import-positive
    (check 1). The time-matched part uses the timing of the allocation that produced
    ``shortfall`` (water-filling for the baseline), which is one optimal allocation among
    many. Nothing here shows how much import was necessary (D18).
    """
    x = df["ech_physiques"].to_numpy()
    s = shortfall.to_numpy()
    short = s > SHORTFALL_TOL_MW
    gwh = DT_H / 1e3  # MW summed over half-hours -> GWh
    at_peak = int(s.argmax())
    return {
        "annual_net_imports_gwh": float(x.sum() * gwh),
        "net_imports_over_net_importing_half_hours_gwh": float(x.clip(min=0.0).sum() * gwh),
        "peak_net_import_gw": float(x.max() / 1e3),
        "modelled_unmet_gwh": float(s.sum() * gwh),
        "modelled_peak_shortfall_gw": float(s.max() / 1e3),
        "time_matched": {
            "note": "timing from the allocation rule used (one optimal allocation among many)",
            "short_half_hours": int(short.sum()),
            "share_of_short_half_hours_with_net_imports": (
                float((x[short] > 0).mean()) if short.any() else None),
            "net_imports_during_short_half_hours_gwh": float(x[short].sum() * gwh),
            "shortfall_above_observed_net_imports_gwh": float(
                (s - x.clip(min=0.0)).clip(min=0.0).sum() * gwh),
            "net_import_at_peak_shortfall_gw": float(x[at_peak] / 1e3) if short.any() else None,
        },
    }
