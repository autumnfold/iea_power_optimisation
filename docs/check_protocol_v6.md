# Methodology note v6 (for final owner approval)

Status: **draft, not adopted.** Versions v1–v5 were written and revised on 2026-11-06. The owner's approvals and requested revisions are listed under "Change history" at the end. v6 corrects two technical definitions, the storage upper bound in section 8.1 and the no-event case in section 6, after the owner approved the research design and the earlier corrections in v5. v5 made the owner's final changes:
- the pumping sign convention;
- the wording of the section 4.1 sensitivity;
- a required monthly storage diagnostic;
- months with $r_m > 1$ flagged as a diagnostic only.

It also corrects the inconsistencies found in a whole-document review. The research design is unchanged and no new assumptions are introduced. Nothing here changes `PROJECT_STATE.md` until the owner approves it. Proposed final location: `docs/methodology.md`.

Labels used throughout: **[fact]** = observed in the data or stated by a cited source; **[assumption]** = a modelling choice we make and must state in the report; **[open]** = not yet resolved.

---

## 1. Objective and system boundary

**Objective (owner, 2026-11-06):** estimate how changes in (1) net demand and hydro resources, (2) dispatchable capacity availability, and (3) fuel and carbon prices affected the **variable cost of meeting French electricity demand using domestic generation** between 2019 and 2022.

- **Closed system [assumption]:** international exchanges are excluded from all eight counterfactual runs. Observed exchanges are used only to validate the two actual years and in diagnostic Test A (section 8.2).
- **Cost [assumption]:** short-run variable cost: fuel, carbon, and variable operation and maintenance. This is not a market price and not a full cost; the report says so in its first results paragraph.
- **Demand [assumption]:** inelastic within each scenario (the observed consumption of the driver-1 year).
- **Unmet energy [open]:** its treatment in the cost attribution is decided after check 2b. No backstop price exists in this note.
- **Status of the results: modelled attribution, not real-world causation.** The Shapley shares are an exact decomposition of the change in **modelled** cost between the modelled 2019 system (S1) and the modelled 2022 system (S8), under the assumptions of this note. They describe how the model's cost responds when each group of inputs is switched between years. They are **not** estimates of what caused the real-world change in French electricity costs, and the report does not present them as such. Statements about the real system remain conditional on:
  - the closed-system boundary;
  - the inputs held fixed (section 2);
  - the treatment of unmet energy;
  - the validation checks of section 8, which test the reconstruction's consistency, not its causal validity.

## 2. Drivers: every input that differs between years belongs to exactly one driver

| Input | Resolution | Driver |
|---|---|---|
| Consumption $C_t$ | 30 min | 1. Net demand and hydro resources |
| Wind $W_t$, solar $S_t$ | 30 min | 1 |
| Run-of-river and daily pondage $R_t$ (`hydraulique_fil_eau_eclusee`) | 30 min | 1 |
| Bioenergy $B_t$ | 30 min | 1 |
| Lake energy budget $E^{L}_m$ and lake capacity $K^{L}$ | monthly | 1 |
| *(check 2b only)* pumped-storage pumping profile $p_t \ge 0$ and generation budget $E^{T}_m$ (section 8.1) | 30 min / monthly | 1 |
| Nuclear available capacity $K^{\text{nuc}}_m$ | monthly (section 4.1) | 2. Dispatchable capacity availability |
| Fossil available capacity by technology $K^{\text{gas}}_m$, $K^{\text{coal}}_m$, $K^{\text{oil}}_m$ | monthly (section 4.1) | 2 |
| Gas, coal and oil prices | monthly | 3. Fuel and carbon prices |
| Carbon (EU ETS) price | monthly or annual [open: source] | 3 |
| USD→EUR exchange rate (World Bank prices are in USD) | monthly | 3 |

**Held fixed across all scenarios [assumption, each value sourced in `ASSUMPTIONS.md`]:**

- plant efficiencies (heat rates) and emission factors per technology;
- variable operation and maintenance costs;
- nuclear variable (fuel) cost per MWh;
- pumped-storage pumping and generating capacities, and technical efficiency $\eta$ (later LP only);
- zero marginal cost for wind, solar and hydro;
- the monthly block structure;
- inelastic demand.

**Frozen-fossil diagnostic (approved as a sensitivity analysis, not an attribution):** rerun all eight scenarios with fossil capacity held at its 2019 values, then at its 2022 values, and report how much driver 2's Shapley share moves.

## 3. The eight Shapley scenarios

A scenario is a triple $(d_1, d_2, d_3)$ with $d_i \in \{2019, 2022\}$: it takes **all** driver-$i$ inputs from year $d_i$.

| Scenario | Driver 1 | Driver 2 | Driver 3 | Note |
|---|---|---|---|---|
| S1 | 2019 | 2019 | 2019 | modelled 2019, $v(\varnothing)$ |
| S2 | 2022 | 2019 | 2019 | |
| S3 | 2019 | 2022 | 2019 | hardest adequacy case expected [open] |
| S4 | 2019 | 2019 | 2022 | |
| S5 | 2022 | 2022 | 2019 | |
| S6 | 2022 | 2019 | 2022 | |
| S7 | 2019 | 2022 | 2022 | |
| S8 | 2022 | 2022 | 2022 | modelled 2022, $v(N)$ |

Prices do not affect whether demand can be met, so check 2b needs only the four $(d_1, d_2)$ combinations: S1/S4, S2/S6, S3/S7, S5/S8.

