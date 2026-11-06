# Adequacy model: specification and function map

Implementation plan approved by the owner on 2026-11-06, with eight clarifications (D24 in `PROJECT_STATE.md`). The check protocol behind it is `docs/check_protocol_v6.md` (frozen, D20). This file states **what the code computes**. It contains no proofs. Where a property is claimed (for example that water-filling is optimal), the claim is checked numerically by the tests listed in section 10. A proof for the report is the owner's to write (D5).

## 1. Scope: what this model is and is not

This is a **simplified, deterministic, domestic adequacy assessment**. For each month it asks whether French domestic supply could have met French demand, half-hour by half-hour, if France had been a closed system (D20).

It does **not** model:
- unit commitment, minimum stable generation or ramping;
- operating reserves or margins;
- internal transmission constraints;
- interconnector availability (exchanges are excluded from every scenario);
- the probability of outages. The model is deterministic and gives no loss-of-load expectation, so any comparison with France's 3-hours-per-year standard is an analogy only.

The Shapley shares decompose the change in **modelled** unmet energy and peak shortfall between modelled 2019 (A1) and modelled 2022 (A4). They are not estimates of real-world causes (v6, section 1).

## 2. Data and notation

Source: éCO2mix national definitive data, ODRÉ CSV export, one file per year (`src/adequacy/data.py`). Each kept row is one observed half-hour, $\Delta t = 0.5$ h. Power is in MW and energy in MWh, and outputs are in GW and GWh. Months and days are Paris local calendar months and days. Duplicate timestamps are **kept** and reported, because each row is a half-hour of observed energy and the model does not depend on the order of half-hours within a month.

| Symbol | Column | Driver |
|---|---|---|
| $C_t$ | `consommation` | D |
| $W_t$, $S_t$ | `eolien`, `solaire` | D |
| $R_t$ | `hydraulique_fil_eau_eclusee` (run-of-river and pondage) | D |
| $B_t$ | `bioenergies` | D |
| $\ell^{\text{obs}}_t$ | `hydraulique_lacs` (lakes) | D, through the monthly budget |
| $g^{\text{obs}}_t$ | `hydraulique_step_turbinage` (pumped-storage generation) | D |
| $p_t = -$`pompage` $\ge 0$ | pumping (`pompage` $\le 0$ is checked on load) | D |
| $G^{\text{nuc}}_t$, $G^{\text{gas}}_t$, $G^{\text{coal}}_t$, $G^{\text{oil}}_t$ | `nucleaire`, `gaz`, `charbon`, `fioul` | A, only through the availability cases |
| $X_t$ | `ech_physiques`: net physical imports, import-positive | none: comparison only |

The loader stops, rather than repairing, if a required column is missing, a value is missing, the time step is not 30 minutes, or `pompage` > 0.

## 3. Driver D: net demand and hydro

**Net demand** (`inputs.demand_side`):

$$N^{\text{base}}_t = C_t - W_t - S_t - R_t - B_t - (g^{\text{obs}}_t - p_t), \qquad N^{\text{flex}}_t = C_t - W_t - S_t - R_t - B_t + p_t.$$

- **Baseline (D19):** the observed net pumped-storage profile is part of net demand.
- **Flexible:** historical pumped-storage generation $g^{\text{obs}}_t$ is **not** subtracted. It is replaced by a decision variable (section 5). Observed pumping stays as load at its observed times. Hence $N^{\text{flex}}_t = N^{\text{base}}_t + g^{\text{obs}}_t$, and nothing is counted twice.

**Monthly budgets** (`inputs.monthly_budgets`): $E^{L}_m = \Delta t \sum_{t \in m} \ell^{\text{obs}}_t$ (lakes) and $E^{T}_m = \Delta t \sum_{t \in m} g^{\text{obs}}_t$ (pumped-storage generation). Water cannot move between months.

**Hydro power limits** $K^{L}$ (lakes) and $K^{T}$ (pumped-storage generation) (`inputs.hydro_capacity`):
- installed capacity, when it is sourced for both years in `inputs/capacities.csv`, taken from the driver-D year (v6, section 2);
- otherwise the highest observed output over both years, the same value in each year. This is an **observed-output proxy: a lower bound on the installed capacity, not the installed capacity.** Every output carries this label.

## 4. Driver A: conventional availability (nuclear and fossil, grouped, D16)

