# IEA power-system attribution project

## Context
Hourly LP dispatch model of the French power system; Shapley attribution of cost changes between years. Owner: L2 maths student. PROJECT_STATE.md is the plan.

## Commands
- Tests: `pytest`
- Lint: `ruff check .`

## Rules
- Work only on a feature branch, never on `main`. Never commit or push.
- Never write mathematical derivations or proofs. Check them only, and say where they fail.
- Every change must come with tests, and `pytest` and `ruff` must pass.
- Duals: keep raw solver signs; convert explicitly and document the convention. Never use abs().
- Floats in tests: `pytest.approx`, never `==`.
- Every numerical assumption goes into ASSUMPTIONS.md with a source.
- Never modify or commit anything in `data/`.
- Explain every non-obvious line you write, because the owner must be able to defend it in an interview.