## 4. Monthly load-duration curves and cross-year combination

- **Calendar alignment [fact]:** 2019 and 2022 are both non-leap years and both have daylight-saving changes in March and October, so every month has the same number of half-hours in both years.
- **Construction:** for each month $m$, compute the fixed net-demand profile from the driver-1 year,

  $$N_t = C_t - W_t - S_t - R_t - B_t \quad (+\ p_t \text{ in check 2b only})$$

  where $p_t = -\,\text{pompage}_t \ge 0$ is observed pumping, added as consumption (sign convention: section 8.1).
- **Why cross-year combinations are well defined:** when driver-2 capacities are **constant within each month**, only the distribution of $N_t$ within the month matters, not the calendar position of individual half-hours. The month-$m$ values of year $d_1$ are combined with the month-$m$ capacities of year $d_2$. Both aggregation measures in section 4.1 are constant within the month for this reason.

### 4.1 Monthly capacity aggregation

Starting from the reconstructed half-hourly availability $K^{\text{tech}}(t)$ (section 6), with $\bar{K}^{\text{tech}}_d$ the mean over day $d$:

- **Baseline:** the monthly mean, $K^{\text{tech}}_m = \text{mean}_{t \in m}\, K^{\text{tech}}(t)$.
- **Conservative sensitivity:** the lowest daily mean in the month, $K^{\text{tech},\text{low}}_m = \min_{d \in m}\, \bar{K}^{\text{tech}}_d$, held constant over the month.
  - **Why the daily mean, not the half-hourly minimum:** the half-hourly minimum would let one short event set capacity for a whole month, which is a bound rather than a plausible case.
  - The total nuclear plus fossil availability is aggregated the same way. Because the minimum of a sum is at least the sum of the minima, aggregating each technology separately is slightly more conservative. **We use the total**, and record the choice.
- **[assumption]** Both measures ignore within-month co-movement of availability and net demand (for example, a reactor outage during a cold week). The baseline can understate unmet energy for that reason. The sensitivity provides a conservative stress test of the effect of lower monthly capacity assumptions.

**The original half-hourly series is retained for validation (no cross-year use):**

1. **Physical consistency:** $K^{\text{nuc}}(t) \ge$ observed nuclear generation in (almost) every half-hour, and the same for each fossil technology (section 6).
2. **Test A** (section 8.2) uses the half-hourly availability, with the chronological hydro allocation of section 8.1, in the actual years S1 and S8.
3. **Aggregation error:** in S1 and S8 only, compare unmet energy from the chronological allocation (section 8.1, stage 1) with the load-duration-curve allocation (section 7.1) under the baseline aggregation. The difference measures the combined effect of monthly aggregation and order-free hydro placement, which cannot be measured in the cross-year scenarios.

## 5. Hydro

### 5.1 Run-of-river and daily pondage
Fixed observed profile $R_t$, subtracted in $N_t$. **[assumption]** The limited within-day flexibility of pondage is ignored.

### 5.2 Lakes
For each month: $E^{L}_m = \sum_{t \in m} \text{lacs}_t\,\Delta t$ (with $\Delta t = 0.5$ h), $0 \le \ell_t \le K^{L}$, and $\sum_{t \in m} \ell_t\,\Delta t \le E^{L}_m$.

- **What $E^{L}_m$ is [assumption]:** a **proxy for the energy available in month $m$**, not a measurement of natural water availability. It is the result of each year's actual reservoir management (inflows plus the operator's choices of when to draw down).
- **No inter-month shifting [assumption]:** water cannot be moved between months. This is likely pessimistic in the hardest months, because a real operator facing a nuclear shortfall would save water for them.
- **Endogeneity caveat [assumption]:** because $E^{L}_m$ reflects each year's operating decisions, the 2022 monthly budgets partly embed 2022 scarcity conditions. Annual lake energy is mostly driven by inflows (weather); its monthly split is partly an operating response. This is stated as a limitation of putting lakes in driver 1.
- **Capacity $K^{L}$:** installed lake turbine capacity if sourced; otherwise the observed monthly maximum (a lower bound) [open].

### 5.3 Pumped storage: technical efficiency vs observed accounting ratio

Write $E^{P} \ge 0$ for pumping energy and $E^{T} \ge 0$ for generation over a period. The data definitions and the sign convention are in section 8.1. Further:

- $\eta_p$ and $\eta_g$ are the pumping and generating efficiencies, so $\eta = \eta_p \eta_g$ is the **technical round-trip efficiency**, a property of the equipment;
- $\Delta S$ is the change in stored energy over the period (in stored-energy terms);
- $I$ is any natural inflow to the upper reservoirs.

Then

$$\Delta S = \eta_p E^{P} + I - \frac{E^{T}}{\eta_g} \quad\Longrightarrow\quad \frac{E^{T}}{E^{P}} = \eta + \eta_g\,\frac{I - \Delta S}{E^{P}}.$$

