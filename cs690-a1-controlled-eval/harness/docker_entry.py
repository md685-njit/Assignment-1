"""The program that runs inside the Docker sandbox.

The Dockerfile copies this one file into the sandbox image, and
harness/sandbox.py starts a fresh container for every candidate answer.
Inside the container this script:

1. reads one JSON message from standard input with the candidate's source
   code, the task's test statements, and the time limit;
2. runs the candidate code, which defines the function the task asked for;
3. runs each test statement, in order, against that function;
4. prints exactly one line of JSON saying whether everything passed.

No exception is allowed to escape. An error, a failed assertion, or running
past the time limit is reported as "passed": false with a description, so the
harness always gets a verdict it can record.

Running model-written code with exec() would be unsafe on your own computer.
It is acceptable here only because this script runs inside the locked-down
container that harness/sandbox.py starts.
"""

from __future__ import annotations

import contextlib
import io
import json
import signal
import sys
import traceback


def expect_raises(exc_type, fn, *args, **kwargs):
    """Test helper: succeed only if fn(*args, **kwargs) raises exc_type.

    Several task tests use it, for example
        expect_raises(ValueError, chunked, [1], 0)
    It is made available to the candidate and the tests through the shared
    namespace set up in main.
    """
    try:
        fn(*args, **kwargs)
    except exc_type:
        return
    except BaseException as exc:
        raise AssertionError(
            f"expected {exc_type.__name__}, got {type(exc).__name__}: {exc}"
        ) from exc
    raise AssertionError(f"expected {exc_type.__name__} to be raised")


def _timeout_handler(signum, frame):
    """Called when the alarm set in main goes off. Stops the candidate with an error."""
    raise TimeoutError("candidate execution exceeded wall-clock limit")


def main() -> int:
    """Run one candidate and its tests, print the verdict as JSON, and return 0."""
    payload = json.load(sys.stdin)
    source = payload["source"]
    tests = payload["tests"]
    timeout_seconds = int(payload.get("timeout_seconds", 5))

    # Anything the candidate prints is captured here instead of going to the
    # real output, so it cannot get mixed into the JSON verdict.
    stdout_buffer = io.StringIO()
    stderr_buffer = io.StringIO()

    # The candidate and the tests share one namespace, so the tests can call
    # the function the candidate defined.
    namespace = {"expect_raises": expect_raises}

    # Ask the operating system for an alarm signal after timeout_seconds.
    # This limit covers the candidate code and all of its tests together.
    signal.signal(signal.SIGALRM, _timeout_handler)
    signal.alarm(max(1, timeout_seconds))

    try:
        with contextlib.redirect_stdout(stdout_buffer), contextlib.redirect_stderr(stderr_buffer):
            # Step 2: run the candidate code, which defines its function.
            exec(compile(source, "candidate.py", "exec"), namespace, namespace)
            # Step 3: run each test. The first failure stops the run, and the
            # message names the test that failed.
            for index, test in enumerate(tests, start=1):
                try:
                    exec(compile(test, f"test_{index}.py", "exec"), namespace, namespace)
                except BaseException as exc:
                    raise AssertionError(f"test {index} failed: {test}: {exc}") from exc
        result = {
            "passed": True,
            "error": None,
            "candidate_stdout": stdout_buffer.getvalue()[-4000:],
            "candidate_stderr": stderr_buffer.getvalue()[-4000:],
        }
    except BaseException as exc:
        # BaseException also catches the TimeoutError from the alarm and a
        # candidate that calls sys.exit().
        result = {
            "passed": False,
            "error": f"{type(exc).__name__}: {exc}",
            "traceback": traceback.format_exc(limit=8)[-8000:],
            "candidate_stdout": stdout_buffer.getvalue()[-4000:],
            "candidate_stderr": stderr_buffer.getvalue()[-4000:],
        }
    finally:
        # Cancel the alarm whether or not the candidate finished.
        signal.alarm(0)

    # Step 4: the verdict, on one line.
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
