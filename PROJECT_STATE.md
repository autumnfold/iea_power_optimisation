# PROJECT_STATE.md

> Canonical source of truth for project status, decisions, open questions, and change history. Last reconciled: 2026-10-14.
> Evidence labels matter: distinguish local verification, Git history, reports from Browser Claude, and unresolved claims.
> **Working protocol:** follow the role-specific instructions in Section 12 before starting work.

---

## 1. Goal

Land a summer internship at the **International Energy Agency (IEA, Paris)** next summer (summer 2027), by producing a serious, rigorous, competitive, public project that shows quantitative modelling skill and clear writing.

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

## 3. The project

**Working title:** *What drove France's power-system costs and prices between 2019 and 2024? An optimisation-based attribution using LP duality and Shapley values, with quantified uncertainty.*

**Origin:** a merge of two candidate projects (LMDI decomposition + weather normalisation, and a power-system optimisation roadmap: dispatch → unit commitment → capacity expansion). Owner chose the hybrid.

### Method (proposed; refine after literature and data checks)
1. **Dispatch model:** hourly LP, one full year (8,760 h), French fleet, hydro energy budgets, pumped storage, interconnection.
2. **Drivers (~6):** weather-normalised demand; weather effect on demand (piecewise-linear degree-day regression, change-point base temperature, Newey–West errors); wind/solar availability; nuclear availability; hydro inflows; fuel and carbon prices.
3. **Attribution:** for a pair of years (e.g. 2019 vs 2022), evaluate all driver coalitions (2^6 = 64 LP runs per pair) and compute exact **Shapley attributions** of the change in system cost.
4. **Model-free benchmark:** LMDI decomposition of observed data for the same years. Compare accounting vs counterfactual answers and explain disagreements.
5. **Uncertainty:** block bootstrap on the weather regression + perturbation of cost assumptions, giving confidence intervals on each driver's share. Report whether the driver ranking is robust.
6. **Stretch (only if ahead):** small clustered-unit MILP for one week, compare attribution under LP vs MILP. The LP value function has convexity properties useful for dual analysis; the MILP value function need not be convex, so dual-based attribution does not transfer directly.

### Mathematical core to be written and proven by the owner
- For the LP, the optimal-cost value function is convex and piecewise linear in relevant right-hand-side parameters. An optimal dual vector gives a subgradient under the chosen sign convention; it equals a unique derivative only where the value function is differentiable (for example, away from a kink).
- With the model's balance convention, `lambda` is the demand-cost marginal value when the value function is differentiable. For capacity bounds, `mu_max` and `mu_min` are KKT multipliers obtained by negating the raw solver duals. A capacity multiplier describes the local value of relaxing a bound; interpret it with the sign convention and active constraints stated.
- Degeneracy: non-unique duals at merit-order kinks; what the solver returns; how it is handled.
- Shapley axioms (efficiency, symmetry, dummy player, additivity); attributions sum exactly to the cost change. The owner must explain why these axioms and this allocation rule suit the project's cost-attribution question.
- **Order dependence:** compare Shapley attribution with first-order dual attribution `Σ λ·Δb` and sequential attribution; quantify variation over driver orderings. For a convex value function, a subgradient at `b` satisfies `V(b + Δb) >= V(b) + λᵀΔb` when the same value-function and sign conventions apply.
- Known traps: cost attribution is clean when cost is the LP objective; **emissions attribution is not** (optimal dispatch can be non-unique), so an explicit tie-break rule (e.g. secondary emissions minimisation) is needed.

### Validation
- Pre-register metrics *before* running: price-duration-curve distance, rank correlation of model dual price vs actual day-ahead price.
- The single-hour dual will not match real prices exactly (interconnection, hydro water values, must-run, bidding). Present divergences as analysis, not failure.

### Novelty statement (NOT yet verified)
Counterfactual merit-order studies and Shapley decompositions in energy each exist separately. Whether this exact combination is unpublished is **unknown**. The claimed contribution is: exact, axiomatic attribution on an LP-based dispatch model, with quantified order dependence and a bootstrap uncertainty layer. Literature search and a defensible contribution statement are due **Oct 22**. Never overclaim in the application.

