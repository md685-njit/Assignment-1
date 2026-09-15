# Recipe for the sandbox image that runs model-written code.
#
# You never build this yourself. harness/sandbox.py builds it automatically
# the first time it is needed and tags it cs690-a1-sandbox:fall2026-v1.
# The security limits (no network, read-only, memory and CPU caps) are not
# set here. They are applied each time a container starts; see run_source in
# harness/sandbox.py.

# A small official Debian image with Python 3.11.15 installed. The exact
# version is pinned so every student runs candidates on the same Python.
FROM python:3.11.15-slim-bookworm

# Do not write .pyc cache files (the container's disk is read-only anyway),
# and print output immediately instead of buffering it.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Create an ordinary user so candidate code never runs as the administrator
# (root) account inside the container.
RUN useradd --create-home --uid 10001 sandbox
WORKDIR /sandbox

# The only file copied in is the small program that runs a candidate and its
# tests. Nothing else from the repository enters the image.
COPY harness/docker_entry.py /sandbox/docker_entry.py
RUN chown sandbox:sandbox /sandbox/docker_entry.py
USER sandbox

# Every container starts by running that program. It reads the candidate and
# tests from standard input and prints one JSON verdict.
ENTRYPOINT ["python", "/sandbox/docker_entry.py"]
