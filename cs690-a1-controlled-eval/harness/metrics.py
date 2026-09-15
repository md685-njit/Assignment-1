"""Scoring math for the harness: pass@k and its confidence interval.

This file is the scoring half of the "Report" part of the harness described
in Week 2 ("Putting it together: your harness"). The runner
(harness/runner.py) calls these functions after every attempt for a model
condition has been graded, and harness/report.py saves the numbers they
produce to results/experiment/summary_A.json and summary_B.json.

The four public functions build on each other in this order:

    aggregate_successes  The 60 graded rows for one condition become, for
                         each task, the pair (n attempts, c correct).
    pass_at_k            One task's (n, c) becomes that task's pass@k.
    macro_pass_at_k      The 20 task scores are averaged into one suite score.
    bootstrap_task_ci    The range that suite score could reasonably have
                         landed in, found by redrawing whole tasks.

Week 2 slides that match this file:
    "One run tells you very little" and "pass@k, worked through" (pass_at_k)
    "The version people get wrong" (why pass_at_k uses combinations)
    "One number is still not a result" and "Where that range comes from"
    (bootstrap_task_ci)

The tests in tests/test_metrics.py are the specification for every function
here. Read the two files side by side.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import math
import random

# Maps each task ID to the pair (n, c):
#   n is the number of attempts the model made on that task (3 here)
#   c is how many of those attempts passed every test
TaskCounts = dict[str, tuple[int, int]]


def pass_at_k(n: int, c: int, k: int) -> float:
    """Return the unbiased pass@k estimate for one task.

    n is the number of attempts made, c is how many were correct, and k is
    the number of attempts you are asking about. The result is the chance
    that at least one of k attempts, picked from those n without repeats,
    is correct. This is the estimator from Chen et al. (2021).

    Contract:
    - n must be positive.
    - 0 <= c <= n.
    - 1 <= k <= n.
    - Return a float in [0.0, 1.0].

    Worked example from the Week 2 slides: pass_at_k(10, 3, 5) is 11/12,
    about 0.9167.
    """
    # Reject impossible inputs instead of returning a misleading number.
    if n <= 0:
        raise ValueError(f"n must be positive, got {n}")
    if not 0 <= c <= n:
        raise ValueError(f"c must be between 0 and n={n}, got {c}")
    if not 1 <= k <= n:
        raise ValueError(f"k must be between 1 and n={n}, got {k}")

    # With fewer than k wrong attempts, any k attempts you pick must include
    # a correct one, so the answer is exactly 1.
    if n - c < k:
        return 1.0

    # comb(n - c, k) counts the ways to pick k attempts that are all wrong.
    # comb(n, k) counts all the ways to pick k attempts.
    # Their ratio is the chance that all k are wrong, so pass@k is 1 minus it.
    #
    # The shortcut 1 - (1 - c/n) ** k is wrong because it assumes the same
    # attempt could be picked twice. There are only n distinct attempts, so
    # the count has to use combinations. For n=10, c=3, k=5 the shortcut
    # gives 0.8319 instead of 0.9167.
    return 1.0 - math.comb(n - c, k) / math.comb(n, k)


def aggregate_successes(rows: Sequence[Mapping[str, object]]) -> TaskCounts:
    """Return a mapping from each task_id to (n, c), built from candidate-level result rows.

    Each row is one graded attempt, in the form the runner writes to
    results/experiment/raw_results.jsonl. Each row must contain a string
    task_id and a boolean passed value.

    Grouping by task comes first because every later step treats the task,
    not the single attempt, as the thing being measured.
    """
    counts: TaskCounts = {}
    for row in rows:
        # Square-bracket lookup raises KeyError when a field is missing. That is the
        # intended behavior: a row with no task or no verdict cannot count.
        task_id = row["task_id"]
        passed = row["passed"]
        if not isinstance(task_id, str):
            raise TypeError(f"task_id must be a string, got {task_id!r}")
        if not task_id:
            raise ValueError("task_id must not be empty")
        # Only a real True or False is accepted. A value such as 1 or "yes"
        # means the row did not come from the grader, so it is rejected
        # rather than guessed at.
        if not isinstance(passed, bool):
            raise TypeError(f"passed must be True or False, got {passed!r}")
        n, c = counts.get(task_id, (0, 0))
        counts[task_id] = (n + 1, c + (1 if passed else 0))
    return counts


def macro_pass_at_k(task_counts: Mapping[str, tuple[int, int]], k: int) -> float:
    """Return the unweighted mean task-level pass@k across the frozen task set.

    Every task counts once. This is the suite-level number reported as
    pass_at_1 or pass_at_2 in the summary files.
    """
    if not task_counts:
        raise ValueError("task_counts is empty, so there is nothing to average")
    # Score each task on its own first, then average the task scores.
    per_task = [pass_at_k(n, c, k) for n, c in task_counts.values()]
    return math.fsum(per_task) / len(per_task)


def bootstrap_task_ci(
    task_counts: Mapping[str, tuple[int, int]],
    k: int,
    confidence: float = 0.95,
    repetitions: int = 5000,
    seed: int = 690,
) -> tuple[float, float]:
    """Return a percentile bootstrap CI for macro pass@k.

    The resampling unit is a task. Each replicate draws len(task_counts)
    tasks with replacement. Individual attempts are never pooled or drawn
    on their own. The repetitions and seed arguments are always used as
    given, so the same results always produce the same interval.

    This is the procedure on the Week 2 slide "Where that range comes from":

    1. Build a pretend suite of the same size by drawing whole tasks from
       the real results at random, allowing repeats.
    2. Compute the suite score of that pretend suite and keep it.
    3. Do this `repetitions` times.
    4. Sort the kept scores, cut off the lowest and the highest
       (1 - confidence) / 2 share, and return the two cut points as
       (low, high). With confidence 0.95 that is 2.5 percent at each end.
    """
    if not task_counts:
        raise ValueError("task_counts is empty, so there is nothing to resample")
    if not 0.0 < confidence < 1.0:
        raise ValueError(f"confidence must be strictly between 0 and 1, got {confidence}")
    if repetitions < 1:
        raise ValueError(f"repetitions must be at least 1, got {repetitions}")

    # Score every task once. Sorting the task IDs fixes their order, so the
    # same seed gives the same interval no matter what order the result rows
    # were read in.
    task_ids = sorted(task_counts)
    task_scores = [pass_at_k(*task_counts[task_id], k) for task_id in task_ids]
    suite_size = len(task_scores)

    # A separate random generator with a fixed seed makes the interval
    # repeatable: anyone who reruns these results gets the same numbers.
    rng = random.Random(seed)

    replicate_scores = []
    for _ in range(repetitions):
        # Draw whole tasks with replacement. A task's attempts always travel
        # together, because attempts on the same task are not independent of
        # each other. Drawing attempts one at a time would make the interval
        # look far narrower than the evidence supports.
        pretend_suite = rng.choices(task_scores, k=suite_size)
        # The suite score is the mean of the task scores, which is exactly
        # what macro_pass_at_k computes.
        replicate_scores.append(math.fsum(pretend_suite) / suite_size)

    replicate_scores.sort()
    tail = (1.0 - confidence) / 2.0
    return (
        _percentile(replicate_scores, tail),
        _percentile(replicate_scores, 1.0 - tail),
    )


def _percentile(sorted_values: Sequence[float], fraction: float) -> float:
    """Return the value found at `fraction` (0 to 1) of an already sorted list.

    Uses linear interpolation between the two nearest positions. This is the
    same rule as the default in NumPy and PERCENTILE.INC in Excel, so the
    result can be checked with either.
    """
    position = fraction * (len(sorted_values) - 1)
    lower = math.floor(position)
    upper = math.ceil(position)
    weight = position - lower
    return sorted_values[lower] + (sorted_values[upper] - sorted_values[lower]) * weight
