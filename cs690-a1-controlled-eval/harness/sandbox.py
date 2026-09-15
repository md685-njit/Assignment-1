"""Runner: executes model-written code inside a locked-down Docker container.

This is the "Runner" part of the harness from the Week 2 slide "Putting it
together: your harness": it executes the generated code in a container, with
a time limit and no network access.

Every candidate is code written by a model that nobody has read. Running it
directly on your computer would give it your files, your network, and your
accounts. Instead, run_source starts a fresh container for each candidate,
passes the code and the tests in, and reads one verdict back out. The
container is thrown away afterward.

Inside the container the program harness/docker_entry.py does the actual
running. The Dockerfile in the repository root describes the container image.
ensure_image builds that image automatically the first time it is needed, so
you never run docker build yourself.

Used by harness/grader.py (every experiment attempt), harness/verify.py
(the setup check), and tests/test_sandbox.py.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import shutil
import subprocess
import time

# Name and version of the sandbox image built from the Dockerfile. The runner
# copies this value into every result row.
IMAGE_TAG = "cs690-a1-sandbox:fall2026-v1"


@dataclass(frozen=True)
class SandboxResult:
    """The verdict for one candidate.

    passed            True only if the code ran and every test passed.
    error             None on success, otherwise what went wrong.
    duration_ms       Wall-clock time for the whole container run.
    candidate_stdout  The last part of anything the candidate printed.
    candidate_stderr  The last part of anything written to standard error.
    """

    passed: bool
    error: str | None
    duration_ms: int
    candidate_stdout: str
    candidate_stderr: str


def _repo_root() -> Path:
    """Return the repository root (this file is <root>/harness/sandbox.py)."""
    return Path(__file__).resolve().parents[1]


def _docker() -> str:
    """Return the full path of the docker command, or stop with a clear message."""
    exe = shutil.which("docker")
    if exe is None:
        raise RuntimeError("Docker was not found on PATH.")
    return exe


def ensure_image() -> None:
    """Build the sandbox image if this computer does not have it yet.

    The first build downloads a Python base image and takes a few minutes.
    After that the image is reused and this check returns immediately.
    """
    docker = _docker()
    # "docker image inspect" succeeds only if the image already exists.
    inspected = subprocess.run(
        [docker, "image", "inspect", IMAGE_TAG],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if inspected.returncode == 0:
        return
    # Build from the Dockerfile in the repository root. check=True stops the
    # program with an error if the build fails, for example when Docker
    # Desktop is not running.
    subprocess.run(
        [docker, "build", "--tag", IMAGE_TAG, "."],
        cwd=_repo_root(),
        check=True,
    )


def run_source(source: str, tests: list[str] | tuple[str, ...], timeout_seconds: int = 5) -> SandboxResult:
    """Run candidate source code and its tests in a new container and return the verdict.

    source           the candidate's Python code
    tests            Python statements, usually asserts, run after the code
    timeout_seconds  how long the candidate and its tests may run
    """
    ensure_image()
    docker = _docker()

    # Everything the container needs arrives as one JSON message on its
    # standard input. Nothing from your computer is mounted into it.
    payload = json.dumps(
        {"source": source, "tests": list(tests), "timeout_seconds": timeout_seconds}
    )
    cmd = [
        docker, "run",
        "--rm",                             # delete the container when it exits
        "--interactive",                    # keep standard input open for the payload
        "--network", "none",                # no network access at all
        "--read-only",                      # the container's file system cannot be changed
        "--cap-drop", "ALL",                # drop every special Linux privilege
        "--security-opt", "no-new-privileges",  # code cannot gain privileges later
        "--memory", "192m",                 # memory limit
        "--cpus", "1",                      # at most one CPU core
        "--pids-limit", "64",               # limits how many processes it can start
        # A small scratch folder in memory. noexec means nothing stored there
        # can be run as a program.
        "--tmpfs", "/tmp:rw,nosuid,nodev,noexec,size=32m",
        IMAGE_TAG,
    ]

    started = time.perf_counter()
    # The time limit for the candidate itself is enforced inside the
    # container (see harness/docker_entry.py). The extra 8 seconds here only
    # covers starting and stopping the container.
    completed = subprocess.run(
        cmd,
        input=payload,
        text=True,
        capture_output=True,
        timeout=timeout_seconds + 8,
        check=False,
    )
    duration_ms = int((time.perf_counter() - started) * 1000)

    # A nonzero exit code means the container itself failed, for example it
    # ran out of memory. That counts as a failed candidate.
    if completed.returncode != 0:
        return SandboxResult(
            passed=False,
            error=f"sandbox container exited {completed.returncode}: {completed.stderr[-2000:]}",
            duration_ms=duration_ms,
            candidate_stdout="",
            candidate_stderr=completed.stderr[-4000:],
        )

    # The verdict is the last line the container printed.
    try:
        result = json.loads(completed.stdout.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError) as exc:
        return SandboxResult(
            passed=False,
            error=f"sandbox returned invalid JSON: {exc}",
            duration_ms=duration_ms,
            candidate_stdout=completed.stdout[-4000:],
            candidate_stderr=completed.stderr[-4000:],
        )
    return SandboxResult(
        passed=bool(result.get("passed")),
        error=result.get("error"),
        duration_ms=duration_ms,
        candidate_stdout=result.get("candidate_stdout", ""),
        candidate_stderr=result.get("candidate_stderr", ""),
    )
