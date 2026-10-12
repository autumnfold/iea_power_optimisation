import copy

import pyomo.environ as pyo
import pytest

from src.dispatch import solve_dispatch


@pytest.fixture
def base_generators():
    return {
        "G1": {"max": 100.0, "cost": 10.0},
        "G2": {"max": 50.0, "cost": 50.0},
        "G3": {"max": 50.0, "cost": 100.0}
    }

def test_raw_pyomo_duals(base_generators):
    """Verify raw dual signs from Pyomo match ∂C/∂b convention before inversion."""
    model = pyo.ConcreteModel()
    model.dual = pyo.Suffix(direction=pyo.Suffix.IMPORT)
    model.G = pyo.Set(initialize=base_generators.keys())
    model.dispatch = pyo.Var(model.G)
    model.cost = pyo.Objective(expr=sum(base_generators[g]["cost"] * model.dispatch[g] for g in model.G), sense=pyo.minimize)
    model.balance = pyo.Constraint(expr=sum(model.dispatch[g] for g in model.G) == 120)
    model.max_cap = pyo.Constraint(model.G, rule=lambda m, g: m.dispatch[g] <= base_generators[g]["max"])
    model.min_cap = pyo.Constraint(model.G, rule=lambda m, g: -m.dispatch[g] <= 0)
    pyo.SolverFactory('appsi_highs').solve(model)
    
    # Relaxing G1's max bound decreases cost -> negative dual
    assert pyo.value(model.dual[model.max_cap["G1"]]) == pytest.approx(-40.0)
    # Increasing demand increases cost -> positive dual
    assert pyo.value(model.dual[model.balance]) == pytest.approx(50.0)
    # Relaxing G3's zero-bound decreases cost -> negative dual
    assert pyo.value(model.dual[model.min_cap["G3"]]) == pytest.approx(-50.0)

def test_base_dispatch_and_duals(base_generators):
    """Verify Primal and all KKT duals for D=120, plus Strong Duality."""
    result = solve_dispatch(base_generators, demand=120)
    
    assert result["total_cost"] == pytest.approx(2000.0)
    assert result["dispatch"]["G1"] == pytest.approx(100.0)
    assert result["dispatch"]["G2"] == pytest.approx(20.0)
    assert result["dispatch"]["G3"] == pytest.approx(0.0)
    
    assert result["lambda"] == pytest.approx(50.0)
    
    assert result["mu_max"]["G1"] == pytest.approx(40.0)
    assert result["mu_max"]["G2"] == pytest.approx(0.0)
    assert result["mu_max"]["G3"] == pytest.approx(0.0)
    
    assert result["mu_min"]["G1"] == pytest.approx(0.0)
    assert result["mu_min"]["G2"] == pytest.approx(0.0)
    assert result["mu_min"]["G3"] == pytest.approx(50.0)
    
    dual_cost = (result["lambda"] * 120) - sum(
        result["mu_max"][g] * base_generators[g]["max"] for g in base_generators
    )
    assert result["total_cost"] == pytest.approx(dual_cost)

def test_probe_a_degeneracy(base_generators):
    """Probe A: Degeneracy at D=100."""
    result = solve_dispatch(base_generators, demand=100)
    
    # Mathematical bounds of the subdifferential
    assert 10.0 - 1e-6 <= result["lambda"] <= 50.0 + 1e-6
    
    # Solver artifact track: HiGHS currently returns the left endpoint.
    assert result["lambda"] == pytest.approx(10.0)

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
    with pytest.raises(RuntimeError, match="optimal"):
        solve_dispatch(base_generators, demand=120)

def test_shapley_corners(base_generators):
    """Test the 4 corners of the Shapley two-driver interaction."""
    assert solve_dispatch(base_generators, 120)["total_cost"] == pytest.approx(2000.0)
    assert solve_dispatch(base_generators, 130)["total_cost"] == pytest.approx(2500.0)
    
    gen_cap = copy.deepcopy(base_generators)
    gen_cap["G1"]["max"] = 70.0
    
    assert solve_dispatch(gen_cap, 120)["total_cost"] == pytest.approx(3200.0)
    assert solve_dispatch(gen_cap, 130)["total_cost"] == pytest.approx(4200.0)