- The left-hand side is an **observed accounting ratio**. It equals the technical efficiency $\eta$ only if $I = \Delta S$, in particular if there is no natural inflow and the reservoir ends the period where it started.
- **[fact]** The observed annual ratios are 0.85 (2019: 5.46 / 6.43 TWh) and 0.81 (2022: 6.02 / 7.44 TWh).
- These are therefore **observed ratios, not technical efficiencies**. A ratio above $\eta$ would mean natural inflows or a net drawdown of the reservoirs. A ratio below $\eta$ would mean a net filling in excess of any inflow. Some French pumped-storage plants also receive natural inflows **[open, to check]**. Monthly ratios are expected to vary more than annual ones, because reservoir levels can change more over a month than over a year.
- **Boundary differences [open]:** `pompage` and `hydraulique_step_turbinage` must cover the same set of plants for the ratio to be meaningful.
- **Where each quantity is used:** the technical efficiency $\eta$ appears only in the later LP below. The monthly observed ratio $r_m$ appears only as an accounting factor in the chronological allocation of check 2b (section 8.1). Neither is substituted for the other.

**In the load-duration-curve allocation of check 2b (section 7.1): an optimistic flexibility assumption [assumption, labelled optimistic].** Observed pumping $p_t$ is added to demand at its observed times. The observed monthly generation budget $E^{T}_m$ may then be placed in **any** half-hours of the month (jointly with lake water, section 7), up to the generating capacity $K^{T}$. This is optimistic because:

1. generation is **not** tied to the chronological timing of pumping, so the model can generate before the corresponding water has been pumped up;
2. the upper reservoir's capacity within the month is ignored;
3. the generation budget can be concentrated in the hardest periods without regard to the actual reservoir level.

To bracket this assumption, check 2b also reports a **fixed-profile variant**: pumped-storage generation fixed at its observed half-hourly profile (subtracted in $N_t$ like run-of-river). Within the model, this variant is pessimistic relative to the flexible one.

**In the later LP (proposal, to approve then):** pumping $p_t \ge 0$ and generation $g_t \ge 0$ are decided by the model within each month, subject to

$$\sum_{t \in m} g_t\,\Delta t = \eta \sum_{t \in m} p_t\,\Delta t, \qquad 0 \le p_t \le K^{P},\quad 0 \le g_t \le K^{T}.$$

This equation assumes **$\Delta S_m = 0$ and $I_m = 0$** in every month: storage is energy-neutral within each month, with no natural inflow. It also cannot enforce "pump before generating" or a reservoir size limit within the month, because a load-duration curve has lost the order of hours. Planned sensitivities:

1. $\eta$ taken from a cited technical value, then varied;
2. a version that adds a monthly term $I^{\text{eff}}_m = \max(0,\ E^{T}_m - \eta E^{P}_m)$ derived from the data. By the identity above, when it is positive it equals $\eta_g (I_m - \Delta S_m)$: it **absorbs natural inflow and net drawdown together** and cannot separate them;
3. "$\le$" instead of "$=$" (storage may end the month fuller, which has no benefit in the model).

## 6. Dispatchable capacity availability (ENTSO-E method)

**What ENTSO-E provides [fact unless marked]:**

- **Installed capacity by production unit:** units of 100 MW or more. Published annually, with values referring to 1 January. Includes the installed net capacity, production type and, where available, commissioning and decommissioning dates.
- **Installed capacity by production type:** aggregated, 1 MW threshold, annual.
- **Unavailability of generation units and of production units:** event messages with planned (A53) or forced (A54) type, a document status (active, cancelled, withdrawn) and message identifiers that carry versions.
- *[to verify in the downloaded data]:* the exact fields of each message (nominal power, available capacity during the event, start and end times), and whether the available capacity can change during one event.
- *[from the Transparency Regulation, to verify]:* only unavailabilities of **100 MW or more** for a generation unit, or **200 MW or more** for a production unit, must be reported. Smaller deratings are therefore **missing**.

**The unavailability data is not an availability series.** It lists events; availability has to be reconstructed:

1. **Unit list per year:** units of 100 MW or more from the installed-capacity-by-unit data (nuclear, gas, coal, oil), with their net capacity $P_u$. Each unit is active between its commissioning and decommissioning dates. Examples: Landivisiau gas from 2022-03-31 **[fact, RTE]**; Fessenheim (two units, closed in 2020) is present in 2019 and absent in 2022 **[to confirm in the unit list]**.
2. **Clean the messages:** keep the latest version of each event; drop cancelled and withdrawn ones; convert all times to UTC.
3. **Rebuild each unit's availability per half-hour.** Let $\mathcal{E}_u(t)$ be the set of outage events for unit $u$ that are active at $t$, after the cleaning of step 2. Then

   $$a_u(t) = \begin{cases} P_u & \text{if } \mathcal{E}_u(t) = \varnothing \ \text{(no event active)}, \\[4pt] \min\Big(P_u,\ \min_{e \in \mathcal{E}_u(t)} \text{avail}_e(t)\Big), \ \text{clipped to } [0, P_u] & \text{otherwise.} \end{cases}$$

   - **If no outage event is active** for unit $u$ at $t$, its availability is its net capacity $P_u$.
   - **Otherwise,** its availability is the minimum of $P_u$ and the available capacities reported by the active events, clipped to $[0, P_u]$. Overlapping events therefore take the most restrictive one.
4. **Aggregate:** $K^{\text{tech}}(t) = \sum_u a_u(t)$, kept as a half-hourly series; the monthly measures follow section 4.1.
5. **Units below 100 MW:** take the aggregated installed capacity minus the sum of listed units, times an assumed availability factor that is **the same in both years** **[assumption]**.
6. **Not captured, by construction [assumption, stated as a limitation]:**
   - deratings below the reporting threshold;
   - non-technical limits that may not be reported (some river-temperature or regulatory limits) **[open]**;
   - voluntary nuclear modulation. This is correct to exclude: modulation is an operating choice, not an unavailability.

