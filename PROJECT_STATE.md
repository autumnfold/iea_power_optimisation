# PROJECT_STATE.md

> Canonical source of truth for project status, decisions, open questions, and change history. Last reconciled: 2026-11-01 (rescope, D12).
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

**Working title (since 2026-11-01):** *Why did producing electricity in France cost so much more in 2022 than in 2019? A merit-order model with exact Shapley attribution.*

**Question:** how much of the rise in France's electricity generation cost between 2019 and 2022 came from (1) the change in residual demand, (2) lower nuclear availability, and (3) higher gas and carbon prices?

**Origin:** a merge of two candidate projects (LMDI decomposition + weather normalisation, and a power-system optimisation roadmap). The resulting hybrid (hourly 8,760-hour model, ~6 drivers, weather regression, bootstrap, LMDI benchmark, 2019→2022→2024) was judged too large by the owner on 2026-11-01 and rescoped (D12). The superseded design is kept in Git history (`1b70363` and earlier).

### Method (approved by owner, 2026-11-01)
1. **Model:** the three-generator merit-order LP in `src/dispatch.py`, scaled to roughly 8 technology groups (exact grouping decided after the data check).
2. **Load-duration curve instead of chronological hours:** about 20 demand blocks per year, sorted from highest to lowest. Whether to use one curve per year or one per season/month is open (see Section 5): 2022's nuclear shortfall was concentrated in part of the year.
3. **Residual demand:** demand minus wind, solar, hydro and net imports, all taken as fixed observed profiles. Limitation (to state in the report): these sources do not respond in the counterfactual runs.
4. **Drivers (3):** residual demand; nuclear availability; gas and carbon prices. All $2^3 = 8$ combinations are solved, and the change in cost is split exactly with the 3-player Shapley value.
5. **Uncertainty:** sensitivity analysis instead of a bootstrap. Vary 2–3 cost assumptions by ±20% and check whether the ranking of the drivers holds.
6. **Validation:** modelled annual generation by technology vs éCO2mix actuals; modelled marginal cost vs the annual average wholesale price as a rough sanity check only.
7. **Extension, only if the core is finished by mid-January:** split residual demand into separate drivers (e.g. wind and solar as a 4th driver, $2^4 = 16$ runs).
8. **Report:** 8–10 pages, with the KKT write-up as an appendix.

**Listed as "extensions / future work" in the report, not built:** hourly chronological model, hydro energy budgets, pumped storage, interconnection modelling (price-taking neighbours), weather normalisation, bootstrap, LMDI benchmark, 2024 comparison, MILP unit commitment, emissions attribution.

