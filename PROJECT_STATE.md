# PROJECT_STATE.md

> Single source of truth for the IEA internship project. Last updated: 2026-09-29 23:15 (Week 1: repo skeleton + CI green; repo connected to the Claude Project; 3-generator problem solved by hand; KKT write-up not yet started).
> **Claude: read this file completely before answering anything. Update it at the end of every session (see "Session protocol").**

---

## 1. Goal

Land a summer internship at the **International Energy Agency (IEA, Paris)** next summer (summer 2027), by producing a serious, rigorous, competitive, public project that shows quantitative modelling skill and clear writing.

**Application facts (IEA official internship page, checked 2026-09-29):**
- Must be enrolled full-time in a degree programme in a field related to the IEA's work, for the whole internship.
- Excellent command of English and/or French; strong drafting and communication skills; minimum internship length one month.
- Applications are year-round via the OECD internship platform. Apply at least 3 months before the desired start date. Select IEA as one of the 3 areas of interest. The "Message to hiring manager" field works as the cover letter: state interest in the IEA, the type of role and the area of work.
- Some individual IEA postings have required Master's/PhD enrolment. **Check the level requirement of every posting before applying.**
- **Target: application submitted by ~Feb 1, 2027. Hard deadline: Feb 15, 2027.**
- To do: ask the Paris-Saclay department about the *convention de stage* process.

## 2. Owner profile

- L2 Mathematics, Université Paris-Saclay (France).
- Very good in Python; comfortable in C++; learning LaTeX; loves math and CS.
- Environment: Windows + WSL Ubuntu, VS Code, GitHub account (knows Git), LM Studio with DeepSeek R1 and Qwen Coder, a recent DeepSeek Harness (`dsh`).
- Not yet experienced with professional project tooling (CI, repo structure, agent workflows). Wants to become as professional as possible.
- **Working style:** wants demanding, direct coaching. Do not go easy. Strong pushes, hard gates, blunt critique.

## 3. The project

**Working title:** *What drove France's power-system costs and prices between 2019 and 2024? An optimisation-based attribution using LP duality and Shapley values, with quantified uncertainty.*

**Origin:** a merge of two candidate projects (LMDI decomposition + weather normalisation, and a power-system optimisation roadmap: dispatch → unit commitment → capacity expansion). Owner chose the hybrid.

### Method (as proposed, to be refined)
1. **Dispatch model:** hourly LP, one full year (8,760 h), French fleet, hydro energy budgets, pumped storage, interconnection.
2. **Drivers (~6):** weather-normalised demand; weather effect on demand (piecewise-linear degree-day regression, change-point base temperature, Newey–West errors); wind/solar availability; nuclear availability; hydro inflows; fuel and carbon prices.
3. **Attribution:** for a pair of years (e.g. 2019 vs 2022), evaluate all driver coalitions (2^6 = 64 LP runs per pair) and compute exact **Shapley attributions** of the change in system cost.
4. **Model-free benchmark:** LMDI decomposition of observed data for the same years. Compare accounting vs counterfactual answers and explain disagreements.
5. **Uncertainty:** block bootstrap on the weather regression + perturbation of cost assumptions, giving confidence intervals on each driver's share. Report whether the driver ranking is robust.
6. **Stretch (only if ahead):** small clustered-unit MILP for one week, compare attribution under LP vs MILP (value function no longer convex, so dual-based attribution breaks down: explain why).

### Mathematical core to be written and proven
- LP value function is convex piecewise linear in the RHS; its derivative is the dual variable (envelope theorem). Availability drivers enter via capacity constraints (duals = scarcity rents).
- Degeneracy: non-unique duals at merit-order kinks; what the solver returns; how it is handled.
- Shapley axioms (efficiency, symmetry, dummy player, additivity); attributions sum exactly to the cost change.
- Path dependence: compare Shapley vs first-order dual attribution Σλ·Δb vs sequential attribution; quantify spread over driver orderings.
- Known traps: cost attribution is clean (cost is the LP objective); **emissions attribution is not** (optimal dispatch can be non-unique), so an explicit tie-break rule (e.g. secondary emissions minimisation) is needed.