Driver A gives a constant $K_m$ (MW) for each month. Its contribution must not be read as the effect of nuclear availability alone.

### 4.1 Reconstructed availability (ENTSO-E, when available)

The input is a half-hourly series per technology (`inputs.load_availability`). It is matched to éCO2mix rows on the same UTC half-hour (`inputs.align_availability`). Technologies are summed **first**: $a_t = a^{\text{nuc}}_t + a^{\text{gas}}_t + a^{\text{coal}}_t + a^{\text{oil}}_t$. Then (`inputs.aggregate_availability`):

- **Baseline, monthly mean:** $K_m = \dfrac{1}{|m|} \sum_{t \in m} a_t$.
- **Sensitivity, lowest daily mean:** $K^{\text{low}}_m = \min_{d \in m} \dfrac{1}{|d|} \sum_{t \in d} a_t$.
  - $d$ runs over the local calendar days of month $m$.
  - $|d|$ is the number of half-hours present on day $d$ (46 or 50 on clock-change days).
  - Summing per-technology minima instead would give a value at or below this one, combining days that may never have coincided (v6, section 4.1).
- **Sensitivity, half-hourly:** $K_t = a_t$. This applies to **A1 and A4 only**, because a 2022 half-hour cannot be paired with a 2019 one. Comparing it with the monthly-mean result measures the effect of monthly aggregation.

The ENTSO-E reconstruction itself (v6, section 6) is not built yet. Its cleaning steps depend on the fields of the actual download. The code above is its interface.

### 4.2 Generation-based sensitivity cases (fallback)

These are **alternative assumptions, not bounds** on available capacity (`inputs.generation_based_availability`):

| | Fossil = $\sum_k \max_t G^{k}_t$ over the year (`fos_obsmax`) | Fossil = installed capacity, when sourced (`fos_installed`) |
|---|---|---|
| Nuclear = monthly mean of $G^{\text{nuc}}_t$ (`nuc_mean`) | case 1 | case 3 |
| Nuclear = monthly maximum of $G^{\text{nuc}}_t$ (`nuc_max`) | case 2 | case 4 |

Why these are not bounds:
- generation can sit below availability (modulation, export-driven operation, especially in 2019);
- a monthly maximum is reached in one half-hour only;
- the fossil value $\sum_k \max_t G^{k}_t$ sums maxima that may occur at different times.

Installed capacity is a physical ceiling for fossil, but the case as a whole is not an upper bound, because its nuclear part is not. The spread of results across cases is a **sensitivity range**, not a confidence interval.

The aggregation variants of section 4.1 do **not** apply to these cases. The lowest daily mean of observed nuclear *generation* would mostly reflect weekend and holiday modulation, not availability.

### 4.3 Frozen-fossil diagnostic (v6, section 2)

For each generation-based case, the four scenarios are rerun with fossil availability held at its 2019 value, then at its 2022 value, under baseline pumped storage. The report shows how much $\varphi_A$ moves. This is a diagnostic, not an attribution.

## 5. Allocation of flexible hydro, month by month

**Deficit before flexible hydro:** $D_t = \max(0,\ N_t - K)$, with $K = K_m$ (or $K_t$ in the half-hourly variant).

### 5.1 Baseline: water-filling of lake energy (`allocation.water_fill`)

Define, for month $m$,

$$F_m(\theta) = \Delta t \sum_{t \in m} \min\big(K^{L},\ \max(0,\ D_t - \theta)\big).$$

$F_m$ is continuous and non-increasing in $\theta$, with $F_m(\max_t D_t) = 0$.

- If $F_m(0) \le E^{L}_m$, the budget does not bind and $\theta_m = 0$.
- Otherwise $\theta_m = \min\{\theta \ge 0 : F_m(\theta) \le E^{L}_m\}$. By continuity $F_m(\theta_m) = E^{L}_m$: the whole budget is used. It is computed by bisection on $[0, \max_t D_t]$, with the invariant $F_m(\text{lo}) > E^{L}_m \ge F_m(\text{hi})$, for 100 halvings. Returning "hi" guarantees that the budget is respected.

Then:
- lake output $\ell_t = \min\big(K^{L}, \max(0, D_t - \theta_m)\big)$;
- shortfall $s_t = D_t - \ell_t$;
- monthly unmet energy $U_m = \Delta t \sum_{t \in m} s_t$;
- monthly peak $P_m = \max_{t \in m} s_t$.

