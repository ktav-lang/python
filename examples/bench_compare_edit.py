"""Same-runner pure source-edit comparison for isolated base/candidate checkouts.

Candidate ``examples/bench_edit.py`` is the sole workload and oracle source.
Only the standard library is used; this harness never builds or installs code.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any

WORKER = r"""
import importlib.util, json, sys, time
from pathlib import Path
# -I ignores PYTHONPATH; explicitly allow only this checkout's Python source.
source_root = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(source_root / "python"))
bench_path = Path(sys.argv[2]).resolve()
spec = importlib.util.spec_from_file_location("worker_bench_edit", bench_path)
bench = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bench)
import ktav
from ktav import pure
if getattr(ktav, "_HAS_CORE", False):
    raise RuntimeError("pure worker unexpectedly loaded native ktav")
for line in sys.stdin:
    req = json.loads(line)
    case = req["case"]
    try:
        if req["action"] == "validate":
            result = bench.invoke(pure, case)
            if result.encode("utf-8") != case["expected"].encode("utf-8"):
                raise AssertionError("byte output mismatch")
            actual = pure.loads(result)
            if actual != case["semantic"]:
                raise AssertionError("semantic output mismatch: {!r}".format(actual))
            response = {"ok": True}
        else:
            for _ in range(req["warmup"]):
                bench.invoke(pure, case)
            start = time.perf_counter()
            for _ in range(req["iterations"]):
                bench.invoke(pure, case)
            response = {"seconds_per_operation": (time.perf_counter() - start) / req["iterations"]}
    except Exception as exc:
        response = {"error": "{}: {}".format(type(exc).__name__, exc)}
    print(json.dumps(response, ensure_ascii=False), flush=True)
"""


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def request(proc: subprocess.Popen[str], payload: dict[str, Any]) -> dict[str, Any]:
    if proc.poll() is not None:
        raise RuntimeError(f"worker exited with status {proc.returncode}")
    if proc.stdin is None or proc.stdout is None:
        raise RuntimeError("worker pipes are unavailable")
    proc.stdin.write(json.dumps(payload, ensure_ascii=False) + "\n")
    proc.stdin.flush()
    line = proc.stdout.readline()
    if not line:
        raise RuntimeError(f"worker exited without a response (status {proc.poll()})")
    response = json.loads(line)
    if "error" in response:
        raise RuntimeError(response["error"])
    return response


def load_candidate_bench(path: Path, candidate_root: Path) -> Any:
    sys.path.insert(0, str(candidate_root / "python"))
    try:
        spec = importlib.util.spec_from_file_location("candidate_bench_edit", str(path))
        if spec is None or spec.loader is None:
            raise RuntimeError("cannot load candidate examples/bench_edit.py")
        bench = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(bench)
        return bench
    finally:
        sys.path.pop(0)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-python", required=True, help="base isolated environment interpreter"
    )
    parser.add_argument(
        "--base-source",
        "--base-root",
        dest="base_source",
        required=True,
        type=Path,
        help="base checkout root",
    )
    parser.add_argument(
        "--candidate-python", required=True, help="candidate isolated environment interpreter"
    )
    parser.add_argument(
        "--candidate-source",
        "--candidate-root",
        dest="candidate_source",
        required=True,
        type=Path,
        help="candidate checkout root; workloads/oracles",
    )
    parser.add_argument("--warmup", type=int, default=100)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--iterations", type=int, default=100)
    args = parser.parse_args()
    if min(args.warmup, args.repeats, args.iterations) < 1:
        parser.error("warmup, repeats, and iterations must be positive")

    roots = {"base": args.base_source.resolve(), "candidate": args.candidate_source.resolve()}
    scripts = {name: roots[name] / "examples" / "bench_edit.py" for name in roots}
    for script in scripts.values():
        if not script.is_file():
            parser.error(f"missing benchmark script: {script}")
    candidate_script = scripts["candidate"]
    candidate_bench = load_candidate_bench(candidate_script, roots["candidate"])
    cases = candidate_bench.all_cases()
    interpreters = {"base": args.base_python, "candidate": args.candidate_python}
    workers: dict[str, subprocess.Popen[str]] = {}
    try:
        for label in ("base", "candidate"):
            workers[label] = subprocess.Popen(
                [
                    interpreters[label],
                    "-I",
                    "-u",
                    "-c",
                    WORKER,
                    str(roots[label]),
                    str(candidate_script),
                ],
                cwd=str(roots[label]),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=None,
                text=True,
                encoding="utf-8",
            )
        # Each identical candidate case is checked by both implementations before timing.
        for case in cases:
            for label in ("base", "candidate"):
                request(workers[label], {"action": "validate", "case": case})

        metadata = {
            "type": "metadata",
            "mode": "pure",
            "python_runner": sys.version,
            "platform": platform.platform(),
            "machine": platform.machine(),
            "warmup": args.warmup,
            "repeats": args.repeats,
            "iterations": args.iterations,
            "scenario_count": len(cases),
            "source_sha256": {key: sha(path) for key, path in scripts.items()},
            "candidate_bench_edit_sha256": sha(scripts["candidate"]),
            "interpreters": interpreters,
            "source_roots": {key: str(value) for key, value in roots.items()},
        }
        print(json.dumps(metadata, ensure_ascii=False), flush=True)
        for case in cases:
            for repeat in range(args.repeats):
                order = ("base", "candidate") if repeat % 2 == 0 else ("candidate", "base")
                for label in order:
                    sample = request(
                        workers[label],
                        {
                            "action": "time",
                            "case": case,
                            "warmup": args.warmup,
                            "iterations": args.iterations,
                        },
                    )
                    print(
                        json.dumps(
                            {
                                "type": "result",
                                "backend": label,
                                "scenario": case["name"],
                                "operation": case["operation"],
                                "source_bytes": len(case["source"].encode("utf-8")),
                                "repeat": repeat,
                                "order": list(order),
                                "iterations": args.iterations,
                                "warmup": args.warmup,
                                "seconds_per_operation": sample["seconds_per_operation"],
                            },
                            ensure_ascii=False,
                        ),
                        flush=True,
                    )
    finally:
        for proc in workers.values():
            if proc.stdin is not None and not proc.stdin.closed:
                proc.stdin.close()
            if proc.poll() is None:
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.terminate()
                    try:
                        proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                        proc.wait()


if __name__ == "__main__":
    main()
