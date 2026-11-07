# functional-testing-2507229

[![CI](https://github.com/Borna98/functional-testing-2507229/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Borna98/functional-testing-2507229/actions/workflows/ci.yml)

Functional tests, CI/CD and live deployment for `target.py` (16 functions:
11 data-type, 5 mathematics).

**Live site:** https://functional-testing-2507229.onrender.com  
**Health / deployed commit:** https://functional-testing-2507229.onrender.com/health

## Project layout

```
target.py                  functions under test (unchanged original)
tests/test_target.py       functional tests for all 16 functions
tests/test_app.py          tests for the web frontend
app.py                     Flask frontend + /health + /api/call
templates/, static/        frontend page, styles and script
scripts/smoke_test.py      live checks used by the smoke-test job
.github/workflows/ci.yml   test -> deploy -> smoke-test pipeline
requirements.txt           pinned dependencies
pyproject.toml             pytest, coverage and ruff settings
```

## Setup

```bash
git clone https://github.com/Borna98/functional-testing-2507229.git
cd functional-testing-2507229
python -m venv .venv
# Windows: .venv\Scripts\activate     macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

## Run the tests

```bash
pytest --cov=target --cov-branch --cov-report=term-missing --cov-fail-under=100
ruff check .
```

The suite covers valid inputs, boundary values, invalid values and wrong
types for every function, uses `parametrize`, checks exceptions with the exact
class (plus `match=` on the message), checks result types, and uses
`pytest.approx` only for inexact floating-point results. It reaches 100% line
and branch coverage of `target.py` with no skips or xfails.

## Run the frontend locally

```bash
python app.py            # http://127.0.0.1:5000
```

Type each argument as a Python literal (`42`, `'text'`, `None`, `[1, 2]`,
`{'apple': 1.5}`, `{1, 2}`, `(1, 2)`, `True`). The page shows the result and
its type, or the exception class and message. The footer shows the deployed
commit SHA, also available at `/health`.

## CI/CD pipeline

| Job | Runs when | What it does |
|---|---|---|
| `test` | every push, PRs to `main` | Python 3.10 / 3.11 / 3.12 with pip cache, `ruff` lint, pytest with 100% coverage gate, uploads the coverage report artifact |
| `deploy` | push to `main` only, `needs: test` | calls the Render deploy hook (secret `RENDER_DEPLOY_HOOK`) for this exact commit |
| `smoke-test` | after `deploy` | waits until `/health` reports the new SHA, then checks three live requests |

Render auto-deploy is **off**, so only commits that pass every test go live.

## Suspected bugs in target.py

`target.py` was not modified. These behaviours look wrong or are not covered
by the docstrings:

1. **`power(-8, 1/3)` returns a complex number** (`(1.0000000000000002+1.7320508075688772j)`)
   instead of `-2.0` or a clear error. A negative base with a fractional exponent
   silently produces a complex result.
2. **`power(0, -1)` raises `ZeroDivisionError` with Python's message**
   (`0.0 cannot be raised to a negative power`), unlike `divide`, which has its own
   checked message.
3. **`is_leap_year(True)` returns `False`** and `is_leap_year(2000.0)` returns `True`:
   bools and floats are accepted as years without a type check.
4. **`greet(123)` raises `AttributeError`**, not `TypeError`, for a non-string name.
5. **`is_adult(float("nan"))` returns `False`** instead of raising, and
   `is_adult(True)` is accepted as age 1.
6. **`find_max("abc")` returns `"c"`**: any non-empty sequence is accepted, not only lists of numbers.
7. **`factorial(True)` returns `1`**, and `factorial(3.5)` raises a generic
   `TypeError` from `range` rather than a clear message.
8. **`to_int(3.9)` returns `3`** (silent truncation, no rounding or error), and
   `to_int("3.5")` raises `ValueError`.
9. **`get_price` error message**: `KeyError` wraps its message in quotes, so
   `str(error)` is `"'apple not found'"`.
10. **`swap("ab")` returns `('b', 'a')`**: any length-2 sequence is accepted, not only tuples.
