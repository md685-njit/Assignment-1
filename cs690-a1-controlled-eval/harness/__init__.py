"""CS 690 Assignment 1: the controlled-evaluation harness.

This package is the harness from the Week 2 lecture: a script that runs an
evaluation the same way every time. Each module is one part of it.

    tasks.py         Problems. Loads the frozen CS690-Eval20 task set and
                     checks that it has not been changed.
    provider.py      Sampler. Sends one request to a model API and returns
                     the answer, the model version, the token usage, and
                     the stop reason.
    sandbox.py       Runner. Starts a locked-down Docker container for each
                     candidate answer.
    docker_entry.py  The small program inside that container. It runs the
                     candidate code and then the task's tests.
    grader.py        Grader. Takes the code out of a model answer and has the
                     sandbox run it against the task's tests.
    metrics.py       Report, scoring. pass@k and the bootstrap interval.
    report.py        Report, saving. Checks and writes each summary file.
    runner.py        Drives all of the above, in order, for both model
                     conditions, and saves every result to disk.
    verify.py        A one-command setup check that needs no API key.

Modules are run from the repository root, for example:

    python -m harness.verify
    python -m harness.runner --config conditions.json --plan
"""
