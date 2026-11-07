"""Tests for the Flask frontend (app.py)."""

import pytest

import app as webapp


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("RENDER_GIT_COMMIT", "abc1234def5678")
    webapp.app.config["TESTING"] = True
    return webapp.app.test_client()


def call(client, function, *args):
    return client.post("/api/call", json={"function": function, "args": list(args)})


def test_health_returns_sha(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok", "sha": "abc1234def5678"}


def test_health_unknown_sha(monkeypatch):
    monkeypatch.delenv("RENDER_GIT_COMMIT", raising=False)
    monkeypatch.delenv("GIT_SHA", raising=False)
    assert webapp.app.test_client().get("/health").get_json()["sha"] == "unknown"


def test_index_lists_all_functions_and_sha(client):
    html = client.get("/").get_data(as_text=True)
    for name in webapp.FUNCTIONS:
        assert f'data-function="{name}"' in html
    assert "abc1234def5678" in html


def test_function_list_has_16_entries(client):
    assert len(client.get("/api/functions").get_json()) == 16


@pytest.mark.parametrize(
    "function, args, result, type_name",
    [
        ("divide", ["10", "4"], "2.5", "float"),
        ("is_adult", ["18"], "True", "bool"),
        ("count_vowels", ["'Hello'"], "2", "int"),
        ("greet", [""], "'Hello, Guest!'", "str"),
        ("get_price", ["{'apple': 1.5}", "'apple'"], "1.5", "float"),
        ("common_items", ["{1, 2}", "{2, 3}"], "{2}", "set"),
        ("swap", ["(1, 2)"], "(2, 1)", "tuple"),
    ],
)
def test_successful_calls(client, function, args, result, type_name):
    data = call(client, function, *args).get_json()
    assert data["ok"] is True
    assert data["result"] == result
    assert data["type"] == type_name


@pytest.mark.parametrize(
    "function, args, error_type",
    [
        ("divide", ["1", "0"], "ZeroDivisionError"),
        ("find_max", ["[]"], "ValueError"),
        ("get_price", ["{}", "'x'"], "KeyError"),
        ("to_int", ["True"], "TypeError"),
        ("invert", ["1"], "TypeError"),
    ],
)
def test_errors_are_reported(client, function, args, error_type):
    data = call(client, function, *args).get_json()
    assert data["ok"] is False
    assert data["error_type"] == error_type


def test_unparseable_input_is_treated_as_string(client):
    data = call(client, "count_vowels", "hello world").get_json()
    assert data["result"] == "3"
    assert data["notes"]


def test_unknown_function_is_404(client):
    assert call(client, "os_system", "1").status_code == 404


@pytest.mark.parametrize(
    "payload", [{"function": "divide", "args": "10"}, {"function": "divide", "args": [1, 2]}]
)
def test_bad_args_are_400(client, payload):
    assert client.post("/api/call", json=payload).status_code == 400


def test_long_input_is_rejected(client):
    assert call(client, "count_vowels", "a" * 1000).status_code == 400


@pytest.mark.parametrize(
    "function, args",
    [("power", ["2", "10**9"]), ("power", ["2", "100000"]), ("factorial", ["5000"])],
)
def test_limits_protect_server(client, function, args):
    response = call(client, function, *args)
    # 10**9 is not a literal, so it is passed as a string and fails with TypeError instead
    data = response.get_json()
    assert data["ok"] is False


def test_huge_int_result_is_described(client):
    data = call(client, "power", "99", "9999").get_json()
    assert data["ok"] is True
    assert data["type"] == "int"
