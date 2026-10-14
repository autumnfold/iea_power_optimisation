# IEA power-system attribution project

## Context

Hourly LP dispatch model of the French power system; Shapley attribution of cost changes between years. Owner: L2 maths student.

`PROJECT_STATE.md` is the canonical project plan and status document. Read it before every task. If it is unavailable or its contents are unclear, ask the owner rather than guessing.

## Commands

- Tests: `pytest`
- Lint: `ruff check .`

## Git: the owner controls Git writes

- Work only on a feature branch, never on `main`.
- Never commit, push, merge, rebase, reset, revert, cherry-pick, tag, delete branches, or otherwise rewrite Git history.
- Inspection commands (`status`, `diff`, `log`, `show`) and `fetch` are allowed.
- Never switch branches or discard changes without the owner's approval.

## Rules

- Mathematics: the owner derives the mathematics. You may explain concepts, give hints, check reasoning, and identify exactly where a derivation fails. Never write derivations or proofs intended for the owner's report.
- Code and behaviour changes must include new or updated tests. Documentation-only changes need no tests. Run `pytest` and `ruff check .` when applicable. Report failures and checks that could not be run honestly; never claim a check passed unless it actually did.
- Duals: keep raw solver signs; convert explicitly and document the convention. Never use `abs()` to conceal sign errors.
- Floats in tests: use `pytest.approx`, never exact `==` comparisons.
- Every numerical assumption must be recorded in `ASSUMPTIONS.md` with a source. Create the file when first needed.
- Never modify or commit anything in `data/`.
- Explain every non-obvious line you write, because the owner must be able to defend it in an interview.

## Documentation

- `PROJECT_STATE.md` is the single canonical status document. Project decisions belong in its decision section.
- Other documentation is allowed when it has a distinct purpose, such as `README.md`, `ASSUMPTIONS.md`, `report/`, or `docs/`.
- Never create competing project-status documents or duplicate decision logs.

## Maintaining `PROJECT_STATE.md`

At the end of every meaningful task:

- Update routine status and open deliverables in section 11.
- Update unverified items in section 10.
- Add one entry to the change log in section 13.
- Ask the owner about priorities, deadlines, gates, project direction, or genuinely ambiguous decisions. Do not silently decide these. Record proposals as **Proposed** and flag them in the handoff note.
- Never silently delete unresolved facts. Mark them resolved, superseded, or still open.

Record each status level separately, and only when supported by evidence:

- **Implemented locally:** changes exist in the working tree.
- **Verified locally:** record the exact command and result.
- **Committed:** record the hash from `git log`.
- **Pushed:** verify the commit on the remote branch.
- **PR merged:** verify the merge on `origin/main`, or clearly label it as reported by the owner.
- **CI result:** use an accessible CI log or clearly label the result as reported by the owner.

Label the evidence source, such as **verified by Claude Code** or **reported by owner**. If evidence is missing, record the item as unverified in section 10.

Do not claim that work is committed, pushed, merged, or CI-verified merely because a change exists locally.

## End-of-task handoff

At the end of every meaningful task, provide a concise handoff in chat, not in a separate file:

1. What changed, including filenames.
2. How it was verified, with commands and actual results.
3. What remains unverified and which questions need the owner's decision.
4. What changed in `PROJECT_STATE.md`.