### Mathematics
**Already done (owner's write-up v3, Oct 6; PDFs shared in chat, not yet in the repo):** LP formulation, KKT conditions and their sufficiency, merit-order theorem, dual problem as optimality certificate, convexity of the LP value function, sensitivity ranging, two-driver Shapley example, order dependence. The toy-model results are asserted by the repository tests (Section 11).

**New, and deliberately small:**
- Load-duration curve: what it is and why sorting hours loses chronology (about 30 minutes).
- Shapley value for 3 players: the average of each driver's marginal contribution over the $3! = 6$ orderings (about 1 hour, extending the two-driver example already done).

**Optional, not required:** old Question 1 (why the dual is a subgradient of the value function); old Question 2 (interaction term) is absorbed into interpreting the 3-player result; old Question 3 (why the Shapley axioms suit cost attribution) becomes one paragraph in the report.

**Dropped with the rescope:** degeneracy and one-sided price derivatives (no price analysis), the Probe A explanation redo, emissions attribution.

Reference facts kept from the write-up: the LP value function is convex and piecewise linear in the right-hand side; an optimal dual vector is a subgradient, and a unique derivative only where the value function is differentiable; hence the first-order dual attribution is a lower bound on the true change, $V(b + \Delta b) \ge V(b) + \lambda^\top \Delta b$, under a consistent sign convention.

### Contribution (replaces the novelty statement)
A clear, reproducible answer to a concrete, policy-relevant question, from a model the owner can fully explain and defend. Novelty is **not** required (D13). Literature is read for context (how RTE, the IEA and the CRE explained 2022) and to position the result, not to prove originality. Never overclaim in the application.

## 4. Data sources (verify licence terms for each)

- **RTE éCO2mix, national consolidated and definitive data** (ODRÉ / data.gouv.fr): <https://odre.opendatasoft.com/explore/dataset/eco2mix-national-cons-def/>. Per the data.gouv.fr dataset page (read by Browser Claude, 2026-11-01): **Licence Ouverte / Open Licence 2.0**; 30-minute step for realised consumption, production by source and cross-border exchanges; coverage January 2012 to December 2024. The page does not list the fuel categories by name: **the owner must confirm the columns (nuclear, gas, coal, oil, hydro, wind, solar, bioenergy, exchanges) in the downloaded file.**
- **Nuclear availability:** candidates are ENTSO-E unavailability data or RTE/EDF publications. Fallback: observed nuclear generation as a proxy (nuclear runs whenever available because it sits low in the merit order), stated as a limitation. To check.
- **Gas and carbon prices:** annual (or monthly) averages; **source TBD**, licence to check.
- **Technology costs and efficiencies:** published RTE, IEA or JRC assumptions; every number goes into `ASSUMPTIONS.md` with its source.
- *No longer needed after the rescope:* Eurostat heating degree days, Copernicus ERA5 (weather regression dropped). ENTSO-E day-ahead prices are optional, only for the validation sanity check.

## 5. Decisions

| # | Decision | Status / evidence |
|---|---|---|
| D1 | ~~Hybrid project: dispatch, attribution, and LMDI benchmark~~ → single question: merit-order LP with 3-driver Shapley attribution, 2019 vs 2022 | Narrowed by owner, 2026-11-01 (D12). LMDI benchmark dropped. |
| D2 | ~~Unit commitment (MILP) is a stretch~~ → not built; listed as future work | Superseded by D12, 2026-11-01 |
| D3 | Minimal AI tooling: one terminal coding agent, chat as reviewer/red team, local models as junior helpers; no multi-agent orchestration | Decided by owner |
| D4 | Agents work on feature branches; owner performs all Git merges (see D10 for the 2026-11-01 exception on commits/pushes) | Decided by owner |
| D5 | Owner derives mathematics by hand first; AI may explain, hint, check reasoning, and locate errors, but must not write report derivations/proofs | Decided by owner |
| D6 | Interconnection: net imports enter as a fixed observed profile inside residual demand; price-taking neighbours (option B) dropped | **Resolved by owner, 2026-11-01**, as part of the approved rescope (D12) |
| D7 | Claude Code is the primary implementation tool; local rules and deny patterns are configured | Deny patterns are configured in `.claude/settings.json`. Commit `6c2a483` added the history-writing deny rules (`merge`, `rebase`, `reset`, `revert`, `cherry-pick`, `tag`, `branch -d`/`-D`) and the updated `CLAUDE.md`; it was merged through PR #4 at `ef72b3c` (verified in local Git history by Claude Code, 2026-10-14). `dsh` is currently unused; dropping it is undecided. |
| D8 | ~~Degenerate hours: report one-sided demand-cost derivatives~~ | Superseded by D12, 2026-11-01: the project attributes costs, not prices |
| D9 | Explicit nonnegativity constraints in the toy model so lower-bound multipliers are available for KKT tests | Implemented in `src/dispatch.py`; tests assert the lower-bound multiplier. Revisit when scaling the model. |
| D10 | Role split: owner decides and merges; Claude Code implements/tests and maintains status; Browser Claude advises/reviews | Decided by owner, 2026-10-14. **Amended by owner, 2026-11-01:** Browser Claude is authorised to make repository changes; it commits and pushes to a feature branch and opens a PR, and never merges. |
| D11 | No separate `DECISIONS.md`; this file is the canonical status and decision record | Decided by owner |
| D12 | **Rescope:** load-duration-curve merit-order model, 3 drivers ($2^3 = 8$ runs), one year pair (2019→2022), sensitivity analysis instead of bootstrap, 8–10 page report; everything in the "extensions" list of Section 3 is cut | Approved by owner, 2026-11-01 |
| D13 | Novelty is not required; the contribution is a clear, correct, finished answer to a real question. The literature-based novelty gate is removed. | Approved by owner, 2026-11-01 |
| D14 | Working rule: no task longer than about 2 hours; each ends with a commit. A task untouched for 3 days is cut smaller and reported to Browser Claude, not postponed. | Approved by owner, 2026-11-01 |

**Open decisions and questions**
- One load-duration curve per year, or one per season/month? Decide after the data check (2022's nuclear shortfall was seasonal).
- Exact technology grouping (~8 groups): after the data check.
- Nuclear availability series: which source, or the generation proxy?
- Gas and carbon price sources remain undecided.
- November examination dates are needed to adjust the schedule.
- Ask the Paris-Saclay department about the *convention de stage* process.
- Check the enrolment-level requirement for every IEA posting before applying.
- `dsh`: decide whether to retain or remove it; do not silently treat it as dropped.
- *Resolved 2026-11-01 (D12):* year pairs (2019→2022 only); driver list (3 drivers); Nov 29 interconnection gate (option B dropped).

Repository: `https://github.com/autumnfold/iea_power_optimisation`. GitHub username changed from `jiuyueqiuu` to `autumnfold`, **reported by owner on 2026-10-29**; new URL verified by Claude Code via clone on 2026-10-29. Local Git history contains the PR #2, PR #3, and PR #4 merge commits. Repository visibility: **public, reported by owner on 2026-09-29**.

## 6. Timeline (rebuilt 2026-11-01 after the rescope)

| By | Deliverable | Notes |
|---|---|---|
| Sep 29–Oct 13 | Repository skeleton, CI workflow, three-generator dispatch/KKT implementation and tests | Done (PR #2, #3 merged) |
| **Sat Nov 7** | Data check: download éCO2mix 2019 and 2022, load them in pandas, fill `docs/data_feasibility.md` | About 2 hours |
| **Sun Nov 15** | 5 sources recorded in `docs/literature.md`; the question restated in 3 sentences (question, method, expected answer) | Starter sources already listed in the file |
| Nov 16–Dec 13 | 2019 model: load-duration curve, ~8 technology groups, checked against the actual 2019 generation mix | Exams fall here (dates TBD): light work |
| Dec 14–Jan 4 | 2022 run, the 8 combinations, 3-player Shapley, sensitivity analysis | Holidays |
| Jan 5–25 | Report (8–10 pp) with the KKT write-up as appendix (small fixes only), README, repo polish | Full draft by Jan 18; check README, licence, secret history, author email, data licences, and CI |
| **Feb 1** | Submit applications | Hard planning deadline Feb 15; IEA rule: at least 3 months before the desired start date |

**History:** the Oct 22 gate (literature, contribution statement, KKT questions) was moved by the owner to Oct 25 (on Oct 22), then to Nov 1 (on Oct 25). No project commits were made between Oct 15 (PR #5) and Oct 29 (PR #6, username change). On Nov 1 the owner rescoped instead (D12).

**If a step slips:** apply D14 first (cut the task smaller). Cut order: the extension (4th driver) → sensitivity reduced to one parameter → never the report.

## 7. Repo standards

- Work inside the WSL filesystem (`~/projects`), not `/mnt/c`.
- Tracked layout (verified by Browser Claude on 2026-11-01 at `1b70363`): `.claude/settings.json`, `.github/workflows/ci.yml`, `.gitignore`, `CLAUDE.md`, `PROJECT_STATE.md`, `pytest.ini`, `requirements.txt`, `src/`, `tests/`. The rescope PR adds `docs/literature.md` and `docs/data_feasibility.md`.
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

## 9. Reading list (since 2026-11-01)

The working list, with links and a reading method, is in `docs/literature.md`: RTE *Bilan électrique 2022*, IEA *Electricity Market Report 2023*, CRE wholesale-market monitoring report for 2022, Ambec & Crampes (TSE) on the 2022 electricity markets, Molnar's chapter on Shapley values, and Kirschen & Strbac for the merit order and load-duration curves.

*Background only, no longer required:* Boyd & Vandenberghe, *Convex Optimization*, ch. 5 (duality; the needed parts are already in the write-up); Wolsey, *Integer Programming* (MILP dropped); Ang's LMDI papers (LMDI dropped); Wood, Wollenberg & Sheblé (unit commitment dropped).

## 10. Unverified / to check

- **Data (owner, by Nov 7):** confirm the éCO2mix fuel categories, units, time step and 2019/2022 coverage in the downloaded file; check whether a public nuclear availability series exists; find a licensable gas and carbon price source.
- **Load-duration-curve adequacy:** whether one annual curve represents 2022's seasonal nuclear shortfall well enough, or whether seasonal curves are needed.
- **IEA applications:** re-check current official eligibility guidance and the education-level requirement for each posting; ask Paris-Saclay about the *convention de stage* process.
- **GitHub CI:** GitHub Actions status has not been independently checked by Claude Code or Browser Claude for any PR; the owner reports it.
- **KKT write-up:** v3 exists as PDFs shared in chat (Oct 6); it is not in the repository. Small fixes for the appendix (Jan): "mathematically necessary" → conditional uniqueness; convexity-proof feasibility clause; $(\lambda, -\bar\mu)$ sign convention; slope vs shadow price.
- **Repository hygiene:** `README.md`, `ASSUMPTIONS.md`, and `report/` are missing. Dependency pins exist in `requirements.txt`; a migration to `pyproject.toml` has not been performed.
- **November examination dates:** not yet supplied.
- **Full model and data pipeline:** not yet implemented.
- **Shapley and sensitivity results:** not yet implemented or run.
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

## 11. Current status

Evidence labels:
- **Verified locally:** observed directly in dated WSL command output or a recorded command result.
- **Verified in Git history:** supported by locally available commit history.
- **Asserted by test code:** the source contains an assertion for the result; this is distinct from a recorded test run.
- **Verified by Browser Claude:** observed by Browser Claude in its own clone of the public repository, with the date.
- **Reported by owner:** stated by the owner in chat.
- **Unverified:** evidence is not currently available.

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

| Deliverable | Due |
|---|---|
| Data check: éCO2mix 2019 and 2022 downloaded, loaded, `docs/data_feasibility.md` filled | **Sat Nov 7** |
| 5 sources in `docs/literature.md`; question restated in 3 sentences | **Sun Nov 15** |
| Supply November exam dates | As soon as known |
| 2019 load-duration-curve model, checked against actual mix | Dec 13 |
| 2022 run, 8 combinations, 3-player Shapley, sensitivity | Jan 4 |
| Report (8–10 pp), README, repo polish | Draft Jan 18, final Jan 25 |
| IEA application | Feb 1 |

*Superseded on 2026-11-01:* the Oct 22/25/Nov 1 gate items (10-source literature search, novelty-based contribution statement, KKT Questions 1–3, Probe A redo), the hourly-model, hydro/interconnection, LMDI and bootstrap milestones. Branch cleanup (proposed Oct 15) remains the owner's decision, with no date.

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
