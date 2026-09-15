"""Grader: turns a model's answer into a pass or fail verdict.

This is the "Grader" part of the harness from the Week 2 slide "Putting it
together: your harness". It does two small jobs for the runner
(harness/runner.py):

1. extract_python takes the Python code out of the model's answer text.
   The prompt asks for bare code, but models sometimes wrap it in a
   Markdown fence anyway, so both forms are handled.
2. grade_candidate runs that code against the task's own tests, unchanged,
   inside the Docker sandbox (harness/sandbox.py).

The verdict is pass or fail with no partial credit, the same rule used by
the benchmarks discussed in Week 2.
"""

from __future__ import annotations

import re

from .sandbox import SandboxResult, run_source
from .tasks import Task

# Matches a Markdown code block: three backticks, optionally the word python,
# the code itself, and three closing backticks.
# DOTALL lets the block span several lines. IGNORECASE also accepts ```Python.
_FENCE = re.compile(r"```(?:python)?\s*(.*?)```", re.IGNORECASE | re.DOTALL)


def extract_python(text: str) -> str:
    """Extract a single fenced Python block when present, otherwise return stripped text.

    Only the first fenced block is used. The result always ends with a
    newline.
    """
    match = _FENCE.search(text)
    if match:
        return match.group(1).strip() + "\n"
    return text.strip() + "\n"


def grade_candidate(source: str, task: Task, timeout_seconds: int) -> SandboxResult:
    """Run one candidate against its task's tests in the sandbox and return the verdict.

    The result's passed field is True only if the code ran and every test
    passed within the time limit.
    """
    return run_source(source, task.tests, timeout_seconds=timeout_seconds)
