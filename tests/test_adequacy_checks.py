"""Physical-consistency checks, Test B and the import comparison on small known inputs."""

import pandas as pd
import pytest

from src.adequacy.checks import (
    availability_vs_generation,
    balance_residual,
    hydro_capacity_check,
    import_comparison,
    run_test_b,
)


def test_balance_residual_is_zero_for_balanced_data_and_detects_a_gap(make_balanced_year):
    df = make_balanced_year(2019, days=2, seed=50)
    assert balance_residual(df)["max_abs_mw"] == pytest.approx(0.0, abs=1e-6)
    df["consommation"] += 50.0  # 50 MW of demand that no column supplies
    r = balance_residual(df)
    assert r["mean_mw"] == pytest.approx(50.0)
    assert r["annual_twh"] == pytest.approx(50.0 * 96 * 0.5 / 1e6)


def test_availability_below_generation_is_located(make_year):
    df = make_year(2019, days=1, values={"nucleaire": 40_000.0, "gaz": 5_000.0})
    avail = pd.DataFrame({"ts_utc": df["ts_utc"], "nucleaire": 41_000.0, "gaz": 5_000.0,
                          "charbon": 0.0, "fioul": 0.0})
    avail.loc[7, "nucleaire"] = 39_970.0  # 30 MW below observed generation in one half-hour
    r = availability_vs_generation(avail, df)
    assert r["matched_half_hours"] == 48
    assert r["nucleaire"]["violating_half_hours"] == 1
    assert r["nucleaire"]["violation_energy_mwh"] == pytest.approx(15.0)
    assert r["nucleaire"]["largest_violation_mw"] == pytest.approx(30.0)
    assert r["gaz"]["violating_half_hours"] == 0  # equal is consistent


def test_hydro_capacity_check():
    assert hydro_capacity_check(5_000.0, pd.Series([1.0, 4_999.0]))["ok"]
    assert not hydro_capacity_check(5_000.0, pd.Series([5_001.0]))["ok"]


def test_test_b_threshold_is_inclusive_and_flags_the_configuration():
    assert run_test_b(36_000.0, "x", True)["within_tolerance"]
    r = run_test_b(36_001.0, "nuc_max+fos_obsmax", False)
    assert not r["within_tolerance"]
    assert r["unmet_gwh"] == pytest.approx(36.001)
    assert r["pre_registered_configuration"] is False


def test_import_comparison_on_a_three_half_hour_example():
    df = pd.DataFrame({"ech_physiques": [-50.0, 200.0, 100.0]})
    shortfall = pd.Series([0.0, 100.0, 300.0])
    r = import_comparison(shortfall, df)
    assert r["annual_net_imports_gwh"] == pytest.approx(250.0 * 0.5 / 1e3)
    assert r["net_imports_over_net_importing_half_hours_gwh"] == pytest.approx(300.0 * 0.5 / 1e3)
    assert r["peak_net_import_gw"] == pytest.approx(0.2)
    assert r["modelled_unmet_gwh"] == pytest.approx(400.0 * 0.5 / 1e3)
    t = r["time_matched"]
    assert t["short_half_hours"] == 2
    assert t["share_of_short_half_hours_with_net_imports"] == pytest.approx(1.0)
    assert t["net_imports_during_short_half_hours_gwh"] == pytest.approx(300.0 * 0.5 / 1e3)
    # Only the last half-hour's shortfall (300) exceeds its observed net imports (100).
    assert t["shortfall_above_observed_net_imports_gwh"] == pytest.approx(200.0 * 0.5 / 1e3)
    assert t["net_import_at_peak_shortfall_gw"] == pytest.approx(0.1)