### Validation
- Pre-register metrics *before* running: price-duration-curve distance, rank correlation of model dual price vs actual day-ahead price.
- The single-hour dual will not match real prices (interconnection, hydro water values, must-run, bidding). Present divergences as analysis, not failure.

### Novelty statement (NOT yet verified)
Counterfactual merit-order studies and Shapley decompositions in energy each exist separately. Whether this exact combination is unpublished is **unknown**. The claimed contribution is: exact, axiomatic attribution on an LP-based dispatch model, with quantified path dependence and a bootstrap uncertainty layer. Literature search in weeks 1–2 must confirm or shrink this claim. Never overclaim in the application.

## 4. Data sources (verify licence terms for each)
- RTE éCO2mix open data (opendata.reseaux-energies.fr): generation by source, demand, exchanges. *Granularity and year coverage to be checked by the owner.*
- ENTSO-E Transparency Platform (free API key needed): day-ahead prices, cross-border flows.
- Eurostat: energy balances and heating degree days (for the LMDI part and weather normalisation).
- Copernicus ERA5 temperature data (optional, for own degree days).
- Fuel and carbon price series: **source TBD.**
- Cost assumptions: from RTE or IEA published data; every number goes into `ASSUMPTIONS.md` with its source.

## 5. Decisions

| # | Decision | Status |
|---|---|---|
| D1 | Hybrid project (dispatch + attribution + LMDI benchmark) | **Decided** |
| D2 | Unit commitment (MILP) is a stretch, not core | Decided (as proposed) |
| D3 | Minimal AI tooling: one terminal coding agent, this chat as design reviewer/red team, local models as junior helpers; no multi-agent orchestration | Decided (as proposed) |
| D4 | Agents work on branches only; owner reviews diffs; nothing pushes to `main` | Decided (as proposed) |
| D5 | Owner derives by hand first; tests are written from the math before code | Decided (as proposed) |

**Open decisions**
- Which terminal coding agent: Claude Code (needs a Claude account; check pricing) vs DeepSeek Harness `dsh`. **Deferred until after the KKT deliverable.** Status of `dsh`: launched once via `npx @deepseek-ai/dsh web` (version `0.2.0-rc.2`, a release candidate); its local web UI opens, provider/model configuration not done. Unknown whether it can use an LM Studio local server. Pick **one**.
- Which year pairs: proposed 2019→2022 and 2022→2024, not confirmed.
- Final driver list (~6 proposed).
- Interconnection modelling: (A) fixed net exchanges = simple, (B) price-taking neighbours with capacity limits = realistic but hard. Start with A; **gate around Nov 16**: if B isn't working, fall back to A and say so in the report.
- ~~Repo name and URL~~ **Resolved:** https://github.com/jiuyueqiuu/iea_power_optimisation (local clone: `~/projects/iea_power_optimisation` in WSL). Private. Connected to the Claude Project "IEA Project" through the GitHub integration (branch `main`); Claude sees a synced snapshot, not the live repo.

## 6. Timeline (week 1 starts Tue 2026-09-29)

| Weeks / dates | Deliverable | Gate |
|---|---|---|
| 1–2 (Sep 29–Oct 12) | Repo skeleton + green CI; hand derivation of 3-generator dual = marginal cost; solver check; literature search; contribution statement in 3 sentences | Cannot state the contribution in 3 sentences → stop and rescope |
| 3–5 (Oct 13–Nov 2) | Single-period, then full-year dispatch, France 2019 | Validation metrics pre-registered before running |
| 6–8 (Nov 3–Nov 23) | Hydro budgets, pumped storage, interconnection | **~Nov 16 interconnection gate** (see above) |
| 9–11 (Nov 24–Dec 14) | Shapley engine with tests; LMDI benchmark | Tests: attributions sum exactly to ΔCost |
| 12–14 (Dec 15–Jan 4) | Bootstrap, sensitivity, 2022 and 2024 results | Exams/holidays risk: plan for reduced capacity |
| 15–17 (Jan 5–Jan 25) | Report (~15 pp, IEA register) + polished repo | **~Jan 18: full draft exists AND repo made public**, after this checklist: real README (question, method, one-command reproduction); `LICENSE`; full-history scan for secrets; author email check; licence check on any redistributed data; green CI |
| 18 (Jan 26–Feb 1) | Submit applications | Hard deadline Feb 15 |