## 4. Data sources (verify licence terms for each)
- RTE éCO2mix open data (opendata.reseaux-energies.fr): generation by source, demand, exchanges. *Granularity and year coverage to be checked by the owner.*
- ENTSO-E Transparency Platform (free API key needed): day-ahead prices, cross-border flows.
- Eurostat: energy balances and heating degree days (for the LMDI part and weather normalisation).
- Copernicus ERA5 temperature data (optional, for own degree days).
- Fuel and carbon price series: **source TBD.**
- Cost assumptions: from RTE or IEA published data; every number goes into `ASSUMPTIONS.md` with its source.

## 5. Decisions

| # | Decision | Status / evidence |
|---|---|---|
| D1 | Hybrid project: dispatch, attribution, and LMDI benchmark | Decided by owner |
| D2 | Unit commitment (MILP) is a stretch, not core | Decided by owner |
| D3 | Minimal AI tooling: one terminal coding agent, chat as reviewer/red team, local models as junior helpers; no multi-agent orchestration | Decided by owner |
| D4 | Agents work on feature branches; owner performs all Git writes | Decided by owner |
| D5 | Owner derives mathematics by hand first; AI may explain, hint, check reasoning, and locate errors, but must not write report derivations/proofs | Decided by owner |
| D6 | Interconnection: fixed net exchanges (option A) initially; price-taking neighbours (B) remain a stretch | **Pending owner confirmation.** Browser Claude reportedly selected A during the Oct 11 schedule rebuild; that report is not owner confirmation. |
| D7 | Claude Code is the primary implementation tool; local rules and deny patterns are configured | Deny patterns are configured in `.claude/settings.json`. Commit `6c2a483` added the history-writing deny rules (`merge`, `rebase`, `reset`, `revert`, `cherry-pick`, `tag`, `branch -d`/`-D`) and the updated `CLAUDE.md`; it was merged through PR #4 at `ef72b3c` (verified in local Git history by Claude Code, 2026-10-14). `dsh` is currently unused; dropping it is undecided. |
| D8 | Degenerate hours: report one-sided demand-cost derivatives by re-solving at demand ± ε | Proposed by owner; confirm implementation when the hourly model exists |
| D9 | Explicit nonnegativity constraints in the toy model so lower-bound multipliers are available for KKT tests | Implemented in the supplied `src/dispatch.py`; tests assert the lower-bound multiplier. Full-model relevance remains to be revisited. |
| D10 | Role split: owner decides and performs Git writes; Claude Code implements/tests and maintains status; Browser Claude advises/reviews but does not edit the repository | Decided by owner, 2026-10-14 |
| D11 | No separate `DECISIONS.md`; this file is the canonical status and decision record | Decided by owner |

**Open decisions and questions**
- Year pairs: 2019→2022 and 2022→2024 are proposed, not confirmed.
- Final driver list: approximately six drivers are proposed; confirm the final list before implementation.
- Fuel and carbon price data sources remain undecided.
- November examination dates are needed to adjust the schedule.
- Ask the Paris-Saclay department about the *convention de stage* process.
- Check the enrolment-level requirement for every IEA posting before applying.
- At the November 29 gate, review whether price-taking neighbours are feasible; otherwise retain fixed net exchanges and disclose the limitation.
- `dsh`: decide whether to retain or remove it; do not silently treat it as dropped.

Repository: `https://github.com/autumnfold/iea_power_optimisation`. GitHub username changed from `jiuyueqiuu` to `autumnfold`, **reported by owner on 2026-10-29**; new URL verified by Claude Code via clone on 2026-10-29. Local Git history contains the PR #2, PR #3, and PR #4 merge commits. Repository visibility: **public, reported by owner on 2026-09-29**.

## 6. Timeline (reconciled 2026-10-14)

| Dates | Deliverable | Gate |
|---|---|---|
| Sep 29–Oct 13 | Repository skeleton, CI workflow, three-generator dispatch/KKT implementation and tests | Browser Claude reports PR #2 and PR #3 merged; local Git history confirms the merge commits |
| **Proposed: Oct 15** | Review branch-cleanup evidence; do not delete branches until the owner decides | Confirm whether any local branch is safe to delete; check remote-branch status without making changes |
| By Thu Oct 22 | Literature search with at least 10 relevant sources; owner answers KKT questions 1–3 in their own words; redo the Probe A explanation; edit the write-up and place the `.tex` source in `report/`; write a three-sentence contribution statement | If the contribution cannot be defended, rescope before writing real-data code |
| Oct 23–Nov 15 | Single-period model, then full-year French dispatch for 2019 | Pre-register validation metrics by Oct 28 |
| Nov 16–29 | Hydro budgets, pumped storage, and interconnection modelling | Nov 29 gate: decide whether price-taking neighbours are feasible |
| Nov 30–Dec 14 | Shapley engine with tests and LMDI benchmark | Attributions must sum to the modelled cost change |
| Dec 15–Jan 4 | Bootstrap, sensitivity, and 2022/2024 analysis | Allow for exams and holidays |
| Jan 5–18 | Approximately 15-page report and repository polish | Full draft by Jan 18; check README, licence, secret history, author email, data licences, and CI |
| Jan 19–Feb 1 | Prepare and submit applications | Target Feb 1; hard planning deadline Feb 15 |

