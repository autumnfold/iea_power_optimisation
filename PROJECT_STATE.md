# PROJECT_STATE.md

> Canonical source of truth for project status, decisions, open questions, and change history. Last reconciled: 2026-11-06 (direction change to domestic adequacy, D15).
> Evidence labels matter: distinguish local verification, Git history, reports from Browser Claude, and unresolved claims.
> **Working protocol:** follow the role-specific instructions in Section 12 before starting work.

---

## 1. Goal

Land a summer internship at the **International Energy Agency (IEA, Paris)** next summer (summer 2027), by producing a serious, rigorous, **finished**, public project that shows quantitative modelling skill and clear writing. The project does not need to be a new contribution to research (D13).

**Application facts (IEA official internship page, checked 2026-09-29 according to the recorded search; re-check before applying):**
- Be enrolled in a full-time degree programme for the duration of the internship in a field or discipline related to the work of the IEA.
- Excellent command of English and/or French; strong drafting and communication skills; minimum internship length one month.
- Applications are year-round via the OECD internship platform. Apply at least 3 months before the desired start date. Select IEA as one of the 3 areas of interest. The "Message to hiring manager" field works as the cover letter: state interest in the IEA, the type of role and the area of work.
- At least one individual IEA posting (third-party posting dated 2023, reported by Browser Claude on 2026-10-14) required Master's/PhD enrolment. Do not generalise this to every internship: **check the education-level requirement of every posting before applying.**
- **Target: application submitted by ~Feb 1, 2027. Hard planning deadline: Feb 15, 2027.**
- To do: ask the Paris-Saclay department about the *convention de stage* process.

## 2. Owner profile

- L2 Mathematics, Université Paris-Saclay (France).
- Very good in Python; comfortable in C++; learning LaTeX; loves math and CS.
- Environment: Windows + WSL Ubuntu, VS Code, GitHub account (knows Git), LM Studio with DeepSeek R1 and Qwen Coder. A recent DeepSeek Harness (`dsh`) is available but currently unused; whether to drop it is undecided.
- Still building experience with professional project tooling (CI, repo structure, agent workflows). Wants to become as professional as possible.
- **Working style:** wants demanding, direct coaching. Do not go easy. Strong pushes, hard gates, blunt critique.
- **Hardest parts so far (owner, 2026-11-01):** reading research papers, and the amount of new mathematics to learn. Plan around this: prefer readable institutional reports over academic papers, and reuse mathematics already done.

## 3. The project

**Research question (owner, 2026-11-06):** *Why did France's domestic electricity supply struggle to meet demand in 2022 compared with 2019, and to what extent can the change be attributed to conventional generation availability versus demand and resource conditions?*

**Working title:** to be chosen by the owner. *Proposed (Browser Claude):* "Domestic electricity adequacy in France, 2019 vs 2022: an exact two-driver attribution".

**History:**
- The original hybrid project was rescoped on 2026-11-01 (D12) to a 3-driver attribution of variable cost.
- On 2026-11-06, the first adequacy check showed that a closed French system cannot meet all 2022 demand in some hours. A closed-system cost attribution would therefore depend on pricing unmet energy, and no defensible price exists. The owner made domestic adequacy the primary objective (D15) and moved cost attribution to a secondary objective (D21).
- Superseded designs are kept in Git history and in `docs/check_protocol_v6.md`.

### Method

**Direction approved by owner, 2026-11-06. The detailed implementation plan is Proposed until the owner approves it.**

1. **Closed system (D20):** only domestic generation serves French demand. International exchanges are excluded from all scenarios. Observed exchanges are used only for validation and for comparison with the implied import requirement (D18).
2. **Net demand, 30-minute step (driver D):**
   $$N_t = C_t - W_t - S_t - R_t - B_t - H^{\text{PS}}_t$$
   - $R_t$ is run-of-river and daily pondage;
   - $B_t$ is bioenergy;
   - $H^{\text{PS}}_t$ is the **observed net pumped-storage profile** (`hydraulique_step_turbinage` + `pompage`, where `pompage` ≤ 0), which is the baseline (D19).
