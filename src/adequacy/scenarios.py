"""The four scenarios of the two-driver attribution, and their adequacy metrics.

A scenario takes ALL driver-D inputs (net demand, lake and pumped-storage budgets, hydro
power limits) from year d_D and ALL driver-A inputs (monthly availability) from year d_A.
Monthly availability is constant within a month, so only the distribution of net demand
within each month matters: a 2022 month can be combined with 2019 availability.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import pandas as pd

from src.adequacy.allocation import min_shortfall_lp, shortfall_metrics, water_fill
from src.adequacy.inputs import monthly_budgets
from src.adequacy.shapley import TwoPlayerShapley, shapley_two_players

# label: (year of driver D, year of driver A)
SCENARIOS = {"A1": (2019, 2019), "A2": (2022, 2019), "A3": (2019, 2022), "A4": (2022, 2022)}
PUMPED_STORAGE_VARIANTS = ("baseline", "flexible")


@dataclass
class AdequacyResult:
    unmet_mwh: float
    peak_mw: float
    hours_short: float  # depends on the allocation rule; not an optimised metric
    unmet_mwh_by_month: dict[int, float]
    peak_mw_by_month: dict[int, float]
    shortfall: pd.Series  # half-hourly s_t (MW), row-aligned with the demand-side frame


def evaluate(
    ds: pd.DataFrame, availability: pd.Series, lake_cap: float, ps_cap: float, pumped_storage: str
) -> AdequacyResult:
    """Adequacy metrics of one year of demand-side data against an availability series.

    ``availability`` is K (MW) for each row of ``ds``: a monthly constant repeated over the
    month's rows, or (A1 and A4 only) a half-hourly series.

    - "baseline": observed net pumped-storage profile inside net demand; lakes placed by
      water-filling, which minimises unmet energy and peak shortfall at the same time.
    - "flexible": pumped-storage generation is a decision variable placed jointly with lake
      water, by two LPs (unmet energy, then peak), which need not share one dispatch.
    """
    if pumped_storage not in PUMPED_STORAGE_VARIANTS:
        raise ValueError(f"unknown pumped-storage variant {pumped_storage!r}")
    if availability.isna().any():
        raise ValueError("availability is missing for some rows (a month without a value?)")
    column = "net_demand_baseline" if pumped_storage == "baseline" else "net_demand_flexible"
    deficit = (ds[column] - availability).clip(lower=0.0)  # D_t = max(0, N_t - K)
    budgets = monthly_budgets(ds)

    shortfall = pd.Series(0.0, index=ds.index)
    unmet_by_month, peak_by_month = {}, {}
    for month, rows in ds.groupby("month").groups.items():
        d = deficit.loc[rows].to_numpy()
        lake_budget = budgets.at[month, "lake_budget_mwh"]
        if pumped_storage == "baseline":
            lake, _theta = water_fill(d, lake_cap, lake_budget)
            s = d - lake
            peak = float(s.max())
        else:
            resources = [(lake_cap, lake_budget), (ps_cap, budgets.at[month, "ps_budget_mwh"])]
            s = min_shortfall_lp(d, resources, "energy")
            peak = float(min_shortfall_lp(d, resources, "peak").max())
        shortfall.loc[rows] = s
        unmet_by_month[int(month)] = shortfall_metrics(s)["unmet_mwh"]
        peak_by_month[int(month)] = peak

    hours = shortfall_metrics(shortfall.to_numpy())["hours_short"]
    return AdequacyResult(
        # math.fsum adds floats without accumulating rounding error.
        unmet_mwh=math.fsum(unmet_by_month.values()),
        # Months are independent, so the annual peak is the largest monthly peak.
        peak_mw=max(peak_by_month.values()),
        hours_short=hours,
        unmet_mwh_by_month=unmet_by_month,
        peak_mw_by_month=peak_by_month,
        shortfall=shortfall,
    )


def run_four_scenarios(
    demand: dict[int, pd.DataFrame],
    availability: dict[int, pd.Series],
    lake_cap: dict[int, float],
    ps_cap: dict[int, float],
    pumped_storage: str,
) -> dict[str, AdequacyResult]:
    """Evaluate A1-A4. ``availability[y]`` is monthly K_m of year y, indexed by month.

    Hydro power limits belong to driver D (v6 section 2), so they follow the d_D year.
    """
    results = {}
    for label, (year_d, year_a) in SCENARIOS.items():
        ds = demand[year_d]
        # Repeat each month's constant over that month's half-hours of the d_D year.
        k_rows = ds["month"].map(availability[year_a])
        results[label] = evaluate(ds, k_rows, lake_cap[year_d], ps_cap[year_d], pumped_storage)
    return results


def attribute(results: dict[str, AdequacyResult]) -> dict:
    """Shapley shares of the change in unmet energy and in peak shortfall.

    Unmet energy is a sum over months, so its attribution is also given month by month
    (the monthly shares add up to the annual ones). Peak shortfall is a maximum over the
    year: it has no monthly decomposition.
    """
    def shapley_of(values: dict[str, float]) -> TwoPlayerShapley:
        return shapley_two_players(values["A1"], values["A2"], values["A3"], values["A4"])

    months = sorted(set().union(*(r.unmet_mwh_by_month for r in results.values())))
    return {
        "unmet_mwh": shapley_of({k: r.unmet_mwh for k, r in results.items()}),
        "peak_mw": shapley_of({k: r.peak_mw for k, r in results.items()}),
        "unmet_mwh_by_month": {
            m: shapley_of({k: r.unmet_mwh_by_month.get(m, 0.0) for k, r in results.items()})
            for m in months
        },
    }
