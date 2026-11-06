"""Run the adequacy pipeline on the two eCO2mix years and write the results.

Usage, from the repository root (raw files stay in the gitignored ``data/`` folder):

    python -m src.adequacy.run --y2019 data/eco2mix_2019.csv --y2022 data/eco2mix_2022.csv

Options:
    --capacities FILE            installed capacities with sources (default inputs/capacities.csv)
    --availability-2019 FILE     half-hourly reconstructed availability for 2019 (and 2022),
    --availability-2022 FILE     columns ts_utc, nucleaire, gaz, charbon, fioul (MW)
    --out DIR                    output folder (default results/, gitignored)

Outputs: ``adequacy_results.json`` (everything), and ``scenarios.csv``,
``monthly_unmet.csv``, ``shapley.csv`` (the tables the figure will use).
Internal units are MW and MWh; outputs are GW and GWh.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from src.adequacy.checks import (
    availability_vs_generation,
    balance_residual,
    hydro_capacity_check,
    import_comparison,
    run_test_b,
)
from src.adequacy.data import DT_H, completeness, load_year
from src.adequacy.inputs import (
    AVAILABILITY_TECHNOLOGIES,
    aggregate_availability,
    align_availability,
    demand_side,
    generation_based_availability,
    hydro_capacity,
    installed_fossil,
    load_availability,
    load_capacities,
    monthly_budgets,
    observed_fossil_max,
)
from src.adequacy.scenarios import (
    PUMPED_STORAGE_VARIANTS,
    SCENARIOS,
    attribute,
    evaluate,
    run_four_scenarios,
)

YEARS = (2019, 2022)
PRE_REGISTERED_TEST_B_CASE = "reconstructed+monthly_mean"  # v6 section 8.3
NUCLEAR_STATS = {"mean": "monthly mean", "max": "monthly maximum"}


def build_cases(years: dict, capacities: dict, aligned: dict | None) -> dict[str, dict]:
    """Availability cases: name -> description, kind, monthly K_m per year, frozen-fossil rule."""
    fossil_options = {"fos_obsmax": (
        {y: observed_fossil_max(df) for y, df in years.items()},
        "fossil = sum of each technology's highest observed output in the year")}
    installed = {y: installed_fossil(capacities, y) for y in years}
    if None not in installed.values():
        fossil_options["fos_installed"] = (installed, "fossil = installed capacity (sourced)")

    cases = {}
    for stat, stat_name in NUCLEAR_STATS.items():
        for fos_key, (fossil_mw, fos_desc) in fossil_options.items():
            cases[f"nuc_{stat}+{fos_key}"] = {
                "kind": "generation-based sensitivity case",
                "description": f"nuclear = {stat_name} of observed generation; {fos_desc}",
                "monthly": {y: generation_based_availability(years[y], stat, fossil_mw[y])
                            for y in years},
                # Frozen-fossil diagnostic: nuclear of year y, fossil of the frozen year f.
                # The default arguments s=stat, mw=fossil_mw freeze this loop's values;
                # without them every lambda would see the last loop iteration.
                "frozen": lambda y, f, s=stat, mw=fossil_mw: generation_based_availability(
                    years[y], s, mw[f]),
            }
    if aligned is not None:
        totals = {y: aligned[y][list(AVAILABILITY_TECHNOLOGIES)].sum(axis=1) for y in years}
        for method in ("monthly_mean", "lowest_daily_mean"):
            cases[f"reconstructed+{method}"] = {
                "kind": "reconstructed availability",
                "description": f"reconstructed half-hourly availability, {method.replace('_', ' ')}",
                "monthly": {y: aggregate_availability(totals[y], years[y], method) for y in years},
                "frozen": None,  # added with the ENTSO-E reconstruction
            }
    return cases


def result_row(case: str, ps: str, label: str, r) -> dict:
    year_d, year_a = SCENARIOS[label]
    return {"case": case, "pumped_storage": ps, "scenario": label, "year_D": year_d,
            "year_A": year_a, "unmet_gwh": r.unmet_mwh / 1e3, "peak_gw": r.peak_mw / 1e3,
            "hours_short": r.hours_short}


def shapley_dict(s, scale: float) -> dict:
    return {"total": s.total / scale, "phi_D": s.phi_d / scale, "phi_A": s.phi_a / scale,
            "interaction": s.interaction / scale}


def run(args: argparse.Namespace) -> dict:
    years = {2019: load_year(args.y2019, 2019), 2022: load_year(args.y2022, 2022)}
    capacities = load_capacities(args.capacities) if Path(args.capacities).exists() else {}
    demand = {y: demand_side(df) for y, df in years.items()}
    lake = hydro_capacity(capacities, years, "lakes", "hydraulique_lacs")
    ps = hydro_capacity(capacities, years, "pumped_storage_generation", "hydraulique_step_turbinage")
    lake_cap = {y: v["mw"] for y, v in lake.items()}
    ps_cap = {y: v["mw"] for y, v in ps.items()}

    aligned = None
    if args.availability_2019 and args.availability_2022:
        raw = {2019: load_availability(args.availability_2019),
               2022: load_availability(args.availability_2022)}
        aligned = {y: align_availability(raw[y], years[y]) for y in YEARS}

    report: dict = {"data": {}, "hydro_power_limits": {"lakes": lake, "pumped_storage": ps},
                    "checks": {}, "cases": {}, "test_b": [], "import_comparison": {},
                    "frozen_fossil": {}, "half_hourly_availability": {}}
    for y, df in years.items():
        budgets = monthly_budgets(demand[y])
        report["data"][y] = {
            "completeness": completeness(df),
            "annual_twh": {
                "consumption": float(df["consommation"].sum() * DT_H / 1e6),
                "net_demand_baseline": float(demand[y]["net_demand_baseline"].sum() * DT_H / 1e6),
                "net_demand_flexible": float(demand[y]["net_demand_flexible"].sum() * DT_H / 1e6),
                "lake_budget": float(budgets["lake_budget_mwh"].sum() / 1e6),
                "pumped_storage_budget": float(budgets["ps_budget_mwh"].sum() / 1e6),
                "pumping": float(demand[y]["pumping"].sum() * DT_H / 1e6),
                "net_imports": float(df["ech_physiques"].sum() * DT_H / 1e6),
            },
            "monthly_budgets_gwh": (budgets / 1e3).rename(columns={
                "lake_budget_mwh": "lake_gwh", "ps_budget_mwh": "pumped_storage_gwh"}
            ).to_dict(orient="index"),
        }
        report["checks"][y] = {
            "balance_residual": balance_residual(df),
            "lake_capacity": hydro_capacity_check(lake_cap[y], df["hydraulique_lacs"]),
            "pumped_storage_capacity": hydro_capacity_check(
                ps_cap[y], df["hydraulique_step_turbinage"]),
        }
        if aligned is not None:
            report["checks"][y]["availability_vs_generation"] = availability_vs_generation(
                aligned[y], df)
    report["checks"]["same_rows_per_month_in_both_years"] = (
        report["data"][2019]["completeness"]["rows_per_month"]
        == report["data"][2022]["completeness"]["rows_per_month"])

    cases = build_cases(years, capacities, aligned)
    rows, monthly_rows, shapley_rows = [], [], []
    for case, spec in cases.items():
        report["cases"][case] = {"kind": spec["kind"], "description": spec["description"],
                                 "monthly_availability_gw": {
                                     y: (spec["monthly"][y] / 1e3).to_dict() for y in YEARS},
                                 "results": {}}
        for ps_mode in PUMPED_STORAGE_VARIANTS:
            results = run_four_scenarios(demand, spec["monthly"], lake_cap, ps_cap, ps_mode)
            shares = attribute(results)
            report["cases"][case]["results"][ps_mode] = {
                "scenarios": {k: result_row(case, ps_mode, k, r) for k, r in results.items()},
                "shapley_unmet_gwh": shapley_dict(shares["unmet_mwh"], 1e3),
                "shapley_peak_gw": shapley_dict(shares["peak_mw"], 1e3),
                "shapley_unmet_gwh_by_month": {
                    m: shapley_dict(s, 1e3) for m, s in shares["unmet_mwh_by_month"].items()},
            }
            rows += [result_row(case, ps_mode, k, r) for k, r in results.items()]
            monthly_rows += [
                {"case": case, "pumped_storage": ps_mode, "scenario": k, "month": m,
                 "unmet_gwh": u / 1e3, "peak_gw": r.peak_mw_by_month[m] / 1e3}
                for k, r in results.items() for m, u in r.unmet_mwh_by_month.items()]
            for metric, key, scale in (("unmet_gwh", "unmet_mwh", 1e3), ("peak_gw", "peak_mw", 1e3)):
                shapley_rows.append({"case": case, "kind": spec["kind"], "pumped_storage": ps_mode,
                                     "metric": metric, **shapley_dict(shares[key], scale)})

            if ps_mode == "flexible":
                report["test_b"].append(run_test_b(
                    results["A1"].unmet_mwh, case, case == PRE_REGISTERED_TEST_B_CASE))
            if ps_mode == "baseline":
                report["import_comparison"][case] = {
                    "A1_vs_2019": import_comparison(results["A1"].shortfall, years[2019]),
                    "A4_vs_2022": import_comparison(results["A4"].shortfall, years[2022])}
                if spec["frozen"] is not None:
                    frozen = {}
                    for f in YEARS:
                        avail_f = {y: spec["frozen"](y, f) for y in YEARS}
                        s = attribute(run_four_scenarios(demand, avail_f, lake_cap, ps_cap, ps_mode))
                        frozen[f"fossil_frozen_at_{f}"] = {
                            "shapley_unmet_gwh": shapley_dict(s["unmet_mwh"], 1e3),
                            "shapley_peak_gw": shapley_dict(s["peak_mw"], 1e3)}
                    report["frozen_fossil"][case] = frozen

    if aligned is not None:
        # Aggregation effect, actual years only: half-hourly K_t instead of monthly constants.
        for label, y in (("A1", 2019), ("A4", 2022)):
            total = aligned[y][list(AVAILABILITY_TECHNOLOGIES)].sum(axis=1)
            for ps_mode in PUMPED_STORAGE_VARIANTS:
                r = evaluate(demand[y], total, lake_cap[y], ps_cap[y], ps_mode)
                report["half_hourly_availability"][f"{label}_{ps_mode}"] = {
                    "unmet_gwh": r.unmet_mwh / 1e3, "peak_gw": r.peak_mw / 1e3}

    # Sensitivity range: smallest and largest value of each quantity across the cases of
    # one kind. It is a spread across assumptions, not a confidence interval.
    shapley_table = pd.DataFrame(shapley_rows)
    report["sensitivity_range"] = {}
    for (kind, ps_mode, metric), group in shapley_table.groupby(["kind", "pumped_storage", "metric"]):
        report["sensitivity_range"][f"{kind} | {ps_mode} | {metric}"] = {
            q: {"min": float(group[q].min()), "max": float(group[q].max())}
            for q in ("total", "phi_D", "phi_A", "interaction")}

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out / "scenarios.csv", index=False, float_format="%.4f")
    pd.DataFrame(monthly_rows).to_csv(out / "monthly_unmet.csv", index=False, float_format="%.4f")
    shapley_table.to_csv(out / "shapley.csv", index=False, float_format="%.4f")
    # default=str turns dates and other non-JSON values into text instead of failing.
    (out / "adequacy_results.json").write_text(json.dumps(report, indent=2, default=str))
    return report


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--y2019", type=Path, required=True)
    ap.add_argument("--y2022", type=Path, required=True)
    ap.add_argument("--capacities", type=Path, default=Path("inputs/capacities.csv"))
    ap.add_argument("--availability-2019", type=Path)
    ap.add_argument("--availability-2022", type=Path)
    ap.add_argument("--out", type=Path, default=Path("results"))
    return ap.parse_args(argv)


if __name__ == "__main__":
    report = run(parse_args())
    print(json.dumps({"test_b": report["test_b"], "sensitivity_range": report["sensitivity_range"]},
                     indent=2, default=str))
