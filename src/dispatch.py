import pyomo.environ as pyo

def solve_dispatch(demand):
    model = pyo.ConcreteModel()
    
    # Suffix to import dual values (shadow prices) from the solver
    model.dual = pyo.Suffix(direction=pyo.Suffix.IMPORT)
    
    # Static definition of the generators for this iteration
    generators = {
        "G1": {"max": 100.0, "cost": 10.0},
        "G2": {"max": 50.0, "cost": 50.0},
        "G3": {"max": 50.0, "cost": 100.0}
    }
    
    model.G = pyo.Set(initialize=generators.keys())
    model.dispatch = pyo.Var(model.G)
    
    # Objective function: Minimize total cost
    model.cost = pyo.Objective(
        expr=sum(generators[g]["cost"] * model.dispatch[g] for g in model.G), 
        sense=pyo.minimize
    )
    
    # Constraint 1: Demand balance
    model.balance = pyo.Constraint(expr=sum(model.dispatch[g] for g in model.G) == demand)
    
    # Constraint 2: Maximum capacity
    def max_cap_rule(model, g):
        return model.dispatch[g] <= generators[g]["max"]
    model.max_cap = pyo.Constraint(model.G, rule=max_cap_rule)
    
    # Constraint 3: Minimum capacity (Non-negativity)
    def min_cap_rule(model, g):
        return -model.dispatch[g] <= 0
    model.min_cap = pyo.Constraint(model.G, rule=min_cap_rule)
    
    # Solve using the HiGHS solver
    pyo.SolverFactory('appsi_highs').solve(model)
    
    # Safe extraction: abs() bypasses sign convention differences between various LP solvers
    return {
        "total_cost": pyo.value(model.cost),
        "dispatch": {g: pyo.value(model.dispatch[g]) for g in model.G},
        "lambda": abs(pyo.value(model.dual[model.balance])),
        "mu_max": {g: abs(pyo.value(model.dual[model.max_cap[g]])) for g in model.G},
        "mu_min": {g: abs(pyo.value(model.dual[model.min_cap[g]])) for g in model.G}
    }