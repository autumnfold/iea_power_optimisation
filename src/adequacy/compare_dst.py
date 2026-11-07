"""Before-and-after comparison of the clock-change policy (D26).

"Before" loads the files as published: the spring rows whose Paris label does not exist
are kept. "After" applies the policy and removes them. Validation, cases, pumped-storage
variants and scenarios are otherwise identical, so every difference comes from those rows.

Usage, from the repository root (same options as ``src.adequacy.run``):

    python -m src.adequacy.compare_dst --y2019 data/eco2mix_2019.csv --y2022 data/eco2mix_2022.csv

Writes ``dst_comparison.csv`` to ``--out`` and prints every quantity that changed.
Relative difference = (after - before) / |before|. It is 0 when both are 0 and left
empty (undefined) when only "before" is 0.
"""

from __future__ import annotations

import argparse

import numpy as np
import pandas as pd

from src.adequacy.data import DT_H
from src.adequacy.inputs import demand_side, monthly_budgets
from src.adequacy.run import analyse, load_inputs, parse_args

KEYS = ["section", "year", "case", "pumped_storage", "scenario", "month", "quantity", "unit"]


def data_quantities(years: dict) -> list[dict]:
    """Annual energies and monthly hydro budgets of each year, as rows of the comparison."""
    rows = []
    for y, df in years.items():
        ds = demand_side(df)
        budgets = monthly_budgets(ds)
        annual = {
            ("consumption", "TWh"): df["consommation"].sum() * DT_H / 1e6,
            ("net_demand_baseline", "TWh"): ds["net_demand_baseline"].sum() * DT_H / 1e6,
            ("net_demand_flexible", "TWh"): ds["net_demand_flexible"].sum() * DT_H / 1e6,
            ("lake_budget", "GWh"): budgets["lake_budget_mwh"].sum() / 1e3,
            ("pumped_storage_budget", "GWh"): budgets["ps_budget_mwh"].sum() / 1e3,
            ("pumping", "GWh"): ds["pumping"].sum() * DT_H / 1e3,
        }
        rows += [{"section": "data", "year": y, "quantity": q, "unit": u, "value": float(v)}
                 for (q, u), v in annual.items()]
        for month, b in budgets.iterrows():
            rows += [{"section": "data_monthly", "year": y, "month": int(month), "quantity": q,
                      "unit": "GWh", "value": float(b[col] / 1e3)}
                     for q, col in (("lake_budget", "lake_budget_mwh"),
                                    ("pumped_storage_budget", "ps_budget_mwh"))]
    return rows


def result_quantities(scenarios: pd.DataFrame, monthly: pd.DataFrame, shapley: pd.DataFrame) -> list[dict]:
    """U, P and hours short per scenario, U per month, and the Shapley table, as rows."""
    rows = []
    for r in scenarios.itertuples():
        keys = {"case": r.case, "pumped_storage": r.pumped_storage, "scenario": r.scenario}
        rows += [{"section": "scenario", **keys, "quantity": "unmet_energy_U", "unit": "GWh", "value": r.unmet_gwh},
                 {"section": "scenario", **keys, "quantity": "peak_shortfall_P", "unit": "GW", "value": r.peak_gw},
                 {"section": "scenario", **keys, "quantity": "hours_short", "unit": "h", "value": r.hours_short}]
    rows += [{"section": "scenario_monthly", "case": r.case, "pumped_storage": r.pumped_storage,
              "scenario": r.scenario, "month": int(r.month), "quantity": "unmet_energy_U",
              "unit": "GWh", "value": r.unmet_gwh} for r in monthly.itertuples()]
    for r in shapley.itertuples():
        metric, unit = ("U", "GWh") if r.metric == "unmet_gwh" else ("P", "GW")
        rows += [{"section": "shapley", "case": r.case, "pumped_storage": r.pumped_storage,
                  "quantity": f"{name}({metric})", "unit": unit, "value": getattr(r, col)}
                 for name, col in (("total", "total"), ("phi_D", "phi_D"), ("phi_A", "phi_A"),
                                   ("interaction", "interaction"))]
    return rows


def _key_text(value) -> str:
    """Keys as text: '' for an unused key (so the merge matches it), 3 rather than 3.0."""
    if pd.isna(value):
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def as_table(rows: list[dict]) -> pd.DataFrame:
    table = pd.DataFrame(rows)
    for k in KEYS:
        table[k] = table[k].map(_key_text) if k in table else ""
    return table[[*KEYS, "value"]]


def compare(before: pd.DataFrame, after: pd.DataFrame) -> pd.DataFrame:
    """Join the two runs on every key and add absolute and relative differences."""
    table = before.merge(after, on=KEYS, how="outer", suffixes=("_before", "_after"),
                         validate="one_to_one")
    table["abs_diff"] = table["value_after"] - table["value_before"]
    with np.errstate(divide="ignore", invalid="ignore"):
        rel = table["abs_diff"] / table["value_before"].abs()
    both_zero = (table["value_before"] == 0) & (table["value_after"] == 0)
    table["rel_diff"] = rel.where(table["value_before"] != 0, np.where(both_zero, 0.0, np.nan))
    return table


def run_comparison(args: argparse.Namespace) -> pd.DataFrame:
    tables = []
    for apply_policy in (False, True):
        years, _audits, capacities, aligned = load_inputs(args, apply_dst_policy=apply_policy)
        _report, scenarios, monthly, shapley = analyse(years, capacities, aligned)
        tables.append(as_table(data_quantities(years) + result_quantities(scenarios, monthly, shapley)))
    table = compare(*tables)
    args.out.mkdir(parents=True, exist_ok=True)
    table.to_csv(args.out / "dst_comparison.csv", index=False, float_format="%.6g")
    return table


if __name__ == "__main__":
    result = run_comparison(parse_args())
    changed = result[result["abs_diff"] != 0]
    pd.set_option("display.width", 250)
    pd.set_option("display.max_rows", 500)
    print(f"{len(changed)} of {len(result)} quantities changed:")
    print(changed.to_string(index=False))
