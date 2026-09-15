"""Specification tests for harness/report.py.

They check that a summary file is written exactly as given and that a
summary with a missing or extra field is refused.

    pytest -q tests/test_report.py
"""

import json

import pytest

from harness.report import REQUIRED_KEYS, SUMMARY_SCHEMA_VERSION, write_summary


def valid_summary():
    """Return a correctly shaped summary with made-up values."""
    return {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "experiment_id": "exp",
        "condition_id": "A",
        "provider": "test",
        "requested_model": "m",
        "returned_models": ["m-v1"],
        "dataset": {"id": "CS690-Eval20", "version": "fall2026-v1", "sha256": "abc", "task_count": 20},
        "samples_per_task": 3,
        "candidate_count": 60,
        "pass_at_1": 0.5,
        "pass_at_2": 0.7,
        "ci95_pass_at_1": [0.3, 0.7],
        "input_tokens": 100,
        "output_tokens": 200,
        "cost_usd": None,
    }


def test_write_summary_round_trip(tmp_path):
    # Writing into a folder that does not exist yet must work, and reading
    # the file back must give exactly the same data.
    summary = valid_summary()
    path = tmp_path / "nested" / "summary.json"
    write_summary(summary, path)
    assert path.exists()
    assert json.loads(path.read_text(encoding="utf-8")) == summary


def test_write_summary_rejects_missing_or_extra_keys(tmp_path):
    # A missing field would leave a hole in the report table.
    missing = valid_summary()
    missing.pop("pass_at_2")
    with pytest.raises(ValueError):
        write_summary(missing, tmp_path / "missing.json")

    # An extra field would be a number nobody documented.
    extra = valid_summary()
    extra["unexpected"] = 1
    with pytest.raises(ValueError):
        write_summary(extra, tmp_path / "extra.json")


def test_required_key_contract_is_exact():
    # The example above and the official key list must agree exactly.
    assert set(valid_summary()) == REQUIRED_KEYS
