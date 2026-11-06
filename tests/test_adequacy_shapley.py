"""Two-player Shapley values: the owner's Oct 6 example and the axioms."""

import numpy as np
import pytest

from src.adequacy.shapley import shapley_two_players


def test_owner_oct_6_example_regression():
    # Corners from tests/test_three_generator.py::test_shapley_corners: demand 120 -> 130
    # (driver D) and G1 capacity 100 -> 70 (driver A). Owner's hand result: 750 / 1450.
    s = shapley_two_players(v00=2000.0, v10=2500.0, v01=3200.0, v11=4200.0)
    assert s.total == pytest.approx(2200.0)
    assert s.interaction == pytest.approx(500.0)
    assert s.phi_d == pytest.approx(750.0)
    assert s.phi_a == pytest.approx(1450.0)


def test_efficiency_shares_add_up_to_the_total_change():
    rng = np.random.default_rng(20)
    for v00, v10, v01, v11 in rng.uniform(-1e3, 1e3, (200, 4)):
        s = shapley_two_players(v00, v10, v01, v11)
        assert s.phi_d + s.phi_a == pytest.approx(v11 - v00)


def test_each_share_is_its_solo_effect_plus_half_the_interaction():
    rng = np.random.default_rng(21)
    for v00, v10, v01, v11 in rng.uniform(-1e3, 1e3, (200, 4)):
        s = shapley_two_players(v00, v10, v01, v11)
        assert s.phi_d == pytest.approx((v10 - v00) + s.interaction / 2)
        assert s.phi_a == pytest.approx((v01 - v00) + s.interaction / 2)


def test_dummy_player_gets_zero():
    # If changing A never changes the value, A's share and the interaction are zero.
    s = shapley_two_players(v00=10.0, v10=25.0, v01=10.0, v11=25.0)
    assert s.phi_a == pytest.approx(0.0)
    assert s.interaction == pytest.approx(0.0)
    assert s.phi_d == pytest.approx(15.0)


def test_symmetry_swapping_the_players_swaps_the_shares():
    a = shapley_two_players(v00=1.0, v10=4.0, v01=9.0, v11=20.0)
    b = shapley_two_players(v00=1.0, v10=9.0, v01=4.0, v11=20.0)
    assert a.phi_d == pytest.approx(b.phi_a)
    assert a.phi_a == pytest.approx(b.phi_d)
