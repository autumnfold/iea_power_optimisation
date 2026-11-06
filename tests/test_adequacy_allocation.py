"""Water-filling against hand examples, closed forms and independent LPs (HiGHS)."""

import numpy as np
import pytest

from src.adequacy.allocation import (
    covered_energy,
    min_shortfall_lp,
    shortfall_metrics,
    water_fill,
)

DT = 0.5


def random_cases(seed: int, count: int):
    """Small random months: deficits with some zeros, finite or infinite caps, budgets that
    sometimes bind and sometimes do not."""
    rng = np.random.default_rng(seed)
    for _ in range(count):
        n = int(rng.integers(1, 40))
        deficit = rng.uniform(0, 100, n) * (rng.random(n) < 0.7)
        cap = float(rng.uniform(1, 80)) if rng.random() < 0.8 else np.inf
        usable = covered_energy(deficit, cap, 0.0, DT)
        budget = float(rng.uniform(0, 1.2 * usable + 1.0))
        yield deficit, cap, budget


def closed_form_unmet(deficit, cap, budget):
    """U = dt * sum D - min(E, dt * sum min(D, cap)): the most lake energy that can be useful."""
    return DT * deficit.sum() - min(budget, DT * np.minimum(deficit, cap).sum())


def max_flow_useful_hydro(deficit, lake, ps):
    """Closed form (minimum cut) of the most hydro energy two resources can usefully place.

    v6 section 7.1: min{E_L + E_T, E_L + dt*sum min(D, K_T), E_T + dt*sum min(D, K_L),
    dt*sum min(D, K_L + K_T)}. Used only as an independent reference for the LP.
    """
    (k_l, e_l), (k_t, e_t) = lake, ps
    return min(e_l + e_t,
               e_l + DT * np.minimum(deficit, k_t).sum(),
               e_t + DT * np.minimum(deficit, k_l).sum(),
               DT * np.minimum(deficit, k_l + k_t).sum())


def test_hand_example_budget_binds():
    # F(theta) = 0.5 * sum max(0, D - theta) = 6 MWh gives theta = 2: (10-2) + (6-2) = 12.
    deficit = np.array([10.0, 6.0, 2.0])
    lake, theta = water_fill(deficit, np.inf, 6.0, DT)
    assert theta == pytest.approx(2.0)
    assert lake == pytest.approx([8.0, 4.0, 0.0])
    m = shortfall_metrics(deficit - lake, DT)
    assert m["unmet_mwh"] == pytest.approx(3.0)
    assert m["peak_mw"] == pytest.approx(2.0)


def test_hand_example_capacity_binds():
    # With cap 5, F(0) = 0.5 * (5 + 5 + 2) = 6 = budget: the budget does not bind, theta = 0.
    deficit = np.array([10.0, 6.0, 2.0])
    lake, theta = water_fill(deficit, 5.0, 6.0, DT)
    assert theta == pytest.approx(0.0)
    assert lake == pytest.approx([5.0, 5.0, 2.0])
    assert shortfall_metrics(deficit - lake, DT)["peak_mw"] == pytest.approx(5.0)


def test_water_fill_respects_every_constraint():
    for deficit, cap, budget in random_cases(seed=10, count=300):
        lake, theta = water_fill(deficit, cap, budget, DT)
        assert theta >= 0
        assert np.all(lake >= 0)
        assert np.all(lake <= cap)
        assert np.all(lake <= deficit + 1e-12)
        assert DT * lake.sum() <= budget + 1e-9


def test_theta_solves_the_budget_equation_when_the_budget_binds():
    for deficit, cap, budget in random_cases(seed=11, count=300):
        _lake, theta = water_fill(deficit, cap, budget, DT)
        if covered_energy(deficit, cap, 0.0, DT) > budget:
            assert covered_energy(deficit, cap, theta, DT) == pytest.approx(budget, abs=1e-9)
        else:
            assert theta == 0.0


