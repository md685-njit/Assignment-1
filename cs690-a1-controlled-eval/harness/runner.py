"""Runs the controlled comparison from start to finish.

This is the main program of the harness. It connects the other modules in
the order the Week 2 slide "Putting it together: your harness" describes:

    tasks.py      load the 20 frozen problems
    provider.py   ask the model for an answer (the sampler)
    grader.py     take the code out of the answer and have
    sandbox.py    run it against the tests in a locked container
    metrics.py    turn pass/fail rows into pass@1, pass@2, and an interval
    report.py     save one summary file per condition

Usage, from the repository root:

    python -m harness.runner --config conditions.json --plan
        Prints what would run, 20 x 3 x 2 = 120 generations. No API calls.

    python -m harness.runner --config conditions.json
        Runs the experiment and writes:
            prompts/<experiment_id>/<condition>/<task>.txt   exact prompts
            results/experiment/manifest.json                 what was run
            results/experiment/raw_results.jsonl             one row per attempt
            results/experiment/candidates/                   every answer
            results/experiment/summary_A.json, summary_B.json

The run is resumable. Every finished attempt is written to
raw_results.jsonl immediately. If the run stops partway, running the same
command again skips everything already recorded and pays only for what is
missing.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import time
from typing import Any

from .grader import extract_python, grade_candidate
from .metrics import aggregate_successes, bootstrap_task_ci, macro_pass_at_k
from .provider import Condition, provider_for
from .report import SUMMARY_SCHEMA_VERSION, write_summary
from .sandbox import IMAGE_TAG
from .tasks import DATASET_ID, DATASET_VERSION, dataset_sha256, load_tasks

# The one prompt template used for every request in both conditions. Only
# {task_prompt} changes from task to task. Keeping the wording fixed is part
# of what makes the comparison controlled.
PROMPT_TEMPLATE = """You are being evaluated on a frozen Python programming task.
Implement exactly the requested function using only the Python standard library.
Do not read files, access the network, or perform input/output.
Return only the complete Python function definition and any standard-library imports it requires.
Do not return tests, Markdown fences, or explanations.

