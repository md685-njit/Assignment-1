"""Writes the summary file for one model condition.

This is the last step of the harness and the saving half of its "Report"
part. After the runner (harness/runner.py) has graded all 60 attempts for a
condition and scored them with harness/metrics.py, it hands a dictionary of
results to write_summary, which saves it as
results/experiment/summary_A.json or results/experiment/summary_B.json.

Those two files are where the numbers in your report table come from. The set
of keys is fixed, so every summary carries every field the table needs and
nothing the table does not explain.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

# Layout label stored inside every summary, so a reader can tell which
# version of this format the file follows.
SUMMARY_SCHEMA_VERSION = "cs690-a1-summary-v1"

# The exact set of fields every summary must contain.
REQUIRED_KEYS = {
    "schema_version",   # always SUMMARY_SCHEMA_VERSION
    "experiment_id",    # copied from conditions.json
    "condition_id",     # "A" or "B"
    "provider",         # whose API was called, for example "openai"
    "requested_model",  # the model name the harness asked for
    "returned_models",  # the version strings the API reported back
    "dataset",          # task set ID, version, fingerprint, and task count
    "samples_per_task", # attempts per task (3)
    "candidate_count",  # attempts graded for this condition (60)
    "pass_at_1",        # primary score
    "pass_at_2",        # secondary score
    "ci95_pass_at_1",   # [low, high] task-level bootstrap interval for pass@1
    "input_tokens",     # total prompt tokens, or null if any were not reported
    "output_tokens",    # total answer tokens, or null if any were not reported
    "cost_usd",         # always null here: the harness records tokens, not dollars
}


def write_summary(summary: Mapping[str, Any], path: Path) -> None:
    """Validate the supplied summary schema and write UTF-8 JSON to path.

    Raises ValueError if the summary has a missing or unexpected key, if its
    schema_version is wrong, or if a value cannot be written as standard JSON
    (for example NaN). The parent directory is created when needed.
    """
    keys = set(summary)
    if keys != REQUIRED_KEYS:
        missing = sorted(REQUIRED_KEYS - keys)
        unexpected = sorted(keys - REQUIRED_KEYS)
        raise ValueError(
            f"summary keys do not match the schema: missing={missing}, unexpected={unexpected}"
        )
    if summary["schema_version"] != SUMMARY_SCHEMA_VERSION:
        raise ValueError(
            f"schema_version must be {SUMMARY_SCHEMA_VERSION!r}, "
            f"got {summary['schema_version']!r}"
        )

    # Build the text before touching the disk, so a value that cannot be
    # written never leaves a half-written file behind. Sorted keys and
    # indentation make the file easy to read and easy to compare between
    # runs. allow_nan=False rejects NaN and infinity, which are not valid JSON.
    text = json.dumps(dict(summary), indent=2, sort_keys=True, allow_nan=False) + "\n"

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