The schedule and reported milestone completion above are based partly on a Browser Claude update provided by the owner on 2026-10-14. They are not independent evidence that every research deliverable is finished. October 15 remains a proposed date, not a confirmed commitment. November exams may overlap with the Nov 16–29 work; exact dates remain TBD.

**If a gate is missed, cut scope rather than quality.** Cut order: MILP stretch, then second year pair; do not cut the report. Consider placing interconnection option B after the MILP stretch in the cut order, but the owner must confirm the scope order.

## 7. Repo standards

- Work inside the WSL filesystem (`~/projects`), not `/mnt/c`.
- Current tracked layout verified locally: `.claude/settings.json`, `.github/workflows/ci.yml`, `.gitignore`, `CLAUDE.md`, `PROJECT_STATE.md`, `pytest.ini`, `requirements.txt`, `src/`, and `tests/`.
- `README.md`, `ASSUMPTIONS.md`, and `report/` are missing from the current local checkout. Create them when their purposes are reached. `DECISIONS.md` is intentionally not used.
- `data/` must remain untracked and must never be modified by an agent without explicit owner direction.
- Current dependency pins in `requirements.txt`: `pyomo==6.8.0`, `highspy==1.7.2`, `pytest==9.1.1`, `ruff==0.1.6`. The CI workflow installs this file, then runs `ruff check .` and `pytest` on Python 3.12.
- Recorded local verification on 2026-10-14: Ruff 0.1.6 (the pinned CI version) passed; `.venv/bin/pytest` reported 8 passed; `git diff --check` passed. The locally installed Ruff 0.16.9 reports an import-formatting finding that does not reproduce under Ruff 0.1.6. Keep the version distinction explicit; do not claim that the two Ruff versions behave identically.
- `.venv/` is not in the current `git ls-files` output; no tracked virtual environment was found.
- **Git writes are owner-only.** Agents must not commit, push, merge, rebase, reset, revert, cherry-pick, tag, or rewrite Git history, even if asked to do so in a task-level instruction. The owner performs all Git writes.
- Agents must not switch branches or discard working-tree changes without explicit owner approval.
- Inspection commands include `git status`, `git diff`, `git log`, `git show`, and branch-listing commands. `git fetch` is allowed without separate approval to refresh remote-tracking references; it can update those references but does not itself commit, push, merge, or rewrite Git history. All Git history writes remain owner-only.
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

## 9. Reading list

- Boyd & Vandenberghe, *Convex Optimization*, ch. 5 (duality).
- Wolsey, *Integer Programming*, ch. 1–2 (only for the MILP stretch).
- Ang's papers on LMDI.
- IEA Energy Efficiency reports (framing and vocabulary); methodology annexes of recent IEA outlooks.
- Wood, Wollenberg & Sheblé, *Power Generation, Operation, and Control* (UC formulations, stretch only).

## 10. Unverified / to check