def test_unmet_energy_matches_closed_form():
    for deficit, cap, budget in random_cases(seed=12, count=300):
        lake, _ = water_fill(deficit, cap, budget, DT)
        assert DT * (deficit - lake).sum() == pytest.approx(
            closed_form_unmet(deficit, cap, budget), abs=1e-8)


def test_water_fill_minimises_unmet_energy_like_an_independent_lp():
    for deficit, cap, budget in random_cases(seed=13, count=150):
        lake, _ = water_fill(deficit, cap, budget, DT)
        s_lp = min_shortfall_lp(deficit, [(cap, budget)], "energy", DT)
        assert DT * (deficit - lake).sum() == pytest.approx(DT * s_lp.sum(), rel=1e-7, abs=1e-6)


def test_water_fill_minimises_peak_shortfall_like_an_independent_lp():
    # The same allocation is optimal for the peak too: the claim that justifies using one
    # rule for both metrics in the baseline.
    for deficit, cap, budget in random_cases(seed=14, count=150):
        lake, _ = water_fill(deficit, cap, budget, DT)
        s_lp = min_shortfall_lp(deficit, [(cap, budget)], "peak", DT)
        assert (deficit - lake).max() == pytest.approx(s_lp.max(), rel=1e-7, abs=1e-6)


def test_edge_cases():
    deficit = np.array([5.0, 3.0, 0.0])
    lake, _ = water_fill(deficit, 10.0, 0.0, DT)  # no water
    assert lake == pytest.approx([0.0, 0.0, 0.0])
    lake, _ = water_fill(deficit, 2.0, np.inf, DT)  # unlimited water, power-limited
    assert lake == pytest.approx([2.0, 2.0, 0.0])
    lake, _ = water_fill(deficit, 0.0, 100.0, DT)  # no lake capacity
    assert lake == pytest.approx([0.0, 0.0, 0.0])
    lake, theta = water_fill(np.zeros(4), 10.0, 100.0, DT)  # no deficit
    assert lake == pytest.approx(np.zeros(4))
    assert theta == 0.0
    lake, _ = water_fill(np.array([]), 10.0, 1.0, DT)  # empty month
    assert lake.size == 0


def test_two_resource_lp_matches_max_flow_closed_form():
    rng = np.random.default_rng(15)
    for _ in range(150):
        n = int(rng.integers(1, 30))
        deficit = rng.uniform(0, 100, n) * (rng.random(n) < 0.7)
        lake = (float(rng.uniform(0, 60)), float(rng.uniform(0, 600)))
        ps = (float(rng.uniform(0, 40)), float(rng.uniform(0, 300)))
        s = min_shortfall_lp(deficit, [lake, ps], "energy", DT)
        expected = DT * deficit.sum() - max_flow_useful_hydro(deficit, lake, ps)
        assert DT * s.sum() == pytest.approx(expected, rel=1e-7, abs=1e-6)


def test_two_resource_lp_reduces_to_water_filling_without_pumped_storage():
    for deficit, cap, budget in random_cases(seed=16, count=60):
        lake, _ = water_fill(deficit, cap, budget, DT)
        for no_ps in [(0.0, 500.0), (50.0, 0.0)]:  # no power, or no energy
            s_energy = min_shortfall_lp(deficit, [(cap, budget), no_ps], "energy", DT)
            s_peak = min_shortfall_lp(deficit, [(cap, budget), no_ps], "peak", DT)
            assert DT * s_energy.sum() == pytest.approx(DT * (deficit - lake).sum(), abs=1e-6)
            assert s_peak.max() == pytest.approx((deficit - lake).max(), abs=1e-6)


def test_lp_rejects_unknown_objective():
    with pytest.raises(ValueError):
        min_shortfall_lp(np.array([1.0]), [(1.0, 1.0)], "cost", DT)


def test_shortfall_metrics_counts_only_real_shortfalls():
    m = shortfall_metrics(np.array([0.0, 1e-9, 2.0, 4.0]), DT)
    assert m["unmet_mwh"] == pytest.approx(3.0)
    assert m["peak_mw"] == pytest.approx(4.0)
    assert m["hours_short"] == pytest.approx(1.0)  # two half-hours; 1e-9 MW is noise