**If a gate is missed: cut scope, not quality.** Cut order: MILP stretch → second year pair → (never) the report.

## 7. Repo standards
- Work inside the WSL filesystem (`~/projects`), not `/mnt/c`.
- Layout: `src/`, `tests/`, `notebooks/`, `report/` (LaTeX), `docs/`, `data/` (gitignored; fetch scripts only), `ASSUMPTIONS.md`, `DECISIONS.md`, `PROJECT_STATE.md`, agent instructions file (`AGENTS.md` or `CLAUDE.md`, check which file the chosen tool reads).
- Python env pinned in `pyproject.toml`: pyomo, highspy, pandas, numpy, matplotlib, scipy, pytest, ruff.
- GitHub: SSH auth from WSL, private repo initially, GitHub Actions CI running `ruff` and `pytest` on every push and PR.
- One Issue per task, one branch per issue; merge only if tests pass **and** owner can explain the diff.
- Commit several times a week; history is evidence of sustained work.
- Before writing real model code: move to `pyproject.toml` and pin dependency versions (an unpinned pyomo/highspy update can silently change solver behaviour).
- `PROJECT_STATE.md` is committed to the repo and kept identical to the copy Claude works from.
- Never commit secrets, tokens or `.env`; deleting them later does not remove them from history. Keep the commit author email one you are happy to make public (GitHub noreply address if not).
- Mandatory tests from week 1, including: "LP dual of the demand constraint equals the marginal unit's cost"; "Shapley attributions sum exactly to ΔCost".

## 8. AI-use rules
1. Derive by hand first; AI checks and assists.
2. Tests come from the mathematics, not from the code under test.
3. Any line the owner cannot explain does not merge.
4. Keep an honest record of how AI was used, and be ready to explain it in an interview.
5. Local models (R1 distills, Qwen Coder) are juniors: verify everything, especially proofs.

## 9. Reading list
- Boyd & Vandenberghe, *Convex Optimization*, ch. 5 (duality).
- Wolsey, *Integer Programming*, ch. 1–2 (only for the MILP stretch).
- Ang's papers on LMDI.
- IEA Energy Efficiency reports (framing and vocabulary); methodology annexes of recent IEA outlooks.
- Wood, Wollenberg & Sheblé, *Power Generation, Operation, and Control* (UC formulations, stretch only).