- **Research novelty:** the specific combination of LP-dispatch Shapley attribution, order-dependence analysis, and bootstrap uncertainty has not yet been established as novel. Literature search is due Oct 22.
- **Data:** verify éCO2mix granularity, year coverage, and licences; verify licences and access conditions for all other sources.
- **Fuel/carbon prices:** source remains TBD.
- **Validation:** metrics must be pre-registered before real-data model runs.
- **IEA applications:** re-check current official eligibility guidance and the education-level requirement for each posting; ask Paris-Saclay about the *convention de stage* process.
- **GitHub CI:** local tests and pinned Ruff passed according to recorded local output dated 2026-10-14; GitHub Actions status has not been independently checked by Claude Code.
- **KKT learning deliverable:** the owner still needs to answer questions 1–3 in their own words, redo the Probe A explanation, and edit the write-up. Browser Claude reported a v3 write-up on 2026-10-14; it was not in the tracked-file list inspected that day.
- **Repository hygiene:** `README.md`, `ASSUMPTIONS.md`, and `report/` are missing from the current local checkout. Dependency pins exist in `requirements.txt`; a migration to `pyproject.toml` has not been performed.
- **November examination dates:** not yet supplied.
- **One-sided derivatives at degenerate demand points:** rule is proposed; confirm behaviour on the hourly model.
- **Full-year model and data pipeline:** not yet verified as implemented.
- **Shapley/LMDI/uncertainty results:** not yet verified as implemented or run.
- **Test design:** `tests/test_three_generator.py::test_raw_pyomo_duals` builds a separate Pyomo model rather than exercising `solve_dispatch()`; it tests raw solver dual signs, but does not independently test the production function's dual extraction. Improve this when appropriate.
- **Branch cleanup:** on 2026-10-14, after `git fetch origin`, with `main` and `origin/main` both at `ef72b3c` (verified by Claude Code):
  - `git branch -r --merged origin/main` listed `origin/chore/claude-code-config`, `origin/chore/workflow`, `origin/main`, and `origin/model/three-generator-kkt`.
  - `git branch --merged main` listed `chore/workflow`, `docs/state-pr4`, `main`, and `model/three-generator-kkt`. `docs/state-pr4` appears because it pointed at the same commit as `main` when listed.
  - There is no local `chore/claude-code-config` branch.
  - These listings only show merge status. The owner decides any branch deletion.
- **Numerical results from the write-up:** results not asserted by repository tests (including any Shapley split, first-order total, or convexity-gap figure) must remain unverified until reproduced from code or independently checked calculations.
- **CI/tooling follow-up:** check the actual GitHub Actions result; consider adding a minimal README; align local and pinned Ruff versions or document the reason for using the pinned version. Do not infer a CI result from local tests.
- **Local Git remote after the username change:** the owner's local `origin` may still point to `jiuyueqiuu/iea_power_optimisation`. GitHub redirects renamed accounts' repositories for now, but the owner should run `git remote set-url origin https://github.com/autumnfold/iea_power_optimisation`. Not verified by Claude Code.

## 11. Current status