**Validation:**

- **Physical consistency** (section 4.1, item 1).
- **Cross-check:** compare annual nuclear availability with EDF's published availability coefficient Kd (annual, Licence Ouverte 2.0).

**Fallback if ENTSO-E fails:**

- nuclear: bracket between the monthly mean and the monthly maximum of observed generation;
- fossil: sourced installed capacity × the same assumed availability factor in both years.

**Practical [open]:** a free ENTSO-E account and API token are needed (owner task). The licence terms could not be read and must be checked before any data enters the repository.

## 7. Check 2b specification (adequacy only, no prices)

### 7.1 Joint lake and pumped-storage allocation (load-duration curve)

Lake water and pumped-storage generation **must not** each pick the same peak half-hours independently. Two resources that each "shave the peak" without seeing each other can double-cover some periods and leave others uncovered. They are therefore allocated **jointly**, by solving one small linear programme per month and per scenario.

For month $m$:
- $K^{\text{disp}}_m = K^{\text{nuc}}_m + K^{\text{fos}}_m$ is the dispatchable capacity of the $d_2$ year (baseline or conservative, section 4.1);
- $D_t = \max\big(0,\ N_t - K^{\text{disp}}_m\big)$ is the deficit left before any flexible hydro, with $N_t$ from the $d_1$ year including observed pumping $p_t$;
- the variables are $\ell_t$ (lake), $g_t$ (pumped-storage generation) and $u_t$ (unmet), all $\ge 0$.

$$
\begin{aligned}
\min_{\ell,\,g,\,u}\quad & \sum_{t \in m} u_t\,\Delta t \\
\text{s.t.}\quad & \ell_t + g_t + u_t \ \ge\ D_t && \forall t \in m \\
& 0 \le \ell_t \le K^{L}, \quad 0 \le g_t \le K^{T} && \forall t \in m \\
& \textstyle\sum_{t \in m} \ell_t\,\Delta t \ \le\ E^{L}_m, \quad \sum_{t \in m} g_t\,\Delta t \ \le\ E^{T}_m &&
\end{aligned}
$$

- This **minimises total unmet energy subject to both resources' energy budgets and power limits at once.** The optimum is the minimum unmet energy achievable with the given hydro.
- **Pumped storage here is the optimistic flexible treatment** of section 5.3. The fixed-profile variant replaces $g_t$ with the observed generation, subtracted in $N_t$.
- **Solver:** HiGHS, already a pinned project dependency. Each problem has about 1,500 half-hours × 3 variables: trivial in size.
- **Why not sequential filling:** filling one resource first and then the other on the remaining deficit is not guaranteed to be optimal in general. The joint LP is.
- Only the deficit $D_t$ enters, so hydro is placed only where it changes adequacy. Where leftover water goes does not matter for this check.
- **Independent test (optional, for the test suite only):** the same optimum can be computed in closed form by treating the problem as a maximum flow (lake and pumped storage as sources, half-hours as sinks). The maximum hydro energy usefully placed is

  $$
  \min\Big\{\,E^{L}_m + E^{T}_m,\ \ E^{L}_m + \sum_t \min(D_t, K^{T})\Delta t,\ \ E^{T}_m + \sum_t \min(D_t, K^{L})\Delta t,\ \ \sum_t \min(D_t, K^{L} + K^{T})\Delta t \,\Big\}
  $$

  and unmet energy is $\sum_t D_t\,\Delta t$ minus that value. Agreement between the LP and this formula is a test of the implementation. It is not part of the report's mathematics.

### 7.2 What is computed and reported

**First output, required before any chronological storage result is interpreted:** the monthly pumped-storage diagnostic of section 8.1, for both years: $E^{P}_m$, $E^{T}_m$, $r_m$, and the months flagged with $r_m > 1$.

Then, for each of the four $(d_1, d_2)$ combinations, each month, and each variant:

- hours short, unmet energy (GWh), largest shortfall (GW), and a monthly breakdown;
- **variants:**
  - capacity: ENTSO-E reconstruction, if available, otherwise the fallback brackets;
  - aggregation: baseline or conservative (section 4.1);
  - pumped storage: optimistic flexible, or fixed profile (section 5.3);
  - the frozen-fossil diagnostic;
- for S1 and S8: the chronological allocation (section 8.1), with its three pumped-storage variants, Test A, and the aggregation-error comparison (section 4.1, item 3).

Every number of the run is saved to JSON.

## 8. Pre-registered diagnostics (fixed before running check 2b)

### 8.1 Chronological hydro allocation for the actual years

Test A compares modelled shortfalls with observed imports **period by period**. That comparison only means something if the shortfall series keeps calendar order, and the load-duration-curve allocation of section 7.1 does not: it sorts the half-hours of each month. For **S1 and S8 only**, the two scenarios that have a real chronology, hydro is therefore also allocated chronologically, by one LP per month.

**Pumped-storage data and sign convention [fact, check 1].** The source column `pompage` records pumping as a **negative** number: it is between −4,036 and −3 MW in every half-hour of 2019 and 2022. It enters the electricity balance with a plus sign: $C_t = \sum_k P_{k,t} + \text{pompage}_t + \text{ech}_t$. The storage equations below need pumping as a **positive** quantity, so this note uses

