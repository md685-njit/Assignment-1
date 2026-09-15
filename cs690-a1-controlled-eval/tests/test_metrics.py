"""Specification tests for harness/metrics.py.

Each test states one rule the scoring code must follow, and the comments name
the Week 2 slide the rule comes from. If any of these fail, the numbers in
the summary files cannot be trusted.

    pytest -q tests/test_metrics.py
"""

import math

import pytest

from harness.metrics import aggregate_successes, bootstrap_task_ci, macro_pass_at_k, pass_at_k


def test_pass_at_k_matches_week2_worked_case_and_rejects_naive_form():
    # Slide "pass@k, worked through": 10 attempts, 3 correct, pass@5 = 11/12.
    actual = pass_at_k(10, 3, 5)
    assert actual == pytest.approx(11 / 12, abs=1e-12)
    # Slide "The version people get wrong": the shortcut gives 0.8319.
    # The correct answer must be clearly different from it.
    naive = 1 - (1 - 3 / 10) ** 5
    assert abs(actual - naive) > 0.05


def test_pass_at_k_boundary_cases():
    # No correct attempts: pass@1 is exactly 0.
    assert pass_at_k(5, 0, 1) == 0.0
    # Every attempt correct: pass@1 is exactly 1.
    assert pass_at_k(5, 5, 1) == 1.0
    # One correct attempt out of 5, and you take all 5: you are certain to get it.
    assert pass_at_k(5, 1, 5) == 1.0
    # Any valid input gives a probability between 0 and 1.
    assert 0.0 <= pass_at_k(5, 2, 2) <= 1.0


@pytest.mark.parametrize(
    "args",
    [
        (0, 0, 1),   # no attempts at all
        (3, -1, 1),  # negative number correct
        (3, 4, 1),   # more correct than attempted
        (3, 1, 0),   # k of zero
        (3, 1, 4),   # k larger than the number of attempts
    ],
)
def test_pass_at_k_rejects_invalid_arguments(args):
    # Impossible inputs must raise an error instead of returning a number.
    with pytest.raises(ValueError):
        pass_at_k(*args)


def test_aggregate_successes_groups_candidates_by_task():
    # Six graded attempts, three per task, become one (n, c) pair per task.
    rows = [
        {"task_id": "t1", "passed": True},
        {"task_id": "t1", "passed": False},
        {"task_id": "t1", "passed": True},
        {"task_id": "t2", "passed": False},
        {"task_id": "t2", "passed": False},
        {"task_id": "t2", "passed": True},
    ]
    assert aggregate_successes(rows) == {"t1": (3, 2), "t2": (3, 1)}


def test_aggregate_successes_rejects_malformed_rows():
    # passed must be a real True or False, not the number 1.
    with pytest.raises((TypeError, ValueError, KeyError)):
        aggregate_successes([{"task_id": "t1", "passed": 1}])
    # A row without a task_id cannot be counted.
    with pytest.raises((TypeError, ValueError, KeyError)):
        aggregate_successes([{"passed": True}])


def test_macro_pass_at_k_weights_tasks_equally():
    # One task always passes and one always fails, so the suite score is 0.5.
    counts = {"easy": (3, 3), "hard": (3, 0)}
    assert macro_pass_at_k(counts, 1) == pytest.approx(0.5)
    assert macro_pass_at_k(counts, 2) == pytest.approx(0.5)


def test_task_bootstrap_resamples_tasks_not_candidate_rows():
    # Slide "Where that range comes from": draw whole problems, not attempts.
    # A correct task-level bootstrap over two tasks can draw the always-pass task twice
    # or the always-fail task twice, so its 95 percent percentile interval reaches 0 and 1.
    # Pooling the six individual candidate rows instead produces a materially narrower CI.
    counts = {"always_pass": (3, 3), "always_fail": (3, 0)}
    low, high = bootstrap_task_ci(
        counts,
        1,
        confidence=0.95,
        repetitions=5000,
        seed=690,
    )
    assert low == pytest.approx(0.0, abs=1e-12)
    assert high == pytest.approx(1.0, abs=1e-12)


def test_task_bootstrap_degenerate_case_is_exact():
    # If every task always passes, every pretend suite scores 1.0, so the
    # interval is exactly (1.0, 1.0).
    counts = {"a": (3, 3), "b": (3, 3), "c": (3, 3)}
    assert bootstrap_task_ci(counts, 1, repetitions=1000, seed=690) == pytest.approx((1.0, 1.0))


def test_task_bootstrap_rejects_empty_input_and_bad_parameters():
    # Nothing to resample.
    with pytest.raises(ValueError):
        bootstrap_task_ci({}, 1)
    # A 100 percent interval is not a meaningful setting.
    with pytest.raises(ValueError):
        bootstrap_task_ci({"a": (3, 2)}, 1, confidence=1.0)
    # At least one repetition is needed.
    with pytest.raises(ValueError):
        bootstrap_task_ci({"a": (3, 2)}, 1, repetitions=0)