Task:
{task_prompt}
"""


def _sha_text(text: str) -> str:
    """Return the SHA-256 fingerprint of a string."""
    return sha256(text.encode("utf-8")).hexdigest()


def _load_config(path: Path) -> dict[str, Any]:
    """Read conditions.json and refuse to continue unless every control is at its fixed value.

    These checks are what keep every student's experiment identical. If any
    value is changed, the runner stops before spending anything.
    """
    cfg = json.loads(path.read_text(encoding="utf-8"))
    if cfg.get("samples_per_task") != 3:
        raise ValueError("A1 requires exactly 3 samples per task.")
    if cfg.get("k_values") != [1, 2]:
        raise ValueError("A1 requires k_values [1, 2].")
    if cfg.get("confidence") != 0.95:
        raise ValueError("A1 requires a 0.95 confidence interval.")
    if cfg.get("bootstrap_repetitions") != 5000:
        raise ValueError("A1 requires exactly 5000 bootstrap repetitions.")
    if cfg.get("bootstrap_seed") != 690:
        raise ValueError("A1 requires bootstrap_seed 690.")
    if cfg.get("timeout_seconds") != 5:
        raise ValueError("A1 requires a 5-second sandbox timeout.")

    # Exactly two conditions, A and B.
    conditions = cfg.get("conditions")
    if not isinstance(conditions, list) or len(conditions) != 2:
        raise ValueError("A1 requires exactly two model conditions.")
    parsed = [Condition(**item) for item in conditions]

    # Both conditions must use the same sampling settings, so the model is
    # the only difference between them.
    if parsed[0].sampling_signature() != parsed[1].sampling_signature():
        raise ValueError("Both conditions must use the same sampling configuration.")
    # The shared settings are also fixed: (temperature, top_p, seed, effort,
    # max_output_tokens).
    required_sampling = (1.0, None, None, "none", 800)
    if parsed[0].sampling_signature() != required_sampling:
        raise ValueError(
            "A1 controls are fixed: temperature 1.0, top_p null, seed null, "
            "effort 'none', and max_output_tokens 800."
        )
    # Keep the parsed conditions alongside the raw settings for run() to use.
    cfg["_conditions"] = parsed
    return cfg


def _manifest_payload(cfg: dict[str, Any], config_path: Path) -> dict[str, Any]:
    """Describe exactly what this experiment is: which config and which task set."""
    public_cfg = {k: v for k, v in cfg.items() if k != "_conditions"}
    return {
        "experiment_id": cfg["experiment_id"],
        "dataset_id": DATASET_ID,
        "dataset_version": DATASET_VERSION,
        "dataset_sha256": dataset_sha256(),
        # Fingerprint of the configuration. Any changed setting changes it.
        "config_sha256": _sha_text(json.dumps(public_cfg, sort_keys=True)),
        "config_path": str(config_path),
    }


def _prepare_manifest(out_dir: Path, manifest: dict[str, Any]) -> None:
    """Write manifest.json, or check that an existing one matches this run.

    This prevents mixing results from two different configurations in one
    results folder, which would make every number in it meaningless.
    """
    path = out_dir / "manifest.json"
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        if existing != manifest:
            raise RuntimeError(
                "Experiment configuration changed after results were written. "
                "Restore the original configuration or use a new clean directory."
            )
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _load_existing(path: Path) -> dict[tuple[str, str, int], dict[str, Any]]:
    """Read the rows already in raw_results.jsonl, keyed by (condition, task, sample).

    This is what makes the run resumable: any attempt found here is skipped.
    """
    rows: dict[tuple[str, str, int], dict[str, Any]] = {}
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        key = (row["condition_id"], row["task_id"], int(row["sample_index"]))
        rows[key] = row
    return rows


def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
    """Add one row to the end of a JSON Lines file (one JSON object per line).

    The file is flushed right away, so an interruption loses at most the
    attempt that was in progress.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")
        handle.flush()


def _save_prompt(root: Path, condition_id: str, task_id: str, prompt: str) -> Path:
    """Save the exact prompt text sent for one task, and return where it was saved.

    If a saved prompt already exists and differs, the run stops, because the
    earlier results were produced by a different prompt.
    """
    path = root / condition_id / f"{task_id}.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text(encoding="utf-8") != prompt:
        raise RuntimeError(f"Prompt changed after being recorded: {path}")
    path.write_text(prompt, encoding="utf-8")
    return path


def _save_candidate(
    root: Path,
    condition_id: str,
    task_id: str,
    sample_index: int,
    source: str,
    raw_text: str,
) -> tuple[Path, Path]:
    """Save one attempt twice: the extracted code (.py) and the full answer text (.raw.txt).

    Keeping the raw answer means anyone can check that the code was
    extracted correctly.
    """
    source_path = root / condition_id / task_id / f"sample_{sample_index}.py"
    raw_path = root / condition_id / task_id / f"sample_{sample_index}.raw.txt"
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text(source, encoding="utf-8")
    raw_path.write_text(raw_text, encoding="utf-8")
    return source_path, raw_path


def _generate_with_retry(provider, prompt: str, condition: Condition, attempts: int = 3):
    """Call the API, retrying up to three times with a short wait between tries.

    Temporary network or server errors are common. If every try fails, the
    run stops with the last error, and rerunning the command resumes it.
    """
    last_exc = None
    for attempt in range(1, attempts + 1):
        try:
            return provider.generate(prompt, condition)
        except Exception as exc:
            last_exc = exc
            if attempt == attempts:
                break
            # Wait 2 seconds after the first failure, 4 after the second.
            time.sleep(attempt * 2)
    raise RuntimeError(f"API generation failed after {attempts} attempts: {last_exc}") from last_exc