3. **Lakes (driver D):** the monthly observed energy budget, dispatched flexibly within each month up to the lake capacity. This is a proxy for available monthly energy, with no shifting between months (see `docs/check_protocol_v6.md`, section 5.2).
4. **Conventional generation availability (driver A):** nuclear plus fossil available capacity, per month. The two are **grouped**, and their combined contribution must **not** be read as the isolated effect of nuclear availability (D16).
5. **Monthly load-duration curves.** Availability uses the monthly mean as baseline, with the lowest daily mean as a conservative stress test.
6. **Metrics (D17):** annual unmet energy (GWh/TWh) and peak shortfall (MW/GW). 2019 is **not** assumed to have zero unmet energy before the results are checked.
7. **Two drivers, four scenarios** (2019/2022 × 2019/2022), with an exact two-player Shapley attribution. The interaction term is reported explicitly.
8. **Imports (D18):** the model estimates the **domestic adequacy gap and the implied import requirement under its assumptions**. It does not establish how much of France's historical imports were strictly necessary for security rather than economic reasons.
9. **Pumped storage (D19):** the observed net profile is the baseline. Flexible generation (observed pumping, monthly generation budget placed freely) is an adequacy sensitivity. The limitations of both are documented.
10. **Checks (D20):** physical-consistency checks (balance closure; availability at least observed generation; hydro capacities at least observed output) replace the chronological Test A. Test B (the 36 GWh tolerance for modelled 2019) applies exactly as pre-registered in `docs/check_protocol_v6.md`, section 8.3.
11. **Secondary objective (D21):** variable-cost attribution, to be started only after the adequacy results are judged robust and defensible.
12. **Deliverable:** a **two-page research note** plus the repository. A longer report is optional.

### Mathematics

