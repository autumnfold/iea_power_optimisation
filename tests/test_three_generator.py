import copy

import pytest

from src.dispatch import solve_dispatch


@pytest.fixture
def base_generators():
    return {
        "G1": {"max": 100.0, "cost": 10.0},
        "G2": {"max": 50.0, "cost": 50.0},
        "G3": {"max": 50.0, "cost": 100.0}
    }

def test_base_dispatch_and_duals(base_generators):
    """Verify Primal and all KKT duals for D=120, plus Strong Duality."""
    result = solve_dispatch(base_generators, demand=120)
    
    assert result["total_cost"] == pytest.approx(2000.0)
    assert result["dispatch"]["G1"] == pytest.approx(100.0)
    assert result["dispatch"]["G2"] == pytest.approx(20.0)
    assert result["dispatch"]["G3"] == pytest.approx(0.0)
    
    assert result["lambda"] == pytest.approx(50.0)
    
    # All 6 bounds
    assert result["mu_max"]["G1"] == pytest.approx(40.0)  # G1 inframarginal rent
    assert result["mu_max"]["G2"] == pytest.approx(0.0)
    assert result["mu_max"]["G3"] == pytest.approx(0.0)
    
    assert result["mu_min"]["G1"] == pytest.approx(0.0)
    assert result["mu_min"]["G2"] == pytest.approx(0.0)
    assert result["mu_min"]["G3"] == pytest.approx(50.0) # G3 too expensive
    
    # Strong Duality Certificate: Primal Cost == Dual Cost
    dual_cost = (result["lambda"] * 120) - sum(
        result["mu_max"][g] * base_generators[g]["max"] for g in base_generators
    )
    assert result["total_cost"] == pytest.approx(dual_cost)

def test_probe_a_degeneracy(base_generators):
    """Probe A: Degeneracy at D=100. Prints the solver's chosen lambda."""
    result = solve_dispatch(base_generators, demand=100)
    # The true derivative is an interval [10, 50].
    assert result["lambda"] in [10.0, 50.0]
    print(f"\n[Probe A] HiGHS returned lambda = {result['lambda']} at D=100")

def test_probe_b_sensitivity(base_generators):
    """Probe B: Small capacity reduction stays within the basis."""
    base_generators["G1"]["max"] = 90.0
    result = solve_dispatch(base_generators, demand=120)
    assert result["total_cost"] == pytest.approx(2400.0)

def test_probe_c_regime_change(base_generators):
    """Probe C: Large capacity reduction forces a regime change."""
    base_generators["G1"]["max"] = 60.0
    result = solve_dispatch(base_generators, demand=120)
    assert result["total_cost"] == pytest.approx(4100.0)

def test_probe_c_infeasible(base_generators):
    """Ensure the status check catches infeasibility when G1 drops below 20."""
    base_generators["G1"]["max"] = 10.0
    with pytest.raises(RuntimeError, match="feasible solution was not found"):
        solve_dispatch(base_generators, demand=120)

def test_shapley_corners(base_generators):
    """Test the 4 corners of the Shapley two-driver interaction."""
    # Base: G1=100, D=120 -> 2000
    assert solve_dispatch(base_generators, 120)["total_cost"] == pytest.approx(2000.0)
    
    # Dem Rise: G1=100, D=130 -> 2500
    assert solve_dispatch(base_generators, 130)["total_cost"] == pytest.approx(2500.0)
    
    gen_cap = copy.deepcopy(base_generators)
    gen_cap["G1"]["max"] = 70.0
    
    # Cap Fall: G1=70, D=120 -> 3200
    assert solve_dispatch(gen_cap, 120)["total_cost"] == pytest.approx(3200.0)
    
    # Both: G1=70, D=130 -> 4200
    assert solve_dispatch(gen_cap, 130)["total_cost"] == pytest.approx(4200.0)