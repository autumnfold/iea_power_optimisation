"""Inputs of the two drivers, built from one loaded year (see ``data.load_year``).

Driver D (demand and resource conditions, D16): net demand, lake and pumped-storage budgets.
Driver A (conventional availability, D16): nuclear plus fossil available capacity per month.

Symbols follow docs/adequacy_model.md: C consumption, W wind, S solar, R run-of-river and
pondage, B bioenergy, p >= 0 pumping, g_obs observed pumped-storage generation.
"""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd

from src.adequacy.data import DT_H, FOSSIL


def demand_side(df: pd.DataFrame) -> pd.DataFrame:
    """Half-hourly driver-D quantities of one year (MW), row-aligned with ``df``."""
    pumping = -df["pompage"]  # p_t = -pompage_t >= 0 (pompage <= 0 is checked on load)
    g_obs = df["hydraulique_step_turbinage"]
    # C - W - S - R - B: demand left after the generation that is taken as observed in
    # every pumped-storage variant.
    before_storage = (
        df["consommation"] - df["eolien"] - df["solaire"]
        - df["hydraulique_fil_eau_eclusee"] - df["bioenergies"]
    )
    return pd.DataFrame({
        "ts_utc": df["ts_utc"],
        "month": df["month"],
        # Baseline (D19): subtract the observed net pumped-storage profile g_obs - p.
        "net_demand_baseline": before_storage - (g_obs - pumping),
        # Flexible: observed pumping stays as load; g_obs is NOT subtracted, because the
        # model chooses pumped-storage generation itself (a decision variable).
        "net_demand_flexible": before_storage + pumping,
        "lake_output": df["hydraulique_lacs"],
        "ps_generation": g_obs,
        "pumping": pumping,
    })


def monthly_budgets(ds: pd.DataFrame) -> pd.DataFrame:
    """Monthly energy budgets (MWh): E^L_m for lakes and E^T_m for pumped-storage generation."""
    by_month = ds.groupby("month")
    return pd.DataFrame({
        "lake_budget_mwh": by_month["lake_output"].sum() * DT_H,
        "ps_budget_mwh": by_month["ps_generation"].sum() * DT_H,
    })


# ---------------------------------------------------------------- driver A: availability

def observed_fossil_max(df: pd.DataFrame) -> float:
    """Sum over gas, coal and oil of each technology's highest observed output in the year (MW).

    Each technology's maximum may occur at a different time, so this is not the highest
    simultaneous fossil output. It is the convention of check 1 (13,658 MW in 2019).
    """
    return float(df[FOSSIL].max().sum())


def generation_based_availability(df: pd.DataFrame, nuclear: str, fossil_mw: float) -> pd.Series:
    """Fallback sensitivity case: monthly constant availability K_m (MW), indexed by month.

    ``nuclear`` is "mean" or "max": the monthly mean or maximum of observed nuclear
    generation. These are assumptions, not bounds on available capacity: generation can
    sit below availability (modulation, exports) and the monthly maximum is reached in
    one half-hour only.
    """
    if nuclear not in ("mean", "max"):
        raise ValueError(f"nuclear must be 'mean' or 'max', not {nuclear!r}")
    return df.groupby("month")["nucleaire"].agg(nuclear) + fossil_mw


def aggregate_availability(total: pd.Series, df: pd.DataFrame, method: str) -> pd.Series:
    """Monthly constant K_m (MW) from a half-hourly total availability series a_t.

    ``total`` is nuclear plus fossil availability, already summed at each half-hour and
    row-aligned with ``df``. Methods:
    - "monthly_mean": K_m = mean of a_t over the half-hours of month m;
    - "lowest_daily_mean": daily mean of a_t over each local calendar day (over the
      half-hours present that day, 46 or 50 on clock-change days), then the lowest day of
      the month.
    """
    if method == "monthly_mean":
        return total.groupby(df["month"]).mean()
    if method == "lowest_daily_mean":
        daily = total.groupby([df["month"], df["day"]]).mean()
        return daily.groupby(level="month").min()
    raise ValueError(f"unknown aggregation method {method!r}")


