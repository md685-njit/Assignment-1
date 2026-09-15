"""Tests for the Docker sandbox in harness/sandbox.py.

These need Docker installed and running. If the docker command is not found,
pytest skips them and reports "2 skipped". A skip is not a pass: start Docker
and run the tests again before you rely on the harness.

    pytest -q tests/test_sandbox.py
"""

import shutil

import pytest

from harness.sandbox import run_source

# Skip every test in this file when Docker is not installed.
pytestmark = pytest.mark.skipif(shutil.which("docker") is None, reason="Docker is required for sandbox tests")


def test_candidate_executes_in_sandbox():
    # A tiny correct candidate must run in the container and pass its test.
    result = run_source("def add(a, b):\n    return a + b\n", ["assert add(2, 3) == 5"])
    assert result.passed, result.error


def test_candidate_network_is_disabled():
    # Candidate code must not be able to open a network connection.
    source = """
import socket

def network_is_blocked():
    try:
        s = socket.create_connection(("1.1.1.1", 53), timeout=0.3)
        s.close()
        return False
    except OSError:
        return True
"""
    result = run_source(source, ["assert network_is_blocked() is True"])
    assert result.passed, result.error