Evidence labels:
- **Verified locally:** observed directly in dated WSL command output or a recorded command result.
- **Verified in Git history:** supported by locally available commit history.
- **Asserted by test code:** the source contains an assertion for the result; this is distinct from a recorded test run.
- **Reported by Browser Claude:** stated in the update provided by the owner on 2026-10-14; not independently checked by Claude Code.
- **Unverified:** evidence is not currently available.

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
- Historical (before PR #4): in the earlier reconciliation, `HEAD`, `main`, and `origin/main` were reported at `b57fbf2`. This is no longer the current state; see the PR #4 record below.
- PR #4 merge commit: `ef72b3c` (`Merge pull request #4 from jiuyueqiuu/chore/workflow`), with parents `b57fbf2` and `6c2a483`. `git diff --stat ef72b3c^1 ef72b3c` shows exactly three files changed: `.claude/settings.json`, `CLAUDE.md`, and `PROJECT_STATE.md`. Verified by Claude Code on 2026-10-14 after `git fetch origin`. At that verification time on 2026-10-14, `HEAD`, `main`, and `origin/main` all resolved to `ef72b3c`; this is a dated observation, not a claim about the current checkout. The GitHub Actions result for PR #4 has not been verified.

**Reported by Browser Claude; owner follow-up remains**
- Browser Claude reported on 2026-10-14 that PR #2 and PR #3 merged on Oct 13 and described the KKT write-up as version 3. Local Git history confirms the merge commits, but not every scientific claim or write-up detail.
- Open owner deliverables as of 2026-10-14: answer KKT questions 1–3 in the owner's own words, revisit Probe A, complete the literature search, and produce a defensible contribution statement by Oct 22.
- Browser Claude reported selecting interconnection option A during the Oct 11 schedule rebuild; owner confirmation is pending (see D6).

**Open deliverables**

| Deliverable | Due / status |
|---|---|
| Review feature-branch cleanup evidence; do not delete branches until the owner decides | Proposed: Thu Oct 15 |
| Literature search (at least 10 sources), owner answers to KKT questions 1–3, redo Probe A explanation, write-up edits and `.tex` in `report/`, three-sentence contribution statement | Thu Oct 22 |
| Pre-register validation metrics | Oct 28 |
| Implement and validate full-year French dispatch for 2019 | Nov 15 |
| Hydro budgets, pumped storage, and interconnection gate | Nov 16–29 |
| Shapley engine and LMDI benchmark | Nov 30–Dec 14 |
| Bootstrap, sensitivity, and 2022/2024 analysis | Dec 15–Jan 4 |
| Full report and repository polish | By Jan 18 |
| Target IEA application submission | Around Feb 1; hard planning deadline Feb 15 |

**Current blockers (evidence recorded 2026-10-14):** no technical blocker was demonstrated by the inspected toy-model code and tests. The full-year model is not yet verified as implemented; open decisions and unverified items remain in Sections 5 and 10.

## 12. Session protocol and roles

### Owner
- Makes project, scope, deadline, and methodology decisions.
- Derives mathematical arguments and proofs intended for the report.
- Performs all Git writes: commits, pushes, merges, rebases, resets, reverts, cherry-picks, tags, history rewrites, and branch deletion.
- Confirms proposed dates and unresolved choices. Reviews diffs before deciding whether to apply changes. Reports each PR number and CI status to Browser Claude, and reports any moved deadline before the date.

### Claude Code
- Reads this file before each task and briefly states current status and the next concrete action.
- Implements and tests approved code/documentation changes on a feature branch; does not perform Git writes.
- Must not switch branches or discard changes without explicit owner approval.
- At the end of a meaningful task, updates Sections 10 (unverified items), 11 (status/deliverables), and 13 (change log) itself, using dated evidence. It must not silently change project decisions in Sections 1, 3, 5, or 6; propose material changes for owner confirmation.
- Gives a concise handoff in chat: changed files, exact checks and results, unverified items, and owner decisions needed.
- Never claims to have inspected a live repository, machine, CI run, or browser state unless evidence was supplied. Ask for raw terminal output or logs when needed.

### Browser Claude
- Advises, researches, reviews pull requests, and audits this file against the synced repository.
- Does not edit the repository or maintain a separate canonical status copy.
- Distinguishes observed GitHub evidence from statements reported by the owner or another assistant.

### Shared rules
- The owner derives mathematical arguments by hand first. AI may explain concepts, provide hints, check the owner's reasoning, and locate errors; AI must not write derivations or proofs intended for the owner's report.
- Agents may not commit, push, merge, rebase, reset, revert, cherry-pick, tag, rewrite Git history, or delete branches. The owner performs Git writes.
- Distinguish local implementation, local verification, commits, remote pushes, merges, and CI results. Identify whether each fact was verified locally, observed in Git history, asserted by supplied tests, or reported by the owner/Browser Claude.
- Ask the owner about priorities, deadlines, project direction, and genuinely ambiguous decisions. Record proposals as **Proposed** rather than silently deciding.
- Keep this file canonical. Do not create duplicate project-status or decision logs. `ASSUMPTIONS.md` is reserved for numerical assumptions and their sources.

## 13. Change log

- 2026-09-29: initial project-state document; initial repository, scope, and timeline recorded.
- 2026-10-14: reconciliation prepared from local repository evidence and the Browser Claude update supplied by the owner. KKT implementation and merge history are recorded separately from remaining owner learning deliverables. Previously recorded local checks: pinned Ruff 0.1.6 passed, 8 tests passed, and `git diff --check` passed. GitHub Actions status, novelty, data licences, and full-year implementation remain unverified; public visibility was reported by the owner on 2026-09-29.
- 2026-10-14: workflow reconciliation: recorded role split (D10), owner-only Git history writes, owner-authored mathematical derivations, D6 pending owner confirmation, the value-function subgradient correction, evidence labels, the `test_raw_pyomo_duals` testing limitation, and the `dsh` decision as open. October 15 remains proposed; the Oct 17 placeholder was removed.
- 2026-10-14: recorded the PR #4 merge (`ef72b3c`, second parent `6c2a483`; it changed `.claude/settings.json`, `CLAUDE.md`, and `PROJECT_STATE.md`), verified in local Git history by Claude Code after `git fetch origin`. Removed the obsolete claims that `.claude/settings.json` and `CLAUDE.md` were modified and uncommitted. Updated the D7 evidence and the branch-cleanup listings. The GitHub Actions result for PR #4 remains unverified.
- 2026-10-29: recorded the GitHub username change from `jiuyueqiuu` to `autumnfold` (reported by owner). Updated the repository URL in section 5 and verified the new URL by cloning (Claude Code). The PR #2–#4 merge records in section 11 keep their original commit messages, which still name `jiuyueqiuu`. The owner's local remote update is recorded as unverified in section 10.
