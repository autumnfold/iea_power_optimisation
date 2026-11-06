"""End-to-end run of the pipeline on two small synthetic files (no real data)."""

import json

import pandas as pd
import pytest

from src.adequacy.run import parse_args, run


def write_inputs(tmp_path, make_balanced_year, write_csv, with_availability: bool):
    paths = {}
    for year, seed in ((2019, 60), (2022, 61)):
        df = make_balanced_year(year, days=2, seed=seed)
        paths[year] = tmp_path / f"eco2mix_{year}.csv"
        write_csv(paths[year], df)
        if with_availability:
            # A reconstructed availability that is above observed generation everywhere.
            avail = df[["ts_utc", "nucleaire", "gaz", "charbon", "fioul"]].copy()
            avail[["nucleaire", "gaz", "charbon", "fioul"]] += 500.0
            avail.to_csv(tmp_path / f"avail_{year}.csv", index=False)
    return paths


def test_run_writes_consistent_outputs_without_capacities(tmp_path, make_balanced_year, write_csv):
    paths = write_inputs(tmp_path, make_balanced_year, write_csv, with_availability=False)
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
    scenarios = pd.read_csv(out / "scenarios.csv")
    assert len(scenarios) == 2 * 2 * 4  # cases x pumped-storage variants x scenarios
    saved = json.loads((out / "adequacy_results.json").read_text())
    assert set(saved["frozen_fossil"]) == set(report["cases"])
    assert saved["checks"]["2019"]["balance_residual"]["max_abs_mw"] == pytest.approx(0.0, abs=1e-3)


def test_run_with_reconstructed_availability_and_installed_fossil(tmp_path, make_balanced_year, write_csv):
    paths = write_inputs(tmp_path, make_balanced_year, write_csv, with_availability=True)
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
    assert set(report["half_hourly_availability"]) == {
        "A1_baseline", "A1_flexible", "A4_baseline", "A4_flexible"}
