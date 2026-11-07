"""Flask web frontend for target.py.

Routes
  GET  /            - interactive page to run every target.py function
  POST /api/call    - run one function: {"function": "divide", "args": ["10", "2"]}
  GET  /api/functions - list of functions and their parameters
  GET  /health      - {"status": "ok", "sha": "<deployed commit SHA>"}

Inputs are typed as Python literals (e.g. 42, 3.5, 'text', None, [1, 2],
{'apple': 1.5}, {1, 2}, (1, 2), True) and parsed safely with
ast.literal_eval, so every data type - including wrong types - can be tried.
"""

import ast
import os

from flask import Flask, jsonify, render_template, request

import target

app = Flask(__name__)

MAX_INPUT_LENGTH = 300
MAX_RESULT_LENGTH = 2000

# name -> (category, description, [(param, placeholder), ...])
FUNCTIONS = {
    "is_adult": ("Integer", "True if age is 18 or more", [("age", "18")]),
    "celsius_to_fahrenheit": ("Float", "Celsius to Fahrenheit (2 dp)", [("celsius", "36.6")]),
    "count_vowels": ("String", "Count vowels, ignoring case", [("text", "'Hello World'")]),
    "invert": ("Boolean", "Return the opposite of flag", [("flag", "True")]),
    "greet": ("None", "Greet by name, or Guest", [("name", "'Alice'  or  None")]),
    "find_max": ("List", "Largest number in a list", [("numbers", "[3, 9, 2]")]),
    "get_price": (
        "Dictionary",
        "Price of an item",
        [("prices", "{'apple': 1.5, 'milk': 0.9}"), ("item", "'apple'")],
    ),
    "swap": ("Tuple", "Swap a pair of values", [("pair", "(1, 2)")]),
    "common_items": (
        "Set",
        "Items found in both sets",
        [("set_a", "{1, 2, 3}"), ("set_b", "{2, 3, 4}")],
    ),
    "is_leap_year": ("Date", "True if year is a leap year", [("year", "2024")]),
    "to_int": ("Type conversion", "Convert a value to int", [("value", "'42'")]),
    "divide": ("Math", "a / b", [("a", "10"), ("b", "4")]),
    "power": ("Math", "base ** exponent", [("base", "2"), ("exponent", "10")]),
    "square_root": ("Math", "Square root of x", [("x", "16")]),
    "factorial": ("Math", "n!", [("n", "5")]),
    "average": ("Math", "Average of a list", [("numbers", "[1, 2, 3, 4]")]),
}

# Guards so a single request cannot hang the public server.
LIMITS = {"power": ("exponent", 10_000), "factorial": ("n", 1_000)}


def deployed_sha():
    """Commit SHA of the running deployment (Render sets RENDER_GIT_COMMIT)."""
    return os.environ.get("RENDER_GIT_COMMIT") or os.environ.get("GIT_SHA") or "unknown"


def parse_value(raw):
    """Parse a Python literal; fall back to the raw text as a plain string."""
    try:
        return ast.literal_eval(raw), True
    except (ValueError, SyntaxError, TypeError, MemoryError, RecursionError):
        return raw, False


def describe(value):
    """Return (repr, type name) for a result, safe for huge numbers."""
    try:
        text = repr(value)
    except ValueError:  # int too large to convert to str (Python 3.11+)
        text = f"<int with {value.bit_length()} bits>"
    if len(text) > MAX_RESULT_LENGTH:
        text = text[:MAX_RESULT_LENGTH] + "... (truncated)"
    return text, type(value).__name__


@app.get("/")
def index():
    sha = deployed_sha()
    return render_template("index.html", functions=FUNCTIONS, sha=sha, short_sha=sha[:7])


@app.get("/health")
def health():
    return jsonify(status="ok", sha=deployed_sha())


@app.get("/api/functions")
def list_functions():
    return jsonify(
        {
            name: {"category": cat, "description": desc, "params": [p for p, _ in params]}
            for name, (cat, desc, params) in FUNCTIONS.items()
        }
    )


@app.post("/api/call")
def call_function():
    payload = request.get_json(silent=True) or {}
    name = payload.get("function")
    raw_args = payload.get("args", [])

    if name not in FUNCTIONS:
        return jsonify(
            ok=False, error_type="UnknownFunction", message=f"unknown function: {name!r}"
        ), 404
    if not isinstance(raw_args, list) or not all(isinstance(a, str) for a in raw_args):
        return jsonify(
            ok=False, error_type="BadRequest", message="args must be a list of strings"
        ), 400
    if any(len(a) > MAX_INPUT_LENGTH for a in raw_args):
        return jsonify(
            ok=False,
            error_type="BadRequest",
            message=f"inputs are limited to {MAX_INPUT_LENGTH} characters",
        ), 400

    # An empty trailing field means "argument not given" (lets greet() use its default).
    while raw_args and raw_args[-1].strip() == "":
        raw_args = raw_args[:-1]

    args, notes = [], []
    for param, raw in zip([p for p, _ in FUNCTIONS[name][2]], raw_args, strict=False):
        value, parsed = parse_value(raw.strip())
        if not parsed:
            notes.append(f"{param} was read as the string {raw.strip()!r}")
        args.append(value)

    if name in LIMITS:
        param, limit = LIMITS[name]
        index_ = [p for p, _ in FUNCTIONS[name][2]].index(param)
        value = args[index_] if index_ < len(args) else None
        if isinstance(value, (int, float)) and abs(value) > limit:
            return jsonify(
                ok=False,
                error_type="LimitExceeded",
                message=f"{param} is limited to ±{limit} on this server",
            ), 400

    call_text = f"{name}({', '.join(describe(a)[0] for a in args)})"
    try:
        result = getattr(target, name)(*args)
    except Exception as exc:  # show every error the function raises
        return jsonify(
            ok=False, call=call_text, error_type=type(exc).__name__, message=str(exc), notes=notes
        )
    text, type_name = describe(result)
    return jsonify(ok=True, call=call_text, result=text, type=type_name, notes=notes)


if __name__ == "__main__":
    app.run(debug=True)
