import pytest
from src.dispatch import solve_dispatch

def test_three_generator_kkt():
    """Verify Pyomo/HiGHS outputs match hand-derived KKT values for D=120."""
    
    # Run the model
    result = solve_dispatch(demand=120)
    
    # 1. Primal Checks (Physical Dispatch)
    assert result["total_cost"] == 2000.0
    assert result["dispatch"]["G1"] == 100.0
    assert result["dispatch"]["G2"] == 20.0
    assert result["dispatch"]["G3"] == 0.0
    
    # 2. Dual Checks (Shadow Prices / Multipliers)
    assert result["lambda"] == 50.0          # System marginal price
    assert result["mu_max"]["G1"] == 40.0    # G1 scarcity rent
    assert result["mu_max"]["G2"] == 0.0     # G2 is marginal (slack)
    assert result["mu_min"]["G3"] == 50.0    # G3 is too expensive