**Already done:** LP formulation, KKT, duality, convexity of the value function, the two-driver Shapley example with its interaction term (owner's write-up v3, Oct 6). The toy-model results are asserted by the repository tests.

**New, deliberately small:**
- the load-duration curve;
- placing a limited monthly energy budget against the highest deficits (water-filling);
- the two-player Shapley value applied to adequacy metrics.

The cost LP of the secondary objective reuses the existing toy model.

### Contribution
A clear, reproducible answer to a concrete, policy-relevant question (electricity security, the role of interconnection), from a model the owner can fully explain and defend. Novelty is **not** required (D13). Never overclaim in the application or the note.

## 4. Data sources (verify licence terms for each)

- **RTE éCO2mix, national consolidated and definitive data** (ODRÉ / data.gouv.fr): <https://odre.opendatasoft.com/explore/dataset/eco2mix-national-cons-def/>. Licence Ouverte / Open Licence 2.0 (data.gouv.fr page, read by Browser Claude 2026-11-01).
  - **Check 1 results** (owner's run of `check_eco2mix.py`, 2026-11-06; JSON read by Browser Claude):
    - 30-minute step, 17,520 rows per year, no missing values;
    - `pompage` ≤ 0 (−4,036 to −3 MW); `ech_physiques` is import-positive;
    - the balance $C_t = \sum_k P_{k,t} + \text{pompage}_t + \text{ech}_t$ closes with mean absolute residual 0.7 MW (2019) and 66 MW (2022, unresolved).
  - Annual generation totals match RTE within about 0.5 TWh.
  - Consumption is about 2.5 TWh below RTE's totals in both years. Trade differs by 1.7–2.8 TWh. *Hypotheses:* perimeter (Corsica), and physical vs commercial exchanges.
- **Conventional availability:** an ENTSO-E unit-unavailability reconstruction (method in `docs/check_protocol_v6.md`, section 6), **time-boxed to 2 sessions**. Fallback: monthly brackets (nuclear between the monthly mean and the monthly maximum of observed generation; fossil between the observed maximum and sourced installed capacity).
- **Installed capacities, 2019 and 2022:** lakes, pumped storage (pumping and generating), fossil by technology. Source: RTE annual reports ("parc installé") or ENTSO-E installed capacity by production type. Owner task.
- **Secondary objective only:**
  - World Bank Pink Sheet monthly prices (natural gas Europe, coal, Brent), CC BY 4.0;
  - carbon price source TBD;
  - USD→EUR source TBD;
  - technology costs and efficiencies in `ASSUMPTIONS.md`.

## 5. Decisions

| # | Decision | Status / evidence |
|---|---|---|
| D1 | ~~Hybrid project: dispatch, attribution, and LMDI benchmark~~ → single question: merit-order LP with 3-driver Shapley attribution, 2019 vs 2022 | Narrowed by owner, 2026-11-01 (D12). LMDI benchmark dropped. Primary question replaced on 2026-11-06 (D15). |
| D2 | ~~Unit commitment (MILP) is a stretch~~ → not built; listed as future work | Superseded by D12, 2026-11-01 |
| D3 | Minimal AI tooling: one terminal coding agent, chat as reviewer/red team, local models as junior helpers; no multi-agent orchestration | Decided by owner |
| D4 | Agents work on feature branches; owner performs all Git merges (see D10 for the 2026-11-01 exception on commits/pushes) | Decided by owner |
| D5 | Owner derives mathematics by hand first; AI may explain, hint, check reasoning, and locate errors, but must not write report derivations/proofs | Decided by owner |
| D6 | ~~Interconnection: net imports enter as a fixed observed profile inside residual demand~~; price-taking neighbours (option B) dropped | Resolved by owner 2026-11-01; **superseded by D20 (2026-11-06):** closed system, exchanges excluded from all scenarios |
| D7 | Claude Code is the primary implementation tool; local rules and deny patterns are configured | Deny patterns are configured in `.claude/settings.json`. Commit `6c2a483` added the history-writing deny rules (`merge`, `rebase`, `reset`, `revert`, `cherry-pick`, `tag`, `branch -d`/`-D`) and the updated `CLAUDE.md`; it was merged through PR #4 at `ef72b3c` (verified in local Git history by Claude Code, 2026-10-14). `dsh` is currently unused; dropping it is undecided. |
| D8 | ~~Degenerate hours: report one-sided demand-cost derivatives~~ | Superseded by D12, 2026-11-01: the project attributes costs, not prices |
| D9 | Explicit nonnegativity constraints in the toy model so lower-bound multipliers are available for KKT tests | Implemented in `src/dispatch.py`; tests assert the lower-bound multiplier. Revisit when scaling the model. |
| D10 | Role split: owner decides and merges; Claude Code implements/tests and maintains status; Browser Claude advises/reviews | Decided by owner, 2026-10-14. **Amended by owner, 2026-11-01:** Browser Claude is authorised to make repository changes; it commits and pushes to a feature branch and opens a PR, and never merges. |
| D11 | No separate `DECISIONS.md`; this file is the canonical status and decision record | Decided by owner |
| D12 | **Rescope:** load-duration-curve merit-order model, 3 drivers ($2^3 = 8$ runs), one year pair (2019→2022), sensitivity analysis instead of bootstrap, 8–10 page report | Approved by owner, 2026-11-01. **Partly superseded on 2026-11-06:** the 3-driver cost attribution becomes the secondary objective (D21); the primary question is adequacy (D15); the deliverable becomes a two-page note. |
| D13 | Novelty is not required; the contribution is a clear, correct, finished answer to a real question. The literature-based novelty gate is removed. | Approved by owner, 2026-11-01 |
| D14 | Working rule: no task longer than about 2 hours; each ends with a commit. A task untouched for 3 days is cut smaller and reported to Browser Claude, not postponed. | Approved by owner, 2026-11-01 |
| D15 | **Primary objective: domestic electricity adequacy**, with the research question of Section 3 | Decided by owner, 2026-11-06 |
| D16 | Two drivers: D = demand and resource conditions (consumption, wind, solar, run-of-river, bioenergy, pumped-storage profile, lake budgets); A = conventional generation availability (nuclear and fossil, **grouped**). A's contribution must not be interpreted as the isolated effect of nuclear availability. | Decided by owner, 2026-11-06 |
| D17 | Metrics: annual unmet energy and peak shortfall; 2019 is not assumed to be zero before checking | Decided by owner, 2026-11-06 |
| D18 | Wording on imports: the model estimates the domestic adequacy gap and the implied import requirement under its assumptions; it does not establish how much of historical imports were strictly necessary for security | Decided by owner, 2026-11-06 |
| D19 | Pumped storage: the observed net profile is the baseline; flexible generation is an adequacy sensitivity; both representations' limitations are documented | Decided by owner, 2026-11-06 |
| D20 | **Methodology basis:** closed system (scope B2); net demand definition; monthly load-duration curves; hydro separation; ENTSO-E reconstruction approach; Test B 36 GWh pre-registered (approved by owner through methodology notes v1–v6, 2026-11-06). **v6 is frozen** as `docs/check_protocol_v6.md`. Its section 8.1 (chronological LP, storage envelope, two-stage Test A) and the $r_m$ diagnostic are **removed from the core protocol**; Test A is replaced by physical-consistency checks. No further revisions unless an implementation or data issue requires one. | Decided by owner, 2026-11-06 |
| D21 | Variable-cost attribution is a **secondary objective**, not abandoned; it starts only after the adequacy results are judged robust | Decided by owner, 2026-11-06 |
| D22 | Literature reduced to four institutional sources, including RTE's winter 2022–23 security-of-supply analysis | Decided by owner, 2026-11-06 |
| D23 | Browser Claude leads the adequacy pipeline and its tests, on a feature branch through a PR; the owner runs it on the real data, reviews every line and merges | Decided by owner, 2026-11-06 (extends D10) |

**Open decisions and questions**
- **Adequacy implementation plan:** Proposed by Browser Claude on 2026-11-06, awaiting owner approval before implementation.
- Availability source: ENTSO-E reconstruction or the fallback brackets (after the time-boxed attempt).
- Lake capacity: installed value (to source) or the observed monthly maximum.
- *Proposed (Browser Claude, 2026-11-06), owner to decide:*
  - broaden internship targets beyond the IEA (for example EDF Lab Paris-Saclay, RTE R&D, Paris-Saclay or CentraleSupélec labs, analysis organisations such as Ember);
  - check the IEA's current education-level requirements;
  - ask one Paris-Saclay optimisation or operations-research lecturer to review the work once.
- Secondary objective only: technology grouping, carbon and exchange-rate sources, treatment of unmet energy in a cost attribution.
- *Resolved 2026-11-06:* one load-duration curve per month (D20); the nuclear availability source follows D20 (ENTSO-E or fallback).
- November examination dates are needed to adjust the schedule.
- Ask the Paris-Saclay department about the *convention de stage* process.
- Check the enrolment-level requirement for every IEA posting before applying.
- `dsh`: decide whether to retain or remove it; do not silently treat it as dropped.
- *Resolved 2026-11-01 (D12):* year pairs (2019→2022 only); driver list (3 drivers); Nov 29 interconnection gate (option B dropped).

Repository: `https://github.com/autumnfold/iea_power_optimisation`. GitHub username changed from `jiuyueqiuu` to `autumnfold`, **reported by owner on 2026-10-29**; new URL verified by Claude Code via clone on 2026-10-29. Local Git history contains the PR #2, PR #3, and PR #4 merge commits. Repository visibility: **public, reported by owner on 2026-09-29**.

## 6. Timeline (rebuilt 2026-11-06 after D15; November exam dates still TBD)

| By | Deliverable | Notes |
|---|---|---|
| Sep 29–Oct 13 | Repository, CI, three-generator dispatch/KKT model and tests | Done (PR #2, #3) |
| Nov 6 | Check 1 (balance, sign conventions, first adequacy brackets); methodology notes v1–v6; direction change (D15) | Done |
| **Nov 7–22** | Installed capacities found; ENTSO-E attempt (≤ 2 sessions) or fallback; adequacy pipeline PR (Browser Claude) reviewed and run on real data; 2 of the 4 institutional sources read | Exams may fall here |
| **Nov 23–Dec 6** | **Headline result:** four scenarios, two-driver Shapley with interaction, ranges across variants, one figure; physical-consistency report; Test B | |
| Dec 7–20 | Secondary objective (cost layer), **only if** the adequacy results are judged robust | |
| Dec 21–Jan 10 | Two-page research note; README | Holidays |
| Jan 10–Feb 1 | Outreach and applications | Hard planning deadline Feb 15 |

**History:** the Oct 22 gate was moved to Oct 25, then Nov 1 (owner); on Nov 1 the owner rescoped (D12); on Nov 6 the owner changed the primary objective (D15).

**If a step slips:** apply D14 first. Cut order: the secondary objective (cost layer) → availability sensitivity reduced to the fallback brackets → never the two-page note.

## 7. Repo standards

- Work inside the WSL filesystem (`~/projects`), not `/mnt/c`.
- Tracked layout (verified by Browser Claude on 2026-11-06 at `80a8a44`): `.claude/settings.json`, `.github/workflows/ci.yml`, `.gitignore`, `CLAUDE.md`, `PROJECT_STATE.md`, `pytest.ini`, `requirements.txt`, `docs/literature.md`, `docs/data_feasibility.md`, `src/`, `tests/`. The direction PR adds `docs/check_protocol_v6.md` (frozen, D20).
- `check_eco2mix.py` (check 1) currently lives outside the repository; the adequacy pipeline will absorb its loading and sign-convention logic, with tests.
- `README.md`, `ASSUMPTIONS.md`, and `report/` are still missing. Create them when their purposes are reached. `DECISIONS.md` is intentionally not used.
- `data/` must remain untracked and must never be modified by an agent without explicit owner direction.
- Current dependency pins in `requirements.txt`: `pyomo==6.8.0`, `highspy==1.7.2`, `pytest==9.1.1`, `ruff==0.1.6`. The CI workflow installs this file, then runs `ruff check .` and `pytest` on Python 3.12. Add `pandas` (pinned) when data loading starts.
- Recorded local verification on 2026-10-14: Ruff 0.1.6 (the pinned CI version) passed; `.venv/bin/pytest` reported 8 passed; `git diff --check` passed. The locally installed Ruff 0.16.9 reports an import-formatting finding that does not reproduce under Ruff 0.1.6. Keep the version distinction explicit; do not claim that the two Ruff versions behave identically.
- `.venv/` is not in the current `git ls-files` output; no tracked virtual environment was found.
- **Git merges are owner-only.** Claude Code must not commit, push, merge, rebase, reset, revert, cherry-pick, tag, or rewrite Git history, even if asked to do so in a task-level instruction. **Exception (owner, 2026-11-01, D10):** Browser Claude may commit and push to a feature branch and open a PR; it never merges and never rewrites history.
- Agents must not switch branches or discard working-tree changes without explicit owner approval.
- Inspection commands include `git status`, `git diff`, `git log`, `git show`, and branch-listing commands. `git fetch` is allowed without separate approval to refresh remote-tracking references; it can update those references but does not itself commit, push, merge, or rewrite Git history.
- Start task branches from an up-to-date `main` when the owner has confirmed the relevant refs; never assume a feature branch's ancestry or contents based only on its name.
- Never commit secrets, tokens, `.env`, or data whose licence does not permit redistribution.
- Any code or behaviour change needs appropriate tests. Run the pinned Ruff check and pytest when applicable; report actual output honestly.
- Explain every non-obvious line so the owner can defend the implementation in an interview.
- `PROJECT_STATE.md` is the canonical project status and decision document. Browser Claude reads it from the synced repository; do not maintain a separate competing copy.

## 8. AI-use rules

1. The owner derives mathematical arguments by hand first. AI may explain concepts, provide hints, check the owner's reasoning, and locate errors; AI must not write derivations or proofs intended for the owner's report.
2. Tests should arise from mathematical reasoning and independent expected behaviour, not merely duplicate the implementation under test.
3. Any line the owner cannot explain does not merge.
4. Keep an honest record of how AI was used, and be ready to explain it in an interview.
5. Local models (R1 distills, Qwen Coder) are junior helpers: verify everything, especially proofs.
6. Browser Claude may find and suggest sources; the owner reads the sections cited in the report.

## 9. Reading list (since 2026-11-06, D22)

Four institutional sources; links and reading method in `docs/literature.md`:
1. RTE, *Bilan électrique 2022*;
2. RTE, *Perspectives pour le système électrique pour l'automne et l'hiver 2022-2023* (September 2022), with its updates and the *Bilan de l'hiver 2022-2023* (March 2023);
3. IEA, *Electricity Market Report 2023*;
4. CRE, wholesale-market monitoring report for 2022.

*Optional method references:* Molnar (Shapley values); Kirschen & Strbac (merit order, load-duration curves); Ambec & Crampes (TSE). *Background only:* Boyd & Vandenberghe ch. 5; Wolsey; Ang (LMDI); Wood, Wollenberg & Sheblé.

## 10. Unverified / to check

- **Data:**
  - the 66 MW systematic balance residual in 2022 (candidate: a battery column not read);
  - the 2 duplicate timestamps per year;
  - the ~2.5 TWh consumption gap and the trade gap against RTE (hypotheses only);
  - availability data (ENTSO-E fields, thresholds, licence);
  - installed capacities;
  - curtailment assumed negligible (not verified).
- **Literature:** RTE's winter 2022–23 analyses located by search on 2026-11-06; their contents have not been read.
- **IEA applications:** re-check current official eligibility guidance and the education-level requirement for each posting; ask Paris-Saclay about the *convention de stage* process.
- **GitHub CI:** GitHub Actions status has not been independently checked by Claude Code or Browser Claude for any PR; the owner reports it.
- **KKT write-up:** v3 exists as PDFs shared in chat (Oct 6); it is not in the repository. Small fixes for the appendix (Jan): "mathematically necessary" → conditional uniqueness; convexity-proof feasibility clause; $(\lambda, -\bar\mu)$ sign convention; slope vs shadow price.
- **Repository hygiene:** `README.md`, `ASSUMPTIONS.md`, and `report/` are missing. Dependency pins exist in `requirements.txt`; a migration to `pyproject.toml` has not been performed.
- **November examination dates:** not yet supplied.
- **Adequacy pipeline:** not yet implemented (plan Proposed, 2026-11-06).
- **Adequacy results:** the first brackets (check 1) used pessimistic fossil capacity and a fixed or unconstrained hydro treatment; they are exploratory, not results.
- **Test design:** `tests/test_three_generator.py::test_raw_pyomo_duals` builds a separate Pyomo model rather than exercising `solve_dispatch()`; it tests raw solver dual signs, but does not independently test the production function's dual extraction. Improve this when scaling the model.
- **Branch cleanup:** on 2026-10-14, after `git fetch origin`, with `main` and `origin/main` both at `ef72b3c` (verified by Claude Code):
  - `git branch -r --merged origin/main` listed `origin/chore/claude-code-config`, `origin/chore/workflow`, `origin/main`, and `origin/model/three-generator-kkt`.
  - `git branch --merged main` listed `chore/workflow`, `docs/state-pr4`, `main`, and `model/three-generator-kkt`. `docs/state-pr4` appears because it pointed at the same commit as `main` when listed.
  - There is no local `chore/claude-code-config` branch.
  - These listings only show merge status. The owner decides any branch deletion.
- **Numerical results from the write-up:** results not asserted by repository tests (including any Shapley split, first-order total, or convexity-gap figure) remain unverified until reproduced from code or independently checked calculations.
- **CI/tooling follow-up:** align local and pinned Ruff versions or document the reason for using the pinned version. Do not infer a CI result from local tests.
- **Local Git remote after the username change:** the owner's local `origin` may still point to `jiuyueqiuu/iea_power_optimisation`. GitHub redirects renamed accounts' repositories for now, but the owner should run `git remote set-url origin https://github.com/autumnfold/iea_power_optimisation`. Not verified.
- *Superseded on 2026-11-01 (D12, D13):* research novelty check; weather-data checks; one-sided derivatives at degenerate demand points; LMDI and bootstrap results; pre-registration of price-based validation metrics.
- *Superseded on 2026-11-06 (D20):* the chronological Test A, the storage envelope and the $r_m$ diagnostic (`docs/check_protocol_v6.md`, section 8.1).

## 11. Current status

Evidence labels:
- **Verified locally:** observed directly in dated WSL command output or a recorded command result.
- **Verified in Git history:** supported by locally available commit history.
- **Asserted by test code:** the source contains an assertion for the result; this is distinct from a recorded test run.
- **Verified by Browser Claude:** observed by Browser Claude in its own clone of the public repository, with the date.
- **Reported by owner:** stated by the owner in chat.
- **Unverified:** evidence is not currently available.

**Reported by owner on 2026-11-06**
- Ran `check_eco2mix.py` on the éCO2mix national definitive data for 2019 and 2022 and supplied `eco2mix_checks.json`.
- Approved, through methodology notes v1–v6, the closed-system basis and the check protocol (D20); then the direction change to domestic adequacy (D15–D23).

**Check 1 results** (from the owner's JSON, read by Browser Claude on 2026-11-06)
- Sign conventions and balance closure: see Section 4.
- Net demand (with net hydro subtracted) and 2019 net exports, as computed: 361.8 TWh net demand and a net export of 58.5 TWh in 2019; 341.0 TWh net demand and a net import of 14.8 TWh in 2022.
- Exploratory adequacy brackets (fossil capacity = highest observed output, so pessimistic):
  - 2022 unmet energy between 0.11 and 2.6 TWh (peak 7.1–12.2 GW);
  - 2019 unmet energy between 0.004 and 0.43 TWh (peak 1.8–7.0 GW).
  - These are not results: capacities and the hydro treatment were provisional.

**Reported by owner on 2026-11-01**
- The original project was too big and too hard; the owner approved the rescope (D12), dropped the novelty requirement (D13) and adopted the 2-hour task rule (D14).
- The hardest parts were reading papers and the amount of new mathematics.
- The owner authorised Browser Claude to make repository changes (D10 amendment).

**Verified by Browser Claude on 2026-11-01** (after `git fetch origin`)
- `origin/main` at `1b70363` (`Merge pull request #6 from autumnfold/docs/github-username`).
- No commits on any branch between `e6592e3` (PR #5, Oct 15) and `9a560bf` (Oct 29, username change).

**Verified locally on 2026-10-14**
- After activating `.venv`, `pytest` collected 8 tests; all 8 passed in 0.52 seconds.
- `ruff check .` passed using pinned Ruff 0.1.6. Ruff 0.16.9 previously reported an `I001` import-formatting finding that did not reproduce under the pinned version.
- `python3 -m json.tool .claude/settings.json` succeeded.
- `git diff --check` produced no output.
- `CLAUDE.md` was verified to end with a newline.

**Asserted by source and test code inspected on 2026-10-14**
- `src/dispatch.py` explicitly negates the raw duals for both upper and lower capacity constraints and checks that the solver termination condition is optimal before loading the solution.
- The baseline test asserts total cost 2000, dispatch `(100, 20, 0)`, `lambda = 50`, `mu_max[G1] = 40`, `mu_min[G3] = 50`, and strong duality.
- Probe A asserts that the returned lambda lies in `[10, 50]` and that HiGHS currently returns the left endpoint, 10.
- Probe B asserts total cost 2400 at G1 capacity 90; Probe C asserts 4100 at capacity 60; the infeasibility test expects an exception when G1 capacity is 10.
- The Shapley-corner test asserts costs 2000, 2500, 3200, and 4200 for the four combinations shown in that test.
- `test_raw_pyomo_duals` separately constructs a model to assert raw dual signs; it does not test extraction through `solve_dispatch()`.

**Verified in local Git history**
- PR #2 merge commit: `bffcef8` (`Merge pull request #2 from jiuyueqiuu/chore/claude-code-config`).
- PR #3 merge commit: `b57fbf2` (`Merge pull request #3 from jiuyueqiuu/model/three-generator-kkt`).
- PR #3 merge changes include `PROJECT_STATE.md`, `requirements.txt`, `src/dispatch.py`, and `tests/test_three_generator.py`.
- Historical (before PR #4): in the earlier reconciliation, `HEAD`, `main`, and `origin/main` were reported at `b57fbf2`.
- PR #4 merge commit: `ef72b3c` (`Merge pull request #4 from jiuyueqiuu/chore/workflow`), with parents `b57fbf2` and `6c2a483`; it changed exactly `.claude/settings.json`, `CLAUDE.md`, and `PROJECT_STATE.md` (verified by Claude Code on 2026-10-14).
- PR #5 merge commit: `e6592e3` (Oct 15); PR #6 merge commit: `1b70363` (Oct 29) (verified by Browser Claude, 2026-11-01).

**Open deliverables**

| Deliverable | Owner | Due |
|---|---|---|
| Approve (or amend) the adequacy implementation plan | Owner | Before implementation |
| Adequacy pipeline and tests, PR | Browser Claude | After plan approval |
| Installed capacities (lakes, pumped storage, fossil by technology; 2019, 2022) | Owner | Nov 22 |
| ENTSO-E attempt (≤ 2 sessions) or decision to use the fallback | Owner | Nov 22 |
| 2 of the 4 institutional sources read and recorded | Owner | Nov 22 |
| Headline adequacy result, figure, Test B, physical-consistency report | Both | Dec 6 |
| Two-page research note | Owner (Browser Claude reviews) | Jan 10 |
| November exam dates | Owner | As soon as known |

*Superseded on 2026-11-06:* the Nov 7 data-check deliverable (done through check 1), the Nov 15 five-source literature target (replaced by D22), and the cost-model milestones of D12 (moved to the secondary objective, D21).

**Current blockers:** none technical. The schedule depends on the November exam dates.

## 12. Session protocol and roles

### Owner
- Makes project, scope, deadline, and methodology decisions.
- Derives mathematical arguments and proofs intended for the report.
- Performs all merges, and all other Git writes except the Browser Claude branch/PR exception (D10).
- Confirms proposed dates and unresolved choices. Reviews diffs before deciding whether to apply changes. Reports each PR number and CI status to Browser Claude, and reports any moved deadline before the date.
- Keeps tasks to about 2 hours, each ending in a commit; reports any task untouched for 3 days (D14).

### Claude Code
- Reads this file before each task and briefly states current status and the next concrete action.
- Implements and tests approved code/documentation changes on a feature branch; does not perform Git writes.
- Must not switch branches or discard changes without explicit owner approval.
- At the end of a meaningful task, updates Sections 10 (unverified items), 11 (status/deliverables), and 13 (change log) itself, using dated evidence. It must not silently change project decisions in Sections 1, 3, 5, or 6; propose material changes for owner confirmation.
- Gives a concise handoff in chat: changed files, exact checks and results, unverified items, and owner decisions needed.
- Never claims to have inspected a live repository, machine, CI run, or browser state unless evidence was supplied. Ask for raw terminal output or logs when needed.

### Browser Claude
- Advises, researches, reviews pull requests, and audits this file against the repository.
- Since 2026-11-01 (D10 amendment): may commit and push to a feature branch and open a PR when the owner asks; never merges, never rewrites history, never pushes to `main`.
- Since 2026-11-06 (D23): leads the adequacy pipeline and its tests; takes a more active role in shaping the project, and brings any change of project direction to the owner for decision.
- Finds readable sources for the owner (Section 2: paper reading is the hardest part).
- Does not maintain a separate canonical status copy.
- Distinguishes observed GitHub evidence from statements reported by the owner or another assistant.

### Shared rules
- The owner derives mathematical arguments by hand first. AI may explain concepts, provide hints, check the owner's reasoning, and locate errors; AI must not write derivations or proofs intended for the owner's report.
- Agents may not merge, rebase, reset, revert, cherry-pick, tag, rewrite Git history, or delete branches. Only Browser Claude may commit and push, and only to a feature branch (D10).
- Distinguish local implementation, local verification, commits, remote pushes, merges, and CI results. Identify whether each fact was verified locally, observed in Git history, asserted by supplied tests, or reported by the owner/Browser Claude.
- Ask the owner about priorities, deadlines, project direction, and genuinely ambiguous decisions. Record proposals as **Proposed** rather than silently deciding.
- Keep this file canonical. Do not create duplicate project-status or decision logs. `ASSUMPTIONS.md` is reserved for numerical assumptions and their sources.

## 13. Change log

- 2026-09-29: initial project-state document; initial repository, scope, and timeline recorded.
- 2026-10-14: reconciliation prepared from local repository evidence and the Browser Claude update supplied by the owner. KKT implementation and merge history are recorded separately from remaining owner learning deliverables. Previously recorded local checks: pinned Ruff 0.1.6 passed, 8 tests passed, and `git diff --check` passed. GitHub Actions status, novelty, data licences, and full-year implementation remain unverified; public visibility was reported by the owner on 2026-09-29.
- 2026-10-14: workflow reconciliation: recorded role split (D10), owner-only Git history writes, owner-authored mathematical derivations, D6 pending owner confirmation, the value-function subgradient correction, evidence labels, the `test_raw_pyomo_duals` testing limitation, and the `dsh` decision as open. October 15 remains proposed; the Oct 17 placeholder was removed.
- 2026-10-14: recorded the PR #4 merge (`ef72b3c`, second parent `6c2a483`; it changed `.claude/settings.json`, `CLAUDE.md`, and `PROJECT_STATE.md`), verified in local Git history by Claude Code after `git fetch origin`. Removed the obsolete claims that `.claude/settings.json` and `CLAUDE.md` were modified and uncommitted. Updated the D7 evidence and the branch-cleanup listings. The GitHub Actions result for PR #4 remains unverified.
- 2026-10-29: recorded the GitHub username change from `jiuyueqiuu` to `autumnfold` (reported by owner). Updated the repository URL in section 5 and verified the new URL by cloning (Claude Code). The PR #2–#4 merge records in section 11 keep their original commit messages, which still name `jiuyueqiuu`. The owner's local remote update is recorded as unverified in section 10.
- 2026-10-22 and 2026-10-25 (recorded retrospectively on 2026-11-01): the owner moved the Oct 22 gate to Oct 25, then to Nov 1.
- 2026-11-01 (Browser Claude, owner-authorised): **rescope.** D12 (load-duration-curve merit-order model, 3 drivers, 2019→2022, sensitivity analysis, 8–10 page report), D13 (novelty not required), D14 (2-hour task rule); D1 narrowed; D2 and D8 superseded; D6 resolved; D10 amended (Browser Claude may push branches and open PRs). Rewrote Sections 1, 3, 4, 6, 9, 10, 11 accordingly; added `docs/literature.md` and `docs/data_feasibility.md`; updated the project description in `CLAUDE.md`.
- 2026-11-06 (Browser Claude, owner-authorised): **direction change to domestic adequacy.** Recorded check 1 results; D15 (adequacy primary), D16 (two drivers, nuclear and fossil grouped), D17 (metrics), D18 (import wording), D19 (pumped storage), D20 (methodology basis, v6 frozen, section 8.1 removed from the core), D21 (cost attribution secondary), D22 (four institutional sources), D23 (Browser Claude leads the pipeline). D1, D6 and D12 annotated as partly superseded. Rewrote Sections 3, 4, 6, 9 and the open deliverables; updated 10 and 11; added `docs/check_protocol_v6.md`; updated the source list in `docs/literature.md`. The adequacy implementation plan is recorded as Proposed.