$$p_t = -\,\text{pompage}_t \ \ge\ 0, \qquad g^{\text{obs}}_t = \text{hydraulique\_step\_turbinage}_t \ \ge\ 0,$$

$$E^{P}_m = \sum_{t \in m} p_t\,\Delta t, \qquad E^{T}_m = \sum_{t \in m} g^{\text{obs}}_t\,\Delta t.$$

Everywhere in this note, $p_t$, $E^{P}_m$ and $E^{T}_m$ are non-negative, and pumping adds to net demand: $N_t$ includes $+\,p_t$ (section 4).

**Inputs for month $m$ of the actual year** (all observed or reconstructed for that same year):

- the deficit before flexible hydro, using the **half-hourly** availability rather than a monthly constant: $D_t = \max\big(0,\ N_t - K^{\text{disp}}(t)\big)$, with $K^{\text{disp}}(t) = K^{\text{nuc}}(t) + K^{\text{fos}}(t)$ (section 6) and $N_t$ including $p_t$;
- lakes: monthly budget $E^{L}_m$ and power limit $K^{L}$;
- pumped storage: observed pumping $p_t$ at its observed times, monthly generation budget $E^{T}_m$, power limit $K^{T}$, and the calibrated storage envelope (below).

**Calibrated storage envelope.** This is expressed in generation-equivalent units, so the technical efficiency $\eta$ is not used:

- the monthly observed accounting ratio $r_m = E^{T}_m / E^{P}_m$. It absorbs efficiency, natural inflows and the month's change in stored energy (section 5.3). It is used here only as an accounting factor and **is not a technical efficiency**;
- cumulative observed pumping and generation: $P_t = \sum_{\tau \le t} p_\tau\,\Delta t$ and $G^{\text{obs}}_t = \sum_{\tau \le t} g^{\text{obs}}_\tau\,\Delta t$;
- the smallest starting level consistent with the observed operation, under this accounting: $S_0 = \max\big(0,\ \max_t\,(G^{\text{obs}}_t - r_m P_t)\big)$;
- the highest level the observed operation reached, under this accounting, including the starting level, which is part of the trajectory: $S^{\max}_m = \max\Big\{S_0,\ \max_t\,\big(S_0 + r_m P_t - G^{\text{obs}}_t\big)\Big\}$.

By construction, the observed operation satisfies these bounds.

**[assumption] What the envelope is, and what it is not.** $r_m$ spreads whatever made generation differ from pumping in month $m$ (round-trip losses, natural inflows, and the change in stored energy) **uniformly over the month's pumping**. The result is an **envelope calibrated to the observed operation**: the observed trajectory fits inside it by construction. It is not a reconstruction of the physical reservoirs, and it is **not necessarily more restrictive than real operation**:

- **It may be too narrow.** Real reservoir capacities and starting levels are unknown. $S^{\max}_m$ and $S_0$ are only the values the observed trajectory needed under this accounting, and real reservoirs may be larger or start fuller.
- **It may be too permissive.** Spreading $r_m$ uniformly misplaces stored energy in time. If natural inflow arrived at particular moments, or the reservoirs drew down early in the month, the envelope credits stored energy when the real system did not have it. In some half-hours it can therefore allow generation the real system could not have produced, and in others forbid generation it could have.
- **Consequence:** the envelope's net effect on unmet energy, **relative to reality**, cannot be signed in advance. It is stated as a limitation.
- **What can be signed [fact about the construction]:** within the chronological allocation (same half-hourly deficits $D_t$), the observed generation profile is one admissible schedule, and every schedule the envelope allows also satisfies the monthly budget and power limit alone. So the envelope result always lies **between** two variants of this same chronological LP:
  - pumped-storage generation fixed at its observed profile (most unmet energy);
  - the monthly budget and power limit only (least unmet energy).

  This holds provided $K^{T}$ is at least the observed maximum generation. Check 2b reports all three variants for S1 and S8.

**Required diagnostic before interpretation.** Before any chronological storage result is interpreted, check 2b reports, for every month of both years, $E^{P}_m$, $E^{T}_m$ and $r_m$.

- **Months with $r_m > 1$ are flagged for review.** In such a month generation exceeded pumping, which is possible only with natural inflows or a net drawdown.
- **The flag is a diagnostic only.** Flagged months are **not** switched automatically to fixed-profile generation. Both the fixed-profile and the calibrated-envelope variants are retained and reported for every month, so the owner can compare them.
- The same table shows months where a small $E^{P}_m$ makes $r_m$, and therefore the envelope, unstable.

**Months without pumping.** $r_m$ is undefined when $E^{P}_m = 0$, so such months get explicit rules:

- **$E^{P}_m = 0$ and $E^{T}_m = 0$:** no pumped-storage allocation; $g_t = 0$ for the whole month.
- **$E^{P}_m = 0$ and $E^{T}_m > 0$:** no envelope is built. Pumped-storage generation is fixed at its observed half-hourly profile for that month (subtracted in $N_t$ like run-of-river).
- **[fact, check 1]** **Neither case occurs in 2019 or 2022.** $p_t > 0$ in every one of the 17,520 half-hours of both years, with no missing values. The smallest value is 4 MW in 2019 and 3 MW in 2022, so every month has $E^{P}_m > 0$. The rules are kept so the method is complete for other years or other data versions. *Hypothesis, not checked:* the smallest values, a few MW, may be auxiliary consumption rather than real pumping; this does not affect the rules.