**Claim checked by the tests:** this single allocation attains both the minimum unmet energy and the minimum peak shortfall of the month, as computed by two independent LPs (section 5.2).

### 5.2 Flexible pumped storage, and the reference LP (`allocation.min_shortfall_lp`)

Resources $r$ with power limit $K_r$ and energy budget $E_r$: lakes $(K^{L}, E^{L}_m)$ and pumped-storage generation $(K^{T}, E^{T}_m)$. The deficit uses $N^{\text{flex}}$.

$$\sum_r x_{r,t} + s_t = D_t, \qquad 0 \le x_{r,t} \le K_r, \qquad s_t \ge 0, \qquad \Delta t \sum_{t \in m} x_{r,t} \le E_r.$$

- **Energy objective:** $\min \Delta t \sum_t s_t$.
- **Peak objective:** $\min z$ subject to $s_t \le z$.

The equality with $s_t \ge 0$ also forbids supplying more than the deficit. With two resources, $U$ and $P$ come from **separate** LPs, and a single dispatch need not achieve both. The solver is HiGHS, through `scipy.optimize.linprog`.

**Optimistic assumptions of the flexible variant:**
1. pumped-storage generation does not depend on when the water was pumped;
2. there is no reservoir size and no state of charge within the month;
3. perfect foresight within the month;
4. the monthly generation budget equals observed generation.

**One pessimistic element:** pumping stays at its observed times, even in half-hours where the counterfactual is short.

**Property checked by the tests:** when $K^{T}$ is at least the observed maximum generation, the flexible variant can reproduce the baseline, so its $U$ and $P$ are never larger.

### 5.3 Metrics (`allocation.shortfall_metrics`)

Annual $U = \sum_m U_m$ and annual $P = \max_m P_m$ (D17). **Hours short** counts the half-hours with $s_t > 10^{-3}$ MW, times $\Delta t$.

Hours short is **not an optimised metric**. Under water-filling, every deficit half-hour of a month whose budget binds keeps some shortfall, while other allocations with the same $U$ can have fewer short hours. It is reported for description only.

## 6. Scenarios and attribution (`scenarios`, `shapley`)

| Scenario | Driver D year | Driver A year |
|---|---|---|
| A1 | 2019 | 2019 (modelled 2019) |
| A2 | 2022 | 2019 |
| A3 | 2019 | 2022 |
| A4 | 2022 | 2022 (modelled 2022) |

All driver-D inputs ($N_t$, $E^{L}_m$, $E^{T}_m$, hydro power limits) come from the driver-D year, and $K_m$ from the driver-A year. Because $K_m$ is constant within the month, only the distribution of $N_t$ within each month matters, so cross-year scenarios are well defined.

For each metric $v \in \{U, P\}$, with $v_{ij}$ the value at (D year $i$, A year $j$):

$$\varphi_D = \tfrac12\big[(v_{22,19} - v_{19,19}) + (v_{22,22} - v_{19,22})\big], \qquad \varphi_A = \tfrac12\big[(v_{19,22} - v_{19,19}) + (v_{22,22} - v_{22,19})\big],$$

$$I = v_{22,22} - v_{22,19} - v_{19,22} + v_{19,19}, \qquad \varphi_D + \varphi_A = v_{22,22} - v_{19,19}.$$

The interaction $I$ is reported explicitly, and each share equals its solo effect plus $I/2$.

- $U$ is a sum over months, so its attribution is also given by month, and the monthly shares add up to the annual ones.
- $P$ is a maximum over the year and has no monthly decomposition.

## 7. Checks (`checks`)

Physical consistency (D20):
1. **Balance closure** per year: $C_t - \sum_k G^{k}_t - \text{pompage}_t - X_t$ (mean, mean absolute, maximum absolute, annual TWh).
2. **Completeness:** rows per month, duplicate timestamps, and whether both years have the same number of rows in each month.
3. **Availability at least observed generation**, on the **raw half-hourly** reconstructed series, matched on the same UTC interval, before any aggregation, for nuclear and each fossil technology. It reports violating half-hours, violation energy and the largest violation. This checks the reconstruction, not the monthly model. It is not run on the generation-based cases, where it would be true or false by construction.
4. **Hydro power limits at least observed output**, for $K^{L}$ and $K^{T}$. For the observed-output proxy this holds by construction.
5. **Aggregation effect** (reconstructed availability only): A1 and A4 with half-hourly $K_t$, compared with the monthly mean.