## 10. Unverified / to check
- Novelty of the Shapley-on-LP-dispatch attribution (literature search).
- éCO2mix granularity and coverage; data licences for all sources.
- Whether `dsh` can use a local LM Studio endpoint; what `dsh` actually is beyond third-party descriptions; its `0.2.0-rc.2` release-candidate stability.
- ~~Whether `.gitignore` exists~~ **Resolved:** it exists and covers `.venv/`, `.env`, `data/`, `__pycache__/`, `*.pyc`, `.ipynb_checkpoints/` (seen in the synced repo).
- Whether `.venv/` ever got committed: the synced snapshot shows only 4 files, which looks clean, but the sync may filter. Confirm with `git ls-files | grep venv` (must print nothing).
- ~~Repo visibility~~ **Resolved:** private, connected via the GitHub App.
- Dependencies in `requirements.txt` are unpinned (todo: `pyproject.toml` + pinned versions).
- Level requirements of specific IEA postings (Master's vs. undergraduate).
- *Convention de stage* process at Paris-Saclay.

## 11. Current status
**Done**
- Project chosen and scoped; tooling plan agreed (D1–D5).
- Repo skeleton created and pushed: `requirements.txt`, `.gitignore`, `tests/test_smoke.py`, `.github/workflows/ci.yml`. **CI green** on GitHub Actions (ruff + pytest, Python 3.12), reported by owner. Local `ruff check .` and `pytest` also pass. Contents reviewed by Claude via the synced repo: fine for this stage.
- Repo connected to the Claude Project. **Setup phase is over: nothing left to configure.**
- 3-generator problem solved by hand (G1: 100 MW, 10 €/MWh; G2: 50 MW, 50 €/MWh; G3: 50 MW, 100 €/MWh; demand 120 MW): dispatch 100 / 20 / 0 MW, marginal unit G2, price 50 €/MWh, total cost 2,000 €/h. Numbers verified by Claude. The derivation itself was **not shown**, and the capacity-bound multipliers were not reported.

**Open deliverables**

| Deliverable | Due |
|---|---|
| Checkpoint: photo of KKT steps 1–3 (general n-generator problem with every inequality as h(g) ≤ 0 and its own multiplier; Lagrangian + stationarity; three-state analysis gᵢ = 0 / 0 < gᵢ < Gᵢ / gᵢ = Gᵢ), even if wrong | **Thu Oct 1** |
| Full KKT write-up: steps 1–3 + complementary slackness and dual feasibility + numbers plugged in (full multiplier vector) + strong-duality check (dual objective = 2,000) | **Tue Oct 6** |
| Probes A (d = 100, degeneracy), B (G1 capacity 100 → 90, predict via multipliers then re-solve), C (G1 capacity → 60, explain prediction vs true change) | **Tue Oct 6** |
| Pyomo + HiGHS model returning duals of the balance constraint **and** capacity bounds; `tests/test_three_generator.py` asserting the *hand-computed* values; on a branch (e.g. `docs/kkt-derivation`), never on `main` | **Tue Oct 6** |
| Housekeeping on that branch: commit `PROJECT_STATE.md`; run `git ls-files \| grep venv` | with the branch |
| Three-sentence contribution statement | **Fri Oct 9** |
| Literature search on novelty | by Mon Oct 12 |
| Coding-agent decision | after Oct 6 |

**Blockers:** none. Setup excuses are no longer available.

## 12. Session protocol (for Claude in this Project)
- Start: read this file, state in two lines where the project stands, then push on the next action.
- Role: design reviewer and red team. Critique derivations, code and drafts bluntly; do not validate weak work; flag overclaims.
- Do not write the owner's derivations for them. Check them.
- This Project uses one long working thread. If answers start drifting or forgetting decisions, open a fresh chat in the Project; this file carries continuity, not the thread.
- The owner presses **Sync** on the GitHub source before each session; Claude flags when the snapshot looks stale.
- End of session: output the exact updated sections of this file (status, decisions, open questions, unverified items) for the owner to paste in.
- Never assert something about the owner's machine or repo that has not been shown in the conversation.
- The owner tends to report results without the working. Always ask for the derivation, the raw terminal output or the failing log, and do not accept a summary in its place.
- Work happens on branches; CI must be green before anything merges to `main`.

---

## 13. Change log
- 2026-09-29: initial version.
- 2026-09-29: repo skeleton and CI recorded; 3-generator result recorded; `dsh` status and agent-decision deferral added; open deliverables with due dates added; unverified items extended.
- 2026-09-29 23:15: repo connected to the Project and reviewed; `.gitignore` and visibility items resolved; Jan 18 public-repo gate with checklist added; repo-hygiene standards added; Thu Oct 1 checkpoint added; session protocol updated for the single-thread Project.

## Open Decisions
- **Degenerate Hours:** LP solvers return an arbitrary shadow price within $[\partial^-C, \partial^+C]$ during degenerate intervals. We will implement a rule to report both one-sided derivatives by re-solving at $D \pm \varepsilon$.
