#!/usr/bin/env python3
"""Run the application eval suite against the actual consumer and producer."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import time

import judge_validation as validation


APP_DIR = Path(__file__).resolve().parent
CONSUMER_TIMEOUT_SECONDS = 10


def read_cases(path):
    data = path.read_bytes()
    cases = json.loads(data)
    if not isinstance(cases, list) or not cases:
        raise ValueError("application suite must be a nonempty JSON array")
    ids = set()
    for index, case in enumerate(cases, 1):
        if (
            not isinstance(case, dict)
            or set(case) != {"id", "a", "b"}
            or not isinstance(case.get("id"), str)
            or not case["id"]
            or case["id"] in ids
            or any(type(case.get(key)) is not int or not 0 <= case[key] <= 9
                   for key in ("a", "b"))
        ):
            raise ValueError(
                f"suite case {index}: expected a unique nonempty id and integer "
                "a and b (0..9), with no other fields"
            )
        ids.add(case["id"])
    return cases, hashlib.sha256(data).hexdigest()


def evaluate_case(index, case, judge):
    started = time.monotonic()
    command = [str(APP_DIR / "consumer"), "sum", str(case["a"]), str(case["b"])]
    record = {
        "type": "result", "case": index, "case_id": case["id"],
        "a": case["a"], "b": case["b"],
        "expected_sum": case["a"] + case["b"],
        "expected_verdict": "ACCEPT", "test_status": "error",
        "consumer_command": command,
    }
    try:
        result = subprocess.run(
            command, capture_output=True, timeout=CONSUMER_TIMEOUT_SECONDS,
            check=False,
        )
        record["consumer_exit_status"] = result.returncode
        record["response"] = result.stdout.decode("utf-8")
        record["consumer_stderr"] = result.stderr.decode("utf-8")
        if result.returncode != 0:
            raise RuntimeError(f"consumer exited with status {result.returncode}")
    except (OSError, subprocess.TimeoutExpired, UnicodeError, RuntimeError) as error:
        record.update(status="consumer_error", verdict=None, error=str(error))
        if isinstance(error, subprocess.TimeoutExpired):
            record["consumer_stdout_hex"] = (error.stdout or b"").hex()
            record["consumer_stderr_hex"] = (error.stderr or b"").hex()
        elif isinstance(error, UnicodeError):
            record["consumer_stdout_hex"] = result.stdout.hex()
            record["consumer_stderr_hex"] = result.stderr.hex()
    else:
        try:
            record.update(judge.evaluate(record["expected_sum"], record["response"]))
        except Exception as error:
            record.update(status="evaluator_error", verdict=None, error=str(error))
        if record["status"] == "judged":
            record["test_status"] = "passed" if record["verdict"] == "ACCEPT" else "failed"
    record["elapsed_seconds"] = round(time.monotonic() - started, 4)
    return record


def run(reporter):
    emit = reporter.emit
    suite_path = APP_DIR / "eval_cases.json"
    try:
        cases, suite_digest = read_cases(suite_path)
        artifacts = {
            "eval.py": Path(__file__),
            "judge_validation.py": Path(validation.__file__),
            **{name: APP_DIR / name for name in ("consumer", "consumer.py", "producer")},
        }
        checksums = {name: hashlib.sha256(path.read_bytes()).hexdigest()
                     for name, path in artifacts.items()}
    except (ValueError, OSError) as error:
        emit({"type": "error", "stage": "input", "error": str(error)})
        return 2

    emit({
        "type": "run", "started_at": datetime.now(timezone.utc).isoformat(),
        "source": "consumer_suite", "case_count": len(cases),
        "suite_file": suite_path.name, "suite_sha256": suite_digest,
        "cases": cases, "repetitions": 1,
        "python": platform.python_version(), "python_executable": sys.executable,
        "platform": platform.platform(),
        "model": validation.MODEL_ID, "api_endpoint": validation.API_ENDPOINT,
        "temperature": validation.TEMPERATURE, "top_p": validation.TOP_P,
        "seed": validation.SEED, "max_completion_tokens": validation.MAX_NEW_TOKENS,
        "judging_instruction": validation.JUDGING_INSTRUCTION,
        "consumer_timeout_seconds": CONSUMER_TIMEOUT_SECONDS,
        "script_sha256": checksums["eval.py"], "artifact_sha256": checksums,
    })
    try:
        judge = validation.Judge()
    except Exception as error:
        emit({"type": "error", "stage": "model_setup", "error": str(error)})
        return 2
    emit({"type": "environment", **judge.versions})

    counts = {
        "accept": 0, "reject": 0, "passed": 0, "failed": 0,
        "evaluator_errors": 0, "consumer_errors": 0,
    }
    for index, case in enumerate(cases, 1):
        record = evaluate_case(index, case, judge)
        if record["status"] == "consumer_error":
            counts["consumer_errors"] += 1
        elif record["status"] == "evaluator_error":
            counts["evaluator_errors"] += 1
        else:
            counts[record["verdict"].lower()] += 1
            counts[record["test_status"]] += 1
        emit(record)

    exit_status = (
        2 if counts["evaluator_errors"] or counts["consumer_errors"]
        else 1 if counts["failed"] else 0
    )
    emit({"type": "summary", "total": len(cases), **counts, "exit_status": exit_status})
    return exit_status


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--evidence", type=Path, metavar="PATH",
        help="save full JSONL records to a new file while showing readable results",
    )
    args = parser.parse_args(argv)
    evidence = None
    if args.evidence is not None:
        try:
            evidence = args.evidence.open("x", encoding="utf-8")
        except OSError as error:
            print(f"ERROR evidence: {error}", flush=True)
            return 2

    evidence_ok = True
    status = 2
    try:
        status = run(validation.Reporter(evidence))
    except validation.EvidenceError as error:
        print(f"\nERROR evidence: {error}", flush=True)
        evidence_ok = False
    finally:
        if evidence is not None:
            try:
                evidence.close()
            except (OSError, UnicodeError) as error:
                print(f"\nERROR evidence: {error}", flush=True)
                evidence_ok = False
                status = 2
    if evidence is not None and evidence_ok:
        print(f"Evidence: {args.evidence}", flush=True)
    return status


if __name__ == "__main__":
    sys.exit(main())