**Test B** (v6, section 8.3): A1, flexible pumped storage, $U \le 36$ GWh, a pre-registered convention. The pre-registered configuration uses reconstructed availability with monthly-mean aggregation. Results for every other case are reported with `pre_registered_configuration: false`, as sensitivities. **Open:** which case serves as Test B if only the fallback cases exist. The owner decides before the real-data run.

## 8. Comparison with observed net imports (`checks.import_comparison`)

For A1 against 2019 and A4 against 2022, baseline pumped storage. $X_t$ is already net: imports minus exports, half-hourly.
- $U$ against annual net imports $\Delta t \sum_t X_t$, and against $\Delta t \sum_t \max(0, X_t)$, which is **net imports summed over net-importing half-hours. It is not gross imports.** Gross imports would need flows by border and are not reported.
- $P$ against peak net imports $\max_t X_t$.
- **Time-matched comparison**, over half-hours with $s_t > 0$:
  - the share of those half-hours with net imports;
  - net imports during them;
  - shortfall above observed net imports, $\Delta t \sum_t \max\big(0, s_t - \max(0, X_t)\big)$;
  - net imports at the half-hour of peak shortfall.

  The timing comes from the water-filling allocation, which is one optimal allocation among many, and the output says so.

Wording (D18): the model estimates the domestic adequacy gap and the implied import requirement under its assumptions. Nothing here shows how much of the historical imports was strictly necessary for security.

## 9. Running it and outputs

```bash
python -m src.adequacy.run --y2019 data/eco2mix_2019.csv --y2022 data/eco2mix_2022.csv
```

Optional arguments: `--capacities inputs/capacities.csv` (the default path), `--availability-2019 FILE --availability-2022 FILE` (columns `ts_utc, nucleaire, gaz, charbon, fioul`, in MW) and `--out results` (the default folder, gitignored).

| File | Content |
|---|---|
| `adequacy_results.json` | everything: data summary and monthly budgets, hydro power limits with their basis, checks, every case × pumped-storage variant × scenario, Shapley tables (annual and monthly), Test B, import comparison, frozen-fossil diagnostic, sensitivity ranges |
| `scenarios.csv` | case, pumped-storage variant, scenario, $U$ (GWh), $P$ (GW), hours short |
| `monthly_unmet.csv` | the same by month (input for the figure) |
| `shapley.csv` | $\varphi_D$, $\varphi_A$, $I$ and total for $U$ and $P$, per case and variant |

## 10. Function map and what the tests establish

| Equation or rule | Function | Main tests |
|---|---|---|
| Loading, conventions, local months | `data.load_year`, `data.completeness` | `test_adequacy_data.py` |
| $N^{\text{base}}$, $N^{\text{flex}}$, $p_t$ | `inputs.demand_side` | baseline net demand = nuclear + fossil + lakes + net imports on balanced data; $N^{\text{flex}} - N^{\text{base}} = g^{\text{obs}}$ |
| $E^{L}_m$, $E^{T}_m$ | `inputs.monthly_budgets` | MW → MWh by hand |
| $K_m$ cases, aggregation | `inputs.generation_based_availability`, `inputs.aggregate_availability` | total-first lowest daily mean; days with 46 half-hours |
| $K^{L}$, $K^{T}$ | `inputs.hydro_capacity` | proxy over both years, labelled a lower bound |
| $\theta_m$, $\ell_t$ | `allocation.water_fill` | two hand examples; constraints; $F_m(\theta_m) = E^{L}_m$; closed-form $U$; **$U$ and $P$ equal two independent LP optima** |
| Joint LP | `allocation.min_shortfall_lp` | equals the maximum-flow closed form (v6, section 7.1); reduces to water-filling without pumped storage |
| Scenario assembly | `scenarios.run_four_scenarios` | each scenario uses the right years; budgets and limits follow the driver-D year; no water moves between months; flexible is never worse than the baseline |
| Shapley | `shapley.shapley_two_players` | **owner's Oct 6 example: 2000/2500/3200/4200 → $\varphi_D$ = 750, $\varphi_A$ = 1450**; efficiency; solo effect + $I/2$; dummy; symmetry; monthly shares add up to the annual ones |
| Checks, Test B, imports | `checks.*` | small known inputs |
| End to end | `run.run` | synthetic files, with and without capacities and reconstructed availability |

All tests use synthetic data. No real data is used in CI.
