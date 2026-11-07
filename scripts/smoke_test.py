"""Smoke test for the live deployment.

Usage:  python scripts/smoke_test.py <BASE_URL> <EXPECTED_SHA> [timeout_seconds]

1. Polls <BASE_URL>/health until it reports EXPECTED_SHA (the new deploy is live).
2. Runs three live requests and checks the answers:
     - GET  /            page loads and shows the deployed SHA
     - POST /api/call    divide(10, 4) == 2.5
     - POST /api/call    divide(1, 0)  -> ZeroDivisionError
Exits with status 1 on any failure. Uses only the standard library.
"""

import json
import sys
import time
import urllib.error
import urllib.request


def request(url, data=None):
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json", "User-Agent": "smoke-test"},
        method="POST" if body else "GET",
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.status, response.read().decode()


def wait_for_sha(base, expected, timeout):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            _, body = request(f"{base}/health")
            live_sha = json.loads(body).get("sha", "")
            print(f"live sha: {live_sha[:7]}  expected: {expected[:7]}")
            if live_sha == expected:
                return True
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            print(f"health not ready: {exc}")
        time.sleep(15)
    return False


def check(label, condition):
    print(("PASS " if condition else "FAIL ") + label)
    return condition


def main():
    base = sys.argv[1].rstrip("/")
    expected = sys.argv[2]
    timeout = int(sys.argv[3]) if len(sys.argv) > 3 else 900

    if not wait_for_sha(base, expected, timeout):
        print(f"FAIL: {base} never reported sha {expected} within {timeout}s")
        sys.exit(1)

    results = []

    status, html = request(f"{base}/")
    results.append(
        check("GET / returns 200 and shows the deployed SHA", status == 200 and expected in html)
    )

    _, body = request(f"{base}/api/call", {"function": "divide", "args": ["10", "4"]})
    data = json.loads(body)
    results.append(
        check("divide(10, 4) == 2.5", data.get("ok") is True and data.get("result") == "2.5")
    )

    _, body = request(f"{base}/api/call", {"function": "divide", "args": ["1", "0"]})
    data = json.loads(body)
    results.append(
        check(
            "divide(1, 0) raises ZeroDivisionError", data.get("error_type") == "ZeroDivisionError"
        )
    )

    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