**LP for month $m$.** Variables $\ell_t$, $g_t$, $u_t \ge 0$ and storage level $S_t$, in calendar order $t = 1, \dots, T_m$, with $S_0$ as the starting level:

$$
\begin{aligned}
\min_{\ell,\,g,\,u,\,S}\quad & \sum_{t} u_t\,\Delta t \\
\text{s.t.}\quad & \ell_t + g_t + u_t \ \ge\ D_t && \forall t \\
& 0 \le \ell_t \le K^{L}, \qquad \textstyle\sum_t \ell_t\,\Delta t \le E^{L}_m && \\
& 0 \le g_t \le K^{T}, \qquad \textstyle\sum_t g_t\,\Delta t \le E^{T}_m && \\
& S_t = S_{t-1} + r_m\,p_t\,\Delta t - g_t\,\Delta t, \qquad 0 \le S_t \le S^{\max}_m && \forall t
\end{aligned}
$$

- Pumped-storage generation can only draw on stored energy **credited by the envelope's accounting**: pumped energy scaled by $r_m$, plus the starting level $S_0$. Storage cannot exceed $S^{\max}_m$. Because $r_m P_{T_m} = E^{T}_m$, the monthly budget means the month ends with at least the starting level $S_0$.
- **Lakes [assumption]:** only the monthly budget and the power limit apply, with no within-month storage constraint, because lake reservoirs are large relative to a month's use.
- **Output (stage 1):** the minimum total unmet energy $U^{*}_m$ and a timestamped shortfall series. These are used as the aggregation-error reference (section 4.1, item 3).
- **Why a second stage is needed for Test A:** minimising **total** unmet energy does not pin down **where** it falls. Several schedules can reach the same total, and the solver may place shortfall in a half-hour where France exported. That would make a per-period comparison with imports fail for an artificial reason.
- **Stage 2 (Test A).** Same constraints, plus $u_t \le \max(0, X_t) + |\varepsilon_t| + v_t$ with $v_t \ge 0$, where $\varepsilon_t$ is the balance residual of period $t$ from check 1. Minimise the violation energy $V_m = \sum_t v_t\,\Delta t$. The question becomes: *is there a hydro schedule within our constraints that keeps every half-hourly shortfall within observed imports?* $V_m = 0$ means yes.
- **Remaining idealisation [assumption]:** the LP has perfect foresight within the month (it knows every deficit in advance), so it is still an optimistic operator. The fixed monthly budgets push the other way. The storage envelope's direction relative to reality is unknown (see above).

**How this differs from the load-duration-curve allocation (section 7.1):**

| | Load-duration-curve allocation (7.1) | Chronological allocation (8.1) |
|---|---|---|
| Scenarios | all four adequacy combinations | S1 and S8 only (real chronology) |
| Dispatchable capacity | monthly constant (baseline or conservative) | half-hourly reconstructed series |
| Order of half-hours | ignored (sorted within the month) | calendar order kept |
| Pumped-storage generation | monthly budget placed anywhere (optimistic), or fixed observed profile | calibrated envelope, plus the fixed-profile and budget-only variants for comparison |
| Output | unmet energy per month, no timestamps | half-hourly shortfalls with timestamps |
| Used for | attribution inputs, Test B | Test A, aggregation-error reference |

### 8.2 Test A: consistency diagnostic (not pass/fail)

In each actual year (S1, S8), solve stage 2 of section 8.1 and report the violation energy $V = \sum_m V_m$. Here $X_t$ is `ech_physiques` (import-positive **[fact, check 1]**). The per-period tolerance $|\varepsilon_t|$ is the observed balance residual: at most 3 MW in 2019 and 107 MW in 2022, from check 1. It is pre-registered with this note. Test A is run with the calibrated envelope.

**What Test A can detect [fact about the construction]:** the observed operation is itself a candidate schedule in stage 2. The observed lake and pumped-storage output respects the observed budgets, and the calibrated envelope contains the observed trajectory by construction. If, in addition, the reconstructed availability and power limits are at least the observed output in every period, the observed operation keeps each shortfall within $\max(0, X_t) + |\varepsilon_t|$, so $V = 0$. **Test A is therefore a check that the reconstruction contains the observed operation.** It detects reconstruction and accounting errors. It cannot detect restrictive hydro *budgets*, because those budgets are the observed ones, and it says nothing about the cross-year scenarios.

A violation ($V > 0$) means that no admissible schedule supplies what France demonstrably produced in some periods. **Possible causes, to be investigated in this order:**

1. reconstructed nuclear or fossil availability below observed generation in some periods (the physical-consistency check of section 4.1 locates these);
2. hydro power limits $K^{L}$ or $K^{T}$ below observed output (for example, a sourced installed capacity that does not match the éCO2mix categories);
3. missing resources (units below 100 MW, batteries, demand response; see the unexplained 66 MW balance residual in 2022);
4. accounting-boundary differences (national perimeter, physical vs commercial exchanges) larger than the residual tolerance.

Report the number of violating periods, their energy and their months.

**What a clean Test A shows, and what it does not:** a clean result shows only that observed imports were **sufficient** to cover the modelled shortfall in every period. It does not show that imports were **necessary**, and it does not validate the model's cost results.

### 8.3 Test B: the 36 GWh pre-registered tolerance for 2019

