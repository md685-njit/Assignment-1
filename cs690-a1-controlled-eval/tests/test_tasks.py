"""Tests for the frozen task set loaded by harness/tasks.py.

    pytest -q tests/test_tasks.py
"""

from harness.tasks import DATASET_ID, EXPECTED_SHA256, dataset_sha256, load_tasks


def test_frozen_dataset_identity_and_count():
    # The task file is the distributed one: right name, 20 tasks, matching
    # fingerprint, and no repeated IDs.
    tasks = load_tasks()
    assert DATASET_ID == "CS690-Eval20"
    assert len(tasks) == 20
    assert dataset_sha256() == EXPECTED_SHA256
    assert len({task.id for task in tasks}) == 20


def test_each_task_has_prompt_entry_point_and_multiple_tests():
    # Every task names its function, describes it, and has at least four
    # tests. Thin test suites let wrong answers pass (Week 2, "What happens
    # when you add the missing tests").
    for task in load_tasks():
        assert task.entry_point
        assert task.prompt.strip()
        assert len(task.tests) >= 4
