import pyomo.environ as pyo

def solve_dispatch(generators, demand):
    """
    Solves the economic dispatch problem.
    
    Dual Extraction Convention:
    - Balance (sum(g) == D): returned as lambda (∂C/∂D).
    - Capacity limits: We map the raw duals (∂C/∂b) to KKT multipliers via μ = -∂C/∂b.
    """
    model = pyo.ConcreteModel()
    model.dual = pyo.Suffix(direction=pyo.Suffix.IMPORT)
    
    model.G = pyo.Set(initialize=generators.keys())
    model.dispatch = pyo.Var(model.G)
    
    model.cost = pyo.Objective(
        expr=sum(generators[g]["cost"] * model.dispatch[g] for g in model.G), 
        sense=pyo.minimize
    )
    
    model.balance = pyo.Constraint(expr=sum(model.dispatch[g] for g in model.G) == demand)
    
    def max_cap_rule(model, g):
        return model.dispatch[g] <= generators[g]["max"]
    model.max_cap = pyo.Constraint(model.G, rule=max_cap_rule)
    
    def min_cap_rule(model, g):
        return -model.dispatch[g] <= 0
    model.min_cap = pyo.Constraint(model.G, rule=min_cap_rule)
    
    results = pyo.SolverFactory('appsi_highs').solve(model, load_solutions=False)
    
    if results.solver.termination_condition != pyo.TerminationCondition.optimal:
        raise RuntimeError(f"Solver failed to find optimal solution. Status: {results.solver.termination_condition}")
    
    model.solutions.load_from(results)
    
    return {
        "total_cost": pyo.value(model.cost),
        "dispatch": {g: pyo.value(model.dispatch[g]) for g in model.G},
        "lambda": pyo.value(model.dual[model.balance]),
        "mu_max": {g: -pyo.value(model.dual[model.max_cap[g]]) for g in model.G},
        "mu_min": {g: -pyo.value(model.dual[model.min_cap[g]]) for g in model.G}
    }