**Rule:** in S1 (modelled 2019), using the load-duration-curve allocation (section 7.1) with the baseline aggregation and the optimistic pumped-storage variant, unmet energy should not exceed **36 GWh** (0.01% of 2019 net demand as computed in check 1: 361.8 TWh). Hours short are reported alongside. Results for all other variants are reported but are not tested.

**What this tolerance is, and what it is not:**

- **It is a chosen convention, fixed in advance.** Its value is not derived from the data's error distribution and **is not a statistically established accuracy threshold**. Its purpose is procedural: it is written down before the results exist, so the results cannot shape the test.
- **Context for the order of magnitude (not a justification of the exact value):**
  - The data's own accounting differences are much larger: the 2022 balance residual is 0.58 TWh per year (unresolved), and éCO2mix consumption differs from RTE's published totals by about 2.5 TWh per year.
  - France's security-of-supply standard allows at most 3 hours per year of supply failure on average (article D141-12-6 of the energy code). That is a probabilistic average for the interconnected system, so the comparison is an analogy only.
- **Passing it does not validate the model.** It shows only that the modelled 2019 closed system is close to meeting all demand under our reconstruction. It is a pre-registered sanity check, not sufficient evidence that the capacities, hydro treatment or costs are right. In particular:
  - the balance residual is small in 2019 (mean 0.7 MW) but unresolved in 2022 (about 66 MW on average), so the same reconstruction is not verified to close the 2022 balance;
  - a pass can still hide offsetting errors (for example, capacity overstated while hydro is too restrictive).

  Model credibility rests on all the checks together: the balance closure (check 1), Test A, the physical-consistency checks (section 4.1), the aggregation-error comparison, and the later validation against the actual generation mix. Even together, these test the reconstruction's consistency, not the causal interpretation of the attribution (section 1).

**Secondary comparison (reported, not a requirement):** the ratio of 2019 to 2022 unmet energy under the same assumptions.

**Interpretation:**

- **2019 within tolerance:** the modelled 2019 closed system is consistent with near self-sufficiency under our assumptions. Any 2022 or counterfactual shortfall is then a result of the **modelled** closed-system counterfactual, not a statement about the real system, with the caveats above.
- **2019 above tolerance, Test A clean:** the closed-system reconstruction cannot meet all 2019 demand under the specified assumptions, and in every shortfall period observed imports were at least as large as the modelled shortfall. This does **not** establish that France depended on imports. It shows that imports were sufficient to cover the modelled shortfall, but the shortfall itself may come from the assumptions behind the section 7.1 allocation rather than from a physical inability of the domestic system. Examples: the monthly capacity aggregation, no inter-month water shifting, hydro power limits, missing units below 100 MW, or the availability reconstruction. Consequence: an unmet-energy treatment is needed in every scenario, and the report discusses the closed-system assumptions explicitly. That is a modelling decision.
- **2019 above tolerance, Test A violated:** investigate the causes listed under Test A before drawing any conclusion.

## 9. Open items (to resolve before the LP)

- Treatment of unmet energy in the cost attribution (after check 2b).
- Review of any months flagged with $r_m > 1$ (after the first output of check 2b; no automatic rule).
- ENTSO-E download, message fields and licence; fallback if unavailable.
- Installed capacities: lakes, pumped storage (pumping and generating), fossil by technology, 2019 and 2022.
- Technical pumped-storage efficiency (cited value); whether plants receive natural inflows.
- Carbon price source and licence; the USD→EUR exchange-rate source.
- The 66 MW residual and the duplicate timestamps in the 2022 file.

## Change history

### Changes in v6

- **Section 8.1, storage upper bound:** $S^{\max}_m = \max_t\big(S_0 + r_m P_t - G^{\text{obs}}_t\big)$ replaced by $S^{\max}_m = \max\big\{S_0,\ \max_t\big(S_0 + r_m P_t - G^{\text{obs}}_t\big)\big\}$. The starting level is part of the storage trajectory, so the upper bound must be at least $S_0$. Without this, the starting level could exceed the bound if the observed level fell after the first half-hour and never recovered. The statement "by construction, the observed operation satisfies these bounds" now holds for the starting level too.
- **Section 6, step 3:** the availability reconstruction now defines the case where no outage event is active. Availability is then $P_u$. Otherwise it is the minimum of $P_u$ and the active events' available capacities, clipped to $[0, P_u]$. Previously, the minimum over an empty set of events was undefined.

No other wording, equations, assumptions or design elements were changed.

### Changes in v5

**Requested by the owner:**
- **Section 8.1:** explicit pumping sign convention, $p_t = -\,\text{pompage}_t \ge 0$, with $g^{\text{obs}}_t$, $E^{P}_m$ and $E^{T}_m$ defined as non-negative. It explains that the source records pumping as negative, while the storage equations use positive pumping. The same convention is referenced at the first use of $p_t$ (sections 2 and 4) and in section 5.3.
- **Section 4.1:** "the sensitivity bounds the effect from the conservative side" replaced by "The sensitivity provides a conservative stress test of the effect of lower monthly capacity assumptions."
- **Sections 8.1 and 7.2:** a required diagnostic reporting $E^{P}_m$, $E^{T}_m$ and $r_m$ for every month, as the first output of check 2b and before any chronological storage result is interpreted.
- **Section 8.1:** months with $r_m > 1$ are flagged for review as a diagnostic only, with no automatic switch to fixed-profile generation. Both the fixed-profile and calibrated-envelope variants are retained. This replaces the v4 proposal that flagged months might be switched.

