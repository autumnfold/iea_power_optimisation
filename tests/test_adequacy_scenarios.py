"""Scenario assembly: each driver's inputs come from the right year; months are independent."""

import numpy as np
import pandas as pd
import pytest

from src.adequacy.inputs import demand_side
from src.adequacy.scenarios import attribute, evaluate, run_four_scenarios

N_HALF_HOURS = 48  # one day, all in January
DT = 0.5


def constant_years(make_year, demand_2019, demand_2022, lakes_2019=0.0, lakes_2022=0.0):
    """Two one-day years whose baseline net demand equals the given consumption."""
    return {
        2019: demand_side(make_year(2019, 1, {"consommation": demand_2019, "hydraulique_lacs": lakes_2019})),
        2022: demand_side(make_year(2022, 1, {"consommation": demand_2022, "hydraulique_lacs": lakes_2022})),
    }


def monthly(value):
    return pd.Series({1: value})


def test_each_scenario_takes_demand_and_availability_from_its_own_years(make_year):
    demand = constant_years(make_year, 100.0, 200.0)
    availability = {2019: monthly(90.0), 2022: monthly(150.0)}
    caps = {2019: 0.0, 2022: 0.0}
    r = run_four_scenarios(demand, availability, caps, caps, "baseline")
    energy = DT * N_HALF_HOURS
    assert r["A1"].unmet_mwh == pytest.approx(10.0 * energy)   # 100 - 90
    assert r["A2"].unmet_mwh == pytest.approx(110.0 * energy)  # 2022 demand 200 - 2019 availability 90
    assert r["A3"].unmet_mwh == pytest.approx(0.0)             # 2019 demand 100 < 2022 availability 150
    assert r["A4"].unmet_mwh == pytest.approx(50.0 * energy)   # 200 - 150
    assert r["A2"].peak_mw == pytest.approx(110.0)


def test_lake_budget_and_lake_capacity_follow_the_demand_year(make_year):
    # Only 2022 had lake output, so only the scenarios with 2022 demand (A2, A4) get water.
    demand = constant_years(make_year, 100.0, 100.0, lakes_2019=0.0, lakes_2022=4.0)
    availability = {2019: monthly(90.0), 2022: monthly(90.0)}
    caps = {2019: 1e6, 2022: 1e6}
    r = run_four_scenarios(demand, availability, caps, caps, "baseline")
    assert r["A1"].peak_mw == pytest.approx(10.0)
    assert r["A3"].peak_mw == pytest.approx(10.0)
    assert r["A2"].peak_mw == pytest.approx(6.0)  # the 4 MW of 2022 lake energy, spread evenly
    assert r["A4"].peak_mw == pytest.approx(6.0)
    # Same budgets, but 2022 lake capacity 0: A2 and A4 can no longer use the water.
    r = run_four_scenarios(demand, availability, {2019: 1e6, 2022: 0.0}, caps, "baseline")
    assert r["A2"].peak_mw == pytest.approx(10.0)


def test_lake_water_cannot_move_between_months(make_year):
    # January 31 has lake output but no deficit; February 1 has a deficit and no water.
    lakes = np.r_[np.full(48, 50.0), np.zeros(48)]
    consumption = np.r_[np.full(48, 50.0), np.full(48, 100.0)]
    ds = demand_side(make_year(2019, 2, {"consommation": consumption, "hydraulique_lacs": lakes},
                               start="2019-01-31"))
    r = evaluate(ds, pd.Series(80.0, index=ds.index), 1e6, 1e6, "baseline")
    # In January N = C - 0 = 50 (lakes are not subtracted from net demand), below 80.
    assert r.unmet_mwh_by_month[1] == pytest.approx(0.0)
    assert r.unmet_mwh_by_month[2] == pytest.approx(20.0 * DT * 48)


def test_flexible_equals_baseline_without_pumped_storage(make_balanced_year):
    df = make_balanced_year(2019, days=2, seed=30)
    df["pompage"] = 0.0
    df["hydraulique_step_turbinage"] = 0.0
    ds = demand_side(df)
    k = pd.Series(55_000.0, index=ds.index)
    base = evaluate(ds, k, 5_000.0, 3_000.0, "baseline")
    flex = evaluate(ds, k, 5_000.0, 3_000.0, "flexible")
    assert flex.unmet_mwh == pytest.approx(base.unmet_mwh, rel=1e-7, abs=1e-3)
    assert flex.peak_mw == pytest.approx(base.peak_mw, rel=1e-7, abs=1e-3)


def test_flexible_is_never_worse_than_baseline_when_ps_capacity_covers_observed_output(make_balanced_year):
    # The flexible problem can reproduce the observed pumped-storage profile (it fits the
    # budget and, here, the power limit), so its optimum cannot be worse than the baseline.
    for seed in range(31, 36):
        df = make_balanced_year(2019, days=2, seed=seed)
        ds = demand_side(df)
        k = pd.Series(52_000.0, index=ds.index)
        ps_cap = float(df["hydraulique_step_turbinage"].max())
        base = evaluate(ds, k, 6_000.0, ps_cap, "baseline")
        flex = evaluate(ds, k, 6_000.0, ps_cap, "flexible")
        assert flex.unmet_mwh <= base.unmet_mwh + 1e-3
        assert flex.peak_mw <= base.peak_mw + 1e-3


def test_monthly_attribution_adds_up_to_the_annual_attribution(make_balanced_year):
    years = {2019: demand_side(make_balanced_year(2019, 2, seed=40)),
             2022: demand_side(make_balanced_year(2022, 2, seed=41))}
    for ds in years.values():  # put the two days in different months
        ds["month"] = [1] * 48 + [2] * 48
    availability = {2019: pd.Series({1: 52_000.0, 2: 50_000.0}),
                    2022: pd.Series({1: 47_000.0, 2: 49_000.0})}
    caps = {2019: 4_000.0, 2022: 4_000.0}
    shares = attribute(run_four_scenarios(years, availability, caps, caps, "baseline"))
    annual = shares["unmet_mwh"]
    by_month = shares["unmet_mwh_by_month"].values()
    assert sum(s.phi_a for s in by_month) == pytest.approx(annual.phi_a)
    assert sum(s.phi_d for s in by_month) == pytest.approx(annual.phi_d)
    assert annual.phi_a + annual.phi_d == pytest.approx(annual.total)


def test_missing_availability_month_is_an_error(make_year):
    ds = demand_side(make_year(2019, 1, {"consommation": 1.0}))
    with pytest.raises(ValueError, match="availability"):
        evaluate(ds, ds["month"].map(pd.Series({2: 0.0})), 0.0, 0.0, "baseline")
