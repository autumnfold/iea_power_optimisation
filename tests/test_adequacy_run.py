"""End to end: the pipeline and the clock-change comparison on synthetic full years."""

import json

import pandas as pd
import pytest

from src.adequacy.compare_dst import run_comparison
from src.adequacy.data import DT_H, load_year
from src.adequacy.run import parse_args, run


@pytest.fixture
def inputs(tmp_path, odre_frame, write_csv):
    """Two synthetic years in the ODRE layout, with the clock-change quirks of 2019 and 2022."""
    frames, paths = {}, {}
    for year, seed, fill in ((2019, 60, "mixed_2019"), (2022, 61, "next")):
        frames[year] = odre_frame(year, seed=seed, spring_fill=fill)
        paths[year] = tmp_path / f"eco2mix_{year}.csv"
        write_csv(paths[year], frames[year])
    return frames, paths


def write_availability(tmp_path, paths):
    """A reconstructed availability 500 MW above observed generation at every half-hour."""
    for year, path in paths.items():
        df, _ = load_year(path, year)
        avail = df[["ts_utc", "nucleaire", "gaz", "charbon", "fioul"]].copy()
        avail[["nucleaire", "gaz", "charbon", "fioul"]] += 500.0
        avail.to_csv(tmp_path / f"avail_{year}.csv", index=False)


def test_run_writes_consistent_outputs_and_the_audit(tmp_path, inputs):
    _, paths = inputs
    out = tmp_path / "results"
    report = run(parse_args(["--y2019", str(paths[2019]), "--y2022", str(paths[2022]),
                             "--capacities", str(tmp_path / "none.csv"), "--out", str(out)]))
    # Without sourced fossil capacity, only the two observed-maximum fossil cases exist.
    assert set(report["cases"]) == {"nuc_mean+fos_obsmax", "nuc_max+fos_obsmax"}
    assert "lower bound" in report["hydro_power_limits"]["lakes"][2019]["basis"]
    assert all(not t["pre_registered_configuration"] for t in report["test_b"])
    shapley = pd.read_csv(out / "shapley.csv")
    assert (shapley["phi_D"] + shapley["phi_A"]).to_numpy() == pytest.approx(
        shapley["total"].to_numpy(), abs=1e-3)
    assert len(pd.read_csv(out / "scenarios.csv")) == 2 * 2 * 4  # cases x variants x scenarios
    audit = pd.read_csv(out / "data_audit.csv")
    assert audit["status"].value_counts().to_dict() == {
        "removed_nonexistent_label": 4, "retained_dst_pass_uncertain": 4, "missing_half_hour": 4}
    saved = json.loads((out / "adequacy_results.json").read_text())
    assert saved["data"]["2019"]["loading_audit"]["rows_returned"] == 17_518
    assert saved["checks"]["2019"]["balance_residual"]["max_abs_mw"] == pytest.approx(0.0, abs=0.05)
    assert saved["checks"]["same_rows_per_month_in_both_years"] is True


def test_run_with_reconstructed_availability_and_installed_fossil(tmp_path, inputs):
    _, paths = inputs
    write_availability(tmp_path, paths)
    caps = tmp_path / "capacities.csv"
    caps.write_text("year,technology,capacity_mw,source\n" + "".join(
        f"{y},{t},{mw},synthetic test value\n"
        for y in (2019, 2022) for t, mw in (("gas", 11_000), ("coal", 2_000), ("oil", 1_100))))
    report = run(parse_args([
        "--y2019", str(paths[2019]), "--y2022", str(paths[2022]), "--capacities", str(caps),
        "--availability-2019", str(tmp_path / "avail_2019.csv"),
        "--availability-2022", str(tmp_path / "avail_2022.csv"), "--out", str(tmp_path / "r")]))
    assert len(report["cases"]) == 6  # 2 x 2 generation-based + 2 reconstructed aggregations
    pre = [t for t in report["test_b"] if t["pre_registered_configuration"]]
    assert [t["configuration"] for t in pre] == ["reconstructed+monthly_mean"]
    check = report["checks"][2019]["availability_vs_generation"]
    assert check["nucleaire"]["violating_half_hours"] == 0
    assert check["excluded_dst_pass_uncertain"] == 2  # the autumn rows are not matched
    assert set(report["half_hourly_availability"]) == {
        "A1_baseline", "A1_flexible", "A4_baseline", "A4_flexible"}


def test_dst_comparison_reports_the_exact_effect_of_the_spring_rows(tmp_path, inputs):
    frames, paths = inputs
    out = tmp_path / "cmp"
    table = run_comparison(parse_args(["--y2019", str(paths[2019]), "--y2022", str(paths[2022]),
                                       "--capacities", str(tmp_path / "none.csv"), "--out", str(out)]))
    assert (out / "dst_comparison.csv").exists()
    data = table[table["section"] == "data"].set_index(["year", "quantity"])
    for year, day in ((2019, "2019-03-31"), (2022, "2022-03-27")):
        f = frames[year]
        fillers = f[(f["date"] == day) & f["heure"].isin(["02:00", "02:30"])]
        # Independent expectation: removing the two rows removes exactly their energy.
        expected_twh = -fillers["consommation"].sum() * DT_H / 1e6
        assert data.loc[(str(year), "consumption"), "abs_diff"] == pytest.approx(expected_twh, abs=1e-8)
        expected_lake_gwh = -fillers["hydraulique_lacs"].sum() * DT_H / 1e3
        assert data.loc[(str(year), "lake_budget"), "abs_diff"] == pytest.approx(expected_lake_gwh, abs=1e-5)
    monthly = table[(table["section"] == "data_monthly") & (table["abs_diff"].abs() > 1e-9)]
    assert set(monthly["month"]) == {"3"}  # only March budgets change
    # Every case x variant x scenario is compared, with relative differences.
    scen = table[(table["section"] == "scenario") & (table["quantity"] == "unmet_energy_U")]
    assert len(scen) == 2 * 2 * 4
    assert {"abs_diff", "rel_diff"} <= set(table.columns)
    row = table[table["section"] == "data"].iloc[0]
    if row["value_before"] != 0:
        assert row["rel_diff"] == pytest.approx(row["abs_diff"] / abs(row["value_before"]))