**Consistency corrections from the whole-document review (no change to the research design):**
- **Section 1:** an explicit statement that the Shapley shares are an exact decomposition of **modelled** cost, not estimates of real-world causes, and that the validation checks test consistency, not causal validity. The objective wording is unchanged.
- **Section 8.3, "Test A clean" interpretation:** the listed possible sources of the 2019 shortfall included "the calibrated storage envelope". But Test B uses the section 7.1 allocation, which has no storage envelope. They now list the assumptions of that allocation instead.
- **Section 8.3:** "a necessary sanity check" changed to "a pre-registered sanity check". The interpretation already allows a 2019 result above tolerance without invalidating the model, so "necessary" contradicted it. The residual bullet now distinguishes 2019 (mean 0.7 MW) from 2022 (about 66 MW).
- **Section 5.3:** the sensitivity term $\max(0, E^{T}_m - \eta E^{P}_m)$ is renamed $I^{\text{eff}}_m$. By the identity, it absorbs natural inflow and net drawdown together, so it is no longer called a natural-inflow term. A sentence states where $\eta$ and $r_m$ are each used. "A ratio below $\eta$ would mean a net filling" now reads "a net filling in excess of any inflow".
- **Section 5.3:** the optimistic pumped-storage treatment is now tied to the section 7.1 allocation, since check 2b also contains the chronological allocation of section 8.1. "Pessimistic" for the fixed-profile variant is stated as relative to the flexible variant, within the model.
- **Section 8.1:** "can only use water already pumped up" and "cannot exceed the observed maximum" reworded to the envelope's accounting terms ("stored energy credited by the envelope's accounting"; "cannot exceed $S^{\max}_m$"), consistent with the envelope not being a physical reservoir. $S_0$ and $S^{\max}_m$ are now defined "under this accounting".
- **Section 8.1 table:** the pumped-storage row now names the calibrated envelope and its two comparison variants.
- **Sections 8.2 and 8.3:** the limits of each test are stated alongside the results they cannot support. Test A says nothing about the cross-year scenarios and does not validate costs. The section 8.3 interpretation refers to the **modelled** counterfactual.

### Changes in v4

- **Section 8.1, storage envelope:** no longer claims that real reservoirs are at least as large as $S^{\max}_m$, or that the envelope is conservative. It explains that $r_m$ is an accounting factor applied uniformly, so the envelope is calibrated to the observed operation and may be too narrow or too permissive. Its effect relative to reality cannot be signed. Within the model, its result is bracketed by the fixed-profile and fully flexible variants, which check 2b reports.
- **Section 8.1, months without pumping:** explicit rules for $E^{P}_m = 0$. The data show that no such month occurs in 2019 or 2022.
- **Section 8.3 (consistency only, one word):** "conservative storage envelope" → "calibrated storage envelope", to match section 8.1.

### Changes in v3

- **Section 8.1 (new):** chronological hydro allocation for S1 and S8, with half-hourly availability, monthly lake and pumped-storage budgets and power limits, and a pumped-storage storage envelope derived from observed operation. It produces timestamped shortfalls for Test A. A comparison table with the load-duration-curve allocation is included.
- **Section 8.2:** Test A is now a feasibility test (stage 2 of section 8.1): does a schedule exist that keeps every half-hourly shortfall within observed imports plus the balance residual? The note states what this can detect (reconstruction and accounting errors) and what it cannot (restrictive hydro budgets). A clean result shows imports were sufficient, not necessary.
- **Section 8.3:** the "Test A clean" interpretation no longer claims that France depended on imports. Test B's rule now names the allocation it uses (section 7.1).
- **Section 4.1, item 3:** the aggregation-error reference is now the chronological allocation.

### Changes from v1 (made in v2)

- **Section 4.1 (new):** baseline monthly mean; conservative sensitivity using the lowest daily mean; the half-hourly series retained for physical consistency, Test A and the aggregation-error comparison.
- **Section 5.3:** pumped-storage treatment in check 2b explicitly labelled as an optimistic flexibility assumption; pessimistic fixed-profile variant added.
- **Section 7.1 (new):** joint lake and pumped-storage allocation by one LP per month and scenario, minimising unmet energy; optional closed-form test.
- **Section 8, Test B:** recast as a pre-registered convention; scope of the test fixed (S1, baseline, optimistic pumped storage); passing it explicitly does not validate the model.

## Sources

- RTE, French Annual Electricity Review 2022: <https://analysesetdonnees.rte-france.com/en/electricity-review-keyfindings>
- RTE, Bilan électrique 2022, production: <https://analysesetdonnees.rte-france.com/bilan-electrique-production>
- ENTSO-E, Detailed Data Descriptions v3r4: <https://eepublicdownloads.entsoe.eu/clean-documents/Transparency/MoP_Ref2_DDD_v3r4.pdf>
- entsoe-apy, outage queries: <https://entsoe-apy.berrisch.biz/ENTSOE/outages/>
- EDF Open Data, availability of EDF SA's nuclear fleet: <https://opendata.edf.fr/datasets/disponibilite-du-parc-nucleaire-d-edf-sa-depuis-2002>
- French Ministry for the Ecological Transition, electricity security of supply: <https://www.ecologie.gouv.fr/politiques-publiques/securite-dapprovisionnement-electricite>
- World Bank, Commodity Prices (CC BY 4.0): <https://datacatalog.worldbank.org/search/dataset/0038238/commodity-prices-history-and-projections>
