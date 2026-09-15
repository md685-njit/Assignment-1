"""One-command setup check. Run it before spending any money.

    python -m harness.verify

It needs Docker running but no API key, and it costs nothing. It confirms
that:

1. the 20 frozen tasks load and their fingerprint matches;
2. Python code runs inside the Docker sandbox;
3. that code has no network access;
4. a small run record can be written to results/verification.json.

To test steps 2 and 3 it plays the part of a model. mock_generated_source
below is a pretend model answer that defines a function and also tries to
open a network connection. Two tests then check that the function works,
which proves the code ran, and that the connection failed, which proves the
network is off.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

from .sandbox import run_source
from .tasks import DATASET_ID, EXPECTED_SHA256, dataset_sha256, load_tasks


def main() -> None:
    """Run the four checks, write results/verification.json, and print five OK lines."""
    # Check 1: tasks load. load_tasks stops with an error if the task file
    # was changed.
    tasks = load_tasks()
    if len(tasks) != 20:
        raise RuntimeError("Expected exactly 20 frozen tasks.")

    # Checks 2 and 3: a pretend model answer. It tries to reach a public DNS
    # server. Inside the sandbox that must fail, so NETWORK_BLOCKED ends up True.
    mock_generated_source = (
        "import socket\n"
        "try:\n"
        "    sock = socket.create_connection((\"1.1.1.1\", 53), timeout=0.3)\n"
        "    sock.close()\n"
        "    NETWORK_BLOCKED = False\n"
        "except OSError:\n"
        "    NETWORK_BLOCKED = True\n"
        "\n"
        "def add_one(x):\n"
        "    return x + 1\n"
    )
    tests = [
        "assert add_one(4) == 5",
        "assert NETWORK_BLOCKED is True",
    ]
    # The first call on a new computer also builds the sandbox image, which
    # takes a few minutes.
    result = run_source(mock_generated_source, tests, timeout_seconds=5)
    if not result.passed:
        raise RuntimeError(f"Sandbox verification failed: {result.error}")

    # Check 4: write a small run record. mock_model_metadata shows the shape
    # of the metadata the real experiment records for every attempt.
    repo_root = Path(__file__).resolve().parents[1]
    out = repo_root / "results" / "verification.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "verification_schema": "cs690-a1-verification-v1",
        "verified_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset_id": DATASET_ID,
        "task_count": len(tasks),
        "expected_dataset_sha256": EXPECTED_SHA256,
        "actual_dataset_sha256": dataset_sha256(),
        "generated_code_executed_in_sandbox": True,
        "candidate_network_blocked": True,
        "sandbox_network_mode": "none",
        "mock_model_metadata": {
            "provider": "verification-mock",
            "requested_model": "verification-model",
            "returned_model": "verification-model-v1",
            "temperature": 0.0,
            "top_p": None,
            "seed": 690,
            "effort": None,
            "date": datetime.now(timezone.utc).date().isoformat(),
        },
    }
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    # The five status lines to paste into Part 1 of your report.
    print(f"OK: loaded {len(tasks)} frozen tasks")
    print(f"OK: dataset sha256 {dataset_sha256()}")
    print("OK: generated Python executed in Docker sandbox")
    print("OK: candidate network probe was blocked")
    print("OK: model/configuration metadata written to results/verification.json")


if __name__ == "__main__":
    main()
