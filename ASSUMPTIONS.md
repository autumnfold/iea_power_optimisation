# Numerical assumptions

Every number the model uses that is not read directly from the data, with its source. Modelling choices without a number are in `docs/adequacy_model.md`, and project decisions are in `PROJECT_STATE.md`.

## Adequacy model (primary objective)

| Quantity | Value | Source | Used in |
|---|---|---|---|
| Time step $\Delta t$ | 0.5 h | éCO2mix definitive data are published at a 30-minute step; checked on every load (median step) and found in check 1 (`PROJECT_STATE.md`, section 4) | `src/adequacy/data.py` (`DT_H`) |
| Test B tolerance | 36 GWh (0.01% of 2019 net demand as computed in check 1, 361.8 TWh) | Pre-registered convention, `docs/check_protocol_v6.md`, section 8.3. Not a statistical threshold. | `src/adequacy/checks.py` (`TEST_B_THRESHOLD_MWH`) |
| Lake power limit $K^{L}$ (fallback) | Highest observed `hydraulique_lacs` over 2019 and 2022, computed at run time | éCO2mix data. An observed-output proxy, a lower bound on installed capacity. | `inputs.hydro_capacity` |
| Pumped-storage generation limit $K^{T}$ (fallback) | Highest observed `hydraulique_step_turbinage` over 2019 and 2022, computed at run time | éCO2mix data. An observed-output proxy, a lower bound on installed capacity. | `inputs.hydro_capacity` |
| Fossil availability, case `fos_obsmax` | Sum over gas, coal and oil of each technology's highest observed output in the year (13,658 MW in 2019, 14,130 MW in 2022 in check 1) | éCO2mix data; convention of check 1 | `inputs.observed_fossil_max` |
| Nuclear availability, cases `nuc_mean` and `nuc_max` | Monthly mean and monthly maximum of observed nuclear generation | éCO2mix data. Sensitivity assumptions, not bounds. | `inputs.generation_based_availability` |
| Installed capacities: lakes, pumped-storage generation, gas, coal, oil; 2019 and 2022 | **Not yet sourced** | Owner task: RTE annual reports ("parc installé") or ENTSO-E installed capacity by production type. Fill in `inputs/capacities.csv`, with a source for every value; the loader rejects a value without one. | `inputs.load_capacities` |

## Numerical settings (not modelling assumptions)

| Setting | Value | Reason |
|---|---|---|
| Shortfall threshold for "hours short" | $10^{-3}$ MW (1 kW) | Removes floating-point and solver noise; physically negligible |
| Bisection steps for $\theta_m$ | 100 | Halving an interval of at most about $10^{5}$ MW 100 times reaches floating-point resolution |

## Secondary objective (cost attribution, D21)

Not started. Technology efficiencies, emission factors, variable O&M, fuel and carbon prices and the exchange rate will be recorded here with their sources when the cost layer begins.
