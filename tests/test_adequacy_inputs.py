"""Driver inputs: net demand signs, budgets, availability cases and aggregation, capacities."""

import numpy as np
import pandas as pd
import pytest

from src.adequacy.inputs import (
    aggregate_availability,
    align_availability,
    demand_side,
    generation_based_availability,
    hydro_capacity,
    installed_fossil,
    load_capacities,
    monthly_budgets,
    observed_fossil_max,
)


def test_baseline_net_demand_equals_what_conventional_lakes_and_imports_supplied(make_balanced_year):
    # From the balance C = sum of generation + pompage + ech, the baseline net demand
    # must equal nuclear + fossil + lakes + net imports. This checks every sign at once.
    df = make_balanced_year(2019, days=3, seed=2)
    ds = demand_side(df)
    supplied = df["nucleaire"] + df["gaz"] + df["charbon"] + df["fioul"] + df["hydraulique_lacs"] \
        + df["ech_physiques"]
    assert ds["net_demand_baseline"].to_numpy() == pytest.approx(supplied.to_numpy())


def test_flexible_net_demand_removes_observed_ps_generation_exactly_once(make_balanced_year):
    df = make_balanced_year(2019, days=3, seed=3)
    ds = demand_side(df)
    assert (ds["pumping"] >= 0).all()
    assert ds["pumping"].to_numpy() == pytest.approx(-df["pompage"].to_numpy())
    # N_flex = N_base + g_obs: historical generation is replaced, not added on top.
    assert (ds["net_demand_flexible"] - ds["net_demand_baseline"]).to_numpy() == pytest.approx(
        df["hydraulique_step_turbinage"].to_numpy())


def test_monthly_budgets_convert_mw_to_mwh(make_year):
    # Two January days at 100 MW of lake output: 96 half-hours * 100 MW * 0.5 h = 4800 MWh.
    df = make_year(2019, days=2, values={"hydraulique_lacs": 100.0, "hydraulique_step_turbinage": 10.0})
    budgets = monthly_budgets(demand_side(df))
    assert budgets.at[1, "lake_budget_mwh"] == pytest.approx(4800.0)
    assert budgets.at[1, "ps_budget_mwh"] == pytest.approx(480.0)


def test_generation_based_cases_use_monthly_statistics(make_year):
    nuclear = np.r_[np.full(48, 40_000.0), np.full(48, 50_000.0)]
    df = make_year(2019, days=2, start="2019-01-31", values={"nucleaire": nuclear})
    # Day 1 is in January, day 2 in February.
    mean = generation_based_availability(df, "mean", fossil_mw=1_000.0)
    assert mean.to_dict() == pytest.approx({1: 41_000.0, 2: 51_000.0})
    nuclear_feb = np.r_[np.full(48, 40_000.0), np.linspace(45_000, 55_000, 48)]
    df = make_year(2019, days=2, start="2019-01-31", values={"nucleaire": nuclear_feb})
    assert generation_based_availability(df, "max", 0.0)[2] == pytest.approx(55_000.0)
    with pytest.raises(ValueError):
        generation_based_availability(df, "median", 0.0)


def test_observed_fossil_max_sums_each_technology_maximum(make_year):
    gas = np.zeros(48)
    gas[0] = 9_000.0
    coal = np.zeros(48)
    coal[1] = 1_500.0  # at a different half-hour from the gas maximum
    df = make_year(2019, days=1, values={"gaz": gas, "charbon": coal, "fioul": 300.0})
    assert observed_fossil_max(df) == pytest.approx(10_800.0)  # not 9,300, the simultaneous max


def test_monthly_mean_aggregation():
    df = pd.DataFrame({"month": [1, 1, 2, 2], "day": ["a", "b", "c", "c"]})
    total = pd.Series([10.0, 20.0, 30.0, 50.0])
    assert aggregate_availability(total, df, "monthly_mean").to_dict() == pytest.approx({1: 15.0, 2: 40.0})