AVAILABILITY_TECHNOLOGIES = ("nucleaire", *FOSSIL)


def load_availability(path: Path) -> pd.DataFrame:
    """Half-hourly reconstructed availability (MW): columns ``ts_utc`` and technologies.

    This is the interface the ENTSO-E reconstruction (v6 section 6) will write to; the
    reconstruction itself is built once the download's fields are known.
    """
    avail = pd.read_csv(path)
    avail["ts_utc"] = pd.to_datetime(avail["ts_utc"], utc=True)
    missing = [t for t in AVAILABILITY_TECHNOLOGIES if t not in avail.columns]
    if missing:
        raise ValueError(f"{path}: missing technologies {missing}")
    if avail["ts_utc"].duplicated().any():
        raise ValueError(f"{path}: duplicate timestamps")
    return avail[["ts_utc", *AVAILABILITY_TECHNOLOGIES]]


def align_availability(avail: pd.DataFrame, df: pd.DataFrame) -> pd.DataFrame:
    """Availability for each row of ``df``, matched on the same UTC half-hour."""
    # how="left" keeps df's rows and order; a duplicated eCO2mix timestamp gets the same
    # availability on both rows, because both rows refer to the same instant.
    aligned = df[["ts_utc"]].merge(avail, on="ts_utc", how="left")
    aligned.index = df.index
    if aligned[list(AVAILABILITY_TECHNOLOGIES)].isna().any().any():
        raise ValueError("availability is missing for some eCO2mix half-hours")
    return aligned


# ------------------------------------------------------------- installed capacities file

CAPACITY_TECHNOLOGIES = ("lakes", "pumped_storage_generation", "gas", "coal", "oil")


def load_capacities(path: Path) -> dict[tuple[int, str], float]:
    """Installed capacities (MW) from ``inputs/capacities.csv``, keyed by (year, technology).

    Rows with an empty ``capacity_mw`` are not sourced yet and are skipped. A value without
    a source is rejected: every numerical assumption needs one (ASSUMPTIONS.md).
    """
    # No comment character: a source text or URL may legitimately contain '#'.
    table = pd.read_csv(path, dtype=str).fillna("")
    capacities = {}
    for row in table.itertuples(index=False):
        if row.capacity_mw.strip() == "":
            continue
        if row.technology not in CAPACITY_TECHNOLOGIES:
            raise ValueError(f"unknown technology {row.technology!r} in {path}")
        if row.source.strip() == "":
            raise ValueError(f"{path}: capacity for {row.year} {row.technology} has no source")
        capacities[(int(row.year), row.technology)] = float(row.capacity_mw)
    return capacities


def hydro_capacity(
    capacities: dict, years_data: dict[int, pd.DataFrame], technology: str, column: str
) -> dict[int, dict]:
    """Power limit per year for lakes (K^L) or pumped-storage generation (K^T).

    Installed capacity when it is sourced for every year. Otherwise the highest observed
    output over all years, the same value in each year: an observed-output proxy, which is
    a lower bound on the installed capacity, not the installed capacity itself.
    """
    if all((y, technology) in capacities for y in years_data):
        return {y: {"mw": capacities[(y, technology)], "basis": "installed capacity (sourced)"}
                for y in years_data}
    proxy = max(float(df[column].max()) for df in years_data.values())
    basis = "observed-output proxy: highest observed output, a lower bound on installed capacity"
    return {y: {"mw": proxy, "basis": basis} for y in years_data}


def installed_fossil(capacities: dict, year: int) -> float | None:
    """Installed gas + coal + oil capacity (MW) for ``year``, or None if any is unsourced."""
    values = [capacities.get((year, t)) for t in ("gas", "coal", "oil")]
    return None if None in values else math.fsum(values)