def _sum_optional(rows: list[dict[str, Any]], key: str) -> int | None:
    """Add up a token count across rows, or return None if any row lacks it.

    A total built from only some of the rows would look complete while
    being too small, so it is not reported at all.
    """
    values = [row.get(key) for row in rows]
    ints = [value for value in values if isinstance(value, int)]
    if len(ints) != len(values):
        return None
    return sum(ints)


def _summarize(cfg: dict[str, Any], condition: Condition, rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Turn the 60 rows for one condition into its summary dictionary."""
    # 60 rows become 20 (n, c) pairs, one per task.
    task_counts = aggregate_successes(rows)
    # The primary score and the secondary score.
    p1 = macro_pass_at_k(task_counts, 1)
    p2 = macro_pass_at_k(task_counts, 2)
    # The 95 percent task-level interval for pass@1, with the fixed
    # repetition count and seed from conditions.json.
    low, high = bootstrap_task_ci(
        task_counts,
        1,
        confidence=cfg["confidence"],
        repetitions=cfg["bootstrap_repetitions"],
        seed=cfg["bootstrap_seed"],
    )
    # Every distinct version string the API reported for this condition.
    returned_models = sorted({row["returned_model"] for row in rows if row.get("returned_model")})
    return {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "experiment_id": cfg["experiment_id"],
        "condition_id": condition.id,
        "provider": condition.provider,
        "requested_model": condition.model,
        "returned_models": returned_models,
        "dataset": {
            "id": DATASET_ID,
            "version": DATASET_VERSION,
            "sha256": dataset_sha256(),
            "task_count": 20,
        },
        "samples_per_task": cfg["samples_per_task"],
        "candidate_count": len(rows),
        "pass_at_1": p1,
        "pass_at_2": p2,
        "ci95_pass_at_1": [low, high],
        "input_tokens": _sum_optional(rows, "input_tokens"),
        "output_tokens": _sum_optional(rows, "output_tokens"),
        # The API reports tokens, not dollars. Take the dollar amount from
        # your provider's usage page and write it in your report and ledger.
        "cost_usd": None,
    }


def run(config_path: Path, plan_only: bool) -> None:
    """Run the whole experiment, or with plan_only=True just print the plan."""
    cfg = _load_config(config_path)
    tasks = load_tasks()
    conditions: list[Condition] = cfg["_conditions"]
    total_calls = len(tasks) * cfg["samples_per_task"] * len(conditions)

    # The plan. Printed on every run, so the console log shows what ran.
    print(f"dataset: {DATASET_ID} ({len(tasks)} tasks)")
    print(f"dataset sha256: {dataset_sha256()}")
    print(f"conditions: {conditions[0].id}={conditions[0].model}, {conditions[1].id}={conditions[1].model}")
    print(f"samples per task: {cfg['samples_per_task']}")
    print(f"planned candidate generations: {len(tasks)} x {cfg['samples_per_task']} x {len(conditions)} = {total_calls}")
    if plan_only:
        # Stop before any provider is created, so no key is needed and
        # nothing is spent.
        print("plan only: no API requests were made")
        return

    # Where everything is written.
    repo_root = Path(__file__).resolve().parents[1]
    out_dir = repo_root / "results" / "experiment"
    prompt_root = repo_root / "prompts" / cfg["experiment_id"]
    candidate_root = out_dir / "candidates"
    raw_path = out_dir / "raw_results.jsonl"

    manifest = _manifest_payload(cfg, config_path)
    _prepare_manifest(out_dir, manifest)
    existing = _load_existing(raw_path)

    # The main loop: condition A then B, each of the 20 tasks, 3 attempts
    # per task.
    for condition in conditions:
        provider = provider_for(condition.provider)
        for task in tasks:
            prompt = PROMPT_TEMPLATE.format(task_prompt=task.prompt)
            prompt_path = _save_prompt(prompt_root, condition.id, task.id, prompt)
            for sample_index in range(1, cfg["samples_per_task"] + 1):
                key = (condition.id, task.id, sample_index)
                if key in existing:
                    # Already recorded in an earlier run. Skip it and pay nothing.
                    continue

                # Sampler: one request to the model.
                generation = _generate_with_retry(provider, prompt, condition)
                # Grader, part 1: take the code out of the answer.
                source = extract_python(generation.text)
                candidate_path, raw_response_path = _save_candidate(
                    candidate_root,
                    condition.id,
                    task.id,
                    sample_index,
                    source,
                    generation.text,
                )
                # Grader, part 2, and runner: execute it against the tests
                # in the sandbox.
                grade = grade_candidate(source, task, timeout_seconds=cfg["timeout_seconds"])

                # The run record for this attempt. These are the fields from
                # the Week 2 slides "A model name is not enough" and "What a
                # run record has to contain", plus the verdict.
                now = datetime.now(timezone.utc).isoformat()
                row = {
                    "experiment_id": cfg["experiment_id"],
                    "condition_id": condition.id,
                    "task_id": task.id,
                    "sample_index": sample_index,
                    "provider": condition.provider,
                    "requested_model": condition.model,
                    "returned_model": generation.returned_model,
                    "temperature": condition.temperature,
                    "top_p": condition.top_p,
                    "seed": condition.seed,
                    "effort": condition.effort,
                    "max_output_tokens": condition.max_output_tokens,
                    "run_date_utc": now,
                    "dataset_id": DATASET_ID,
                    "dataset_version": DATASET_VERSION,
                    "dataset_sha256": dataset_sha256(),
                    "prompt_sha256": _sha_text(prompt),
                    "prompt_path": str(prompt_path.relative_to(repo_root)),
                    "candidate_path": str(candidate_path.relative_to(repo_root)),
                    "raw_response_path": str(raw_response_path.relative_to(repo_root)),
                    "sandbox_image": IMAGE_TAG,
                    "sandbox_network": "none",
                    "timeout_seconds": cfg["timeout_seconds"],
                    "passed": grade.passed,
                    "error": grade.error,
                    "duration_ms": grade.duration_ms,
                    "stop_reason": generation.stop_reason,
                    "input_tokens": generation.input_tokens,
                    "output_tokens": generation.output_tokens,
                    "total_tokens": generation.total_tokens,
                }
                _append_jsonl(raw_path, row)
                existing[key] = row
                status = "PASS" if grade.passed else "FAIL"
                print(f"{condition.id} {task.id} sample {sample_index}: {status}")

    # Report: check that each condition is complete, then score it and save
    # its summary.
    all_rows = list(existing.values())
    for condition in conditions:
        rows = [row for row in all_rows if row["condition_id"] == condition.id]
        expected = len(tasks) * cfg["samples_per_task"]
        if len(rows) != expected:
            raise RuntimeError(f"Condition {condition.id} has {len(rows)} rows; expected {expected}.")
        summary = _summarize(cfg, condition, rows)
        write_summary(summary, out_dir / f"summary_{condition.id}.json")

    print(f"complete: {len(all_rows)} candidate rows")
    print(f"raw results: {raw_path.relative_to(repo_root)}")
    print("summaries: results/experiment/summary_A.json, results/experiment/summary_B.json")


def main() -> None:
    """Read the command-line options and start the run."""
    parser = argparse.ArgumentParser(description="Run the CS 690 A1 controlled comparison.")
    parser.add_argument("--config", type=Path, default=Path("conditions.json"),
                        help="experiment configuration file (default: conditions.json)")
    parser.add_argument("--plan", action="store_true",
                        help="print the plan and exit without calling any API")
    args = parser.parse_args()
    run(args.config, args.plan)


if __name__ == "__main__":
    main()
