"""Problems: loads the frozen CS690-Eval20 task set.

This is the "Problems" part of the harness from the Week 2 slide "Putting it
together: your harness". The 20 tasks live in tasks/cs690_eval20.json. Each
task has four fields:

    id           a label such as "A1-001"
    entry_point  the name of the function the model must write
    prompt       the plain-English description sent to the model
    tests        Python assert statements that decide pass or fail

Two results can only be compared if both were measured on exactly the same
tasks. For that reason load_tasks refuses to run if the task file has changed
in any way, even by one character. It checks this with a SHA-256 fingerprint
of the file's bytes.

The slide asks for the date each problem was published. These tasks were
written for this course, so the version label DATASET_VERSION plays that
role. The runner (harness/runner.py) and the verification command
(harness/verify.py) both begin by calling load_tasks.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path

# Identity of the frozen task set. These values are copied into every result
# row and every summary, so a reader always knows which tasks produced a
# number.
DATASET_ID = "CS690-Eval20"
DATASET_VERSION = "fall2026-v1"
# Fingerprint of tasks/cs690_eval20.json exactly as distributed. Any edit to
# the file produces a different fingerprint.
EXPECTED_SHA256 = "5d84176547cb679f4145676d1f4dfd5061bf3b9600904911da8e5700e82eee3b"
EXPECTED_TASK_COUNT = 20


@dataclass(frozen=True)
class Task:
    """One task from the task file. frozen=True means it cannot be changed after loading."""

    id: str
    entry_point: str
    prompt: str
    tests: tuple[str, ...]


def dataset_path() -> Path:
    """Return the location of tasks/cs690_eval20.json."""
    # This file is <repository root>/harness/tasks.py, so parents[1] is the
    # repository root. The path therefore works from any working directory.
    return Path(__file__).resolve().parents[1] / "tasks" / "cs690_eval20.json"


def dataset_sha256() -> str:
    """Return the SHA-256 fingerprint of the task file as a hex string."""
    return sha256(dataset_path().read_bytes()).hexdigest()


def load_tasks() -> list[Task]:
    """Load, check, and return the 20 frozen tasks in file order.

    Raises RuntimeError if the file's fingerprint, identity, task count, or
    task IDs are not exactly what was distributed.
    """
    # Check 1: the file is byte for byte the distributed file.
    actual_hash = dataset_sha256()
    if actual_hash != EXPECTED_SHA256:
        raise RuntimeError(
            "CS690-Eval20 changed. Restore tasks/cs690_eval20.json "
            "from the original assignment download. "
            f"Expected {EXPECTED_SHA256}, got {actual_hash}."
        )
    payload = json.loads(dataset_path().read_text(encoding="utf-8"))

    # Check 2: the file names the expected task set and version.
    if payload.get("dataset_id") != DATASET_ID or payload.get("version") != DATASET_VERSION:
        raise RuntimeError("Unexpected dataset identifier or version.")

    # Check 3: there are exactly 20 tasks.
    raw_tasks = payload.get("tasks")
    if not isinstance(raw_tasks, list) or len(raw_tasks) != EXPECTED_TASK_COUNT:
        raise RuntimeError(f"Expected exactly {EXPECTED_TASK_COUNT} tasks.")

    # Turn each JSON object into a Task. The tests become a tuple, which
    # cannot be edited later in the run.
    tasks = [
        Task(
            id=item["id"],
            entry_point=item["entry_point"],
            prompt=item["prompt"],
            tests=tuple(item["tests"]),
        )
        for item in raw_tasks
    ]

    # Check 4: no two tasks share an ID. Results are grouped by task ID
    # later, so a duplicate would silently merge two tasks into one.
    if len({t.id for t in tasks}) != EXPECTED_TASK_COUNT:
        raise RuntimeError("Task IDs must be unique.")
    return tasks