def test_lowest_daily_mean_sums_technologies_before_aggregating():
    # Day 1: nuclear 100, fossil 20 (total 120). Day 2: nuclear 110, fossil 5 (total 115).
    # The lowest daily mean of the TOTAL is 115; summing per-technology minima would give
    # 100 + 5 = 105, a combination of days that never occurred together.
    df = pd.DataFrame({"month": [1] * 96, "day": ["d1"] * 48 + ["d2"] * 48})
    total = pd.Series([120.0] * 48 + [115.0] * 48)
    assert aggregate_availability(total, df, "lowest_daily_mean")[1] == pytest.approx(115.0)


def test_lowest_daily_mean_uses_each_days_own_number_of_half_hours():
    # A clock-change day with 46 half-hours: half at 50 MW, half at 150 MW, mean 100.
    # Dividing by 48 instead would give 95.8 and make it the "lowest" day by mistake.
    df = pd.DataFrame({"month": [3] * 94, "day": ["normal"] * 48 + ["dst"] * 46})
    total = pd.Series([100.0] * 48 + [50.0] * 23 + [150.0] * 23)
    assert aggregate_availability(total, df, "lowest_daily_mean")[3] == pytest.approx(100.0)
    with pytest.raises(ValueError):
        aggregate_availability(total, df, "minimum")


def test_load_capacities_skips_unsourced_rows_and_requires_sources(tmp_path):
    path = tmp_path / "capacities.csv"
    path.write_text(
        "year,technology,capacity_mw,source\n"
        "2019,lakes,9000,Example source p. 1\n"
        "2022,lakes,,\n")
    assert load_capacities(path) == {(2019, "lakes"): pytest.approx(9000.0)}
    path.write_text("year,technology,capacity_mw,source\n2019,gas,12000,\n")
    with pytest.raises(ValueError, match="no source"):
        load_capacities(path)
    path.write_text("year,technology,capacity_mw,source\n2019,hydrogen,1,x\n")
    with pytest.raises(ValueError, match="unknown technology"):
        load_capacities(path)


def test_hydro_capacity_proxy_is_labelled_lower_bound(make_year):
    years = {2019: make_year(2019, 1, {"hydraulique_lacs": 5_000.0}),
             2022: make_year(2022, 1, {"hydraulique_lacs": 6_000.0})}
    proxy = hydro_capacity({}, years, "lakes", "hydraulique_lacs")
    assert proxy[2019]["mw"] == pytest.approx(6_000.0)  # highest over BOTH years
    assert proxy[2022]["mw"] == pytest.approx(6_000.0)
    assert "lower bound" in proxy[2019]["basis"]
    # Only one year sourced: still the proxy, so both years use the same basis.
    assert hydro_capacity({(2019, "lakes"): 9_000.0}, years, "lakes", "hydraulique_lacs")[2019]["mw"] \
        == pytest.approx(6_000.0)
    sourced = hydro_capacity({(2019, "lakes"): 9_000.0, (2022, "lakes"): 9_100.0},
                             years, "lakes", "hydraulique_lacs")
    assert sourced[2022]["mw"] == pytest.approx(9_100.0)
    assert sourced[2022]["basis"] == "installed capacity (sourced)"


def test_installed_fossil_needs_all_three_technologies():
    caps = {(2019, "gas"): 12_000.0, (2019, "coal"): 3_000.0}
    assert installed_fossil(caps, 2019) is None
    caps[(2019, "oil")] = 3_500.0
    assert installed_fossil(caps, 2019) == pytest.approx(18_500.0)


def test_align_availability_matches_on_utc_interval(make_year):
    df = make_year(2019, days=1)
    df = pd.concat([df, df.iloc[[5]]], ignore_index=True)  # a duplicated eCO2mix label
    avail = pd.DataFrame({"ts_utc": df["ts_utc"].iloc[:48], "nucleaire": np.arange(48.0),
                          "gaz": 1.0, "charbon": 0.0, "fioul": 0.0})
    aligned = align_availability(avail, df)
    assert aligned["nucleaire"].iloc[48] == pytest.approx(5.0)  # same instant, same value
    with pytest.raises(ValueError, match="missing"):
        align_availability(avail.iloc[:40], df)
