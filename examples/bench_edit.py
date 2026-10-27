"""Compare source-edit operations in native ktav and standalone ktav.pure.

Run from the repository root after building/installing the native extension:
``python examples/bench_edit.py``. Results are JSON Lines; timings are
observations only and are not performance claims or thresholds.
"""

from __future__ import annotations

import argparse
import json
import platform
import time
from typing import Any

import ktav
from ktav import pure

CASES = (
    {
        "name": "insert-root",
        "operation": "insert_value",
        "source": "a: 1\n",
        "path": "b",
        "value": 2,
        "expected": "a: 1\nb: 2\n",
        "semantic": {"a": 1, "b": 2},
    },
    {
        "name": "insert-nested-object-array",
        "operation": "insert_value",
        "source": "items: [{name: one}]\n",
        "path": "items.0.value",
        "value": 2,
        "expected": "items: [{name: one, value: 2}]\n",
        "semantic": {"items": [{"name": "one", "value": 2}]},
    },
    {
        "name": "remove-array-element",
        "operation": "remove_value",
        "source": "## keep\na: [1, 2, 3]\nb: 4\n",
        "path": "a.1",
        "expected": "## keep\na: [1, 3]\nb: 4\n",
        "semantic": {"a": [1, 3], "b": 4},
    },
    {
        "name": "rename-crlf-dotted",
        "operation": "rename_key",
        "source": '"a.b": {child: {leaf: 1}, keep: 2}\r\n',
        "path": r"a\.b.child.leaf",
        "new_key": "changed",
        "expected": '"a.b": {child: {changed: 1}, keep: 2}\r\n',
        "semantic": {"a.b": {"child": {"changed": 1}, "keep": 2}},
    },
    {
        "name": "rename-unicode-key-crlf",
        "operation": "rename_key",
        "source": "k:: 042\r\n",
        "path": "k",
        "new_key": "ключ",
        "expected": "ключ:: 042\r\n",
        "semantic": {"ключ": "042"},
    },
    {
        "name": "remove-root",
        "operation": "remove_value",
        "source": "a: 1\nb: 2\n",
        "path": "a",
        "expected": "b: 2\n",
        "semantic": {"b": 2},
    },
)
NATIVE_EDIT_NAMES = ("_insert_value", "_remove_value", "_rename_key")


def wide_root_cases() -> tuple[dict[str, Any], ...]:
    """Build broad-root fixtures and oracles from known ordered entries."""
    cases = []
    for size in (16, 128, 512):
        entries = [(f"key{index:03d}", index) for index in range(size)]
        source = "".join(f"{key}: {value}\n" for key, value in entries)
        semantic = dict(entries)
        for operation, position in (
            ("insert_value", size),
            ("remove_value", size // 2),
            ("remove_value", size - 1),
            ("rename_key", size // 2),
            ("rename_key", size - 1),
        ):
            key = f"key{position:03d}"
            updated_entries = list(entries)
            updated_semantic = dict(semantic)
            if operation == "insert_value":
                updated_entries.append(("added", -1))
                updated_semantic["added"] = -1
                path = "added"
                value = -1
            elif operation == "remove_value":
                updated_entries.pop(position)
                del updated_semantic[key]
                path = key
                value = None
            else:
                updated_entries[position] = ("renamed", position)
                del updated_semantic[key]
                updated_semantic["renamed"] = position
                path = key
                value = None
            expected = "".join(
                f"{entry_key}: {entry_value}\n" for entry_key, entry_value in updated_entries
            )
            case = {
                "name": f"wide-root-{size}-{operation}-{position}",
                "operation": operation,
                "source": source,
                "path": path,
                "expected": expected,
                "semantic": updated_semantic,
            }
            if operation == "insert_value":
                case["value"] = value
            if operation == "rename_key":
                case["new_key"] = "renamed"
            cases.append(case)
    return tuple(cases)


def all_cases() -> tuple[dict[str, Any], ...]:
    return CASES + wide_root_cases()


def invoke(api: Any, case: dict[str, Any]) -> str:
    operation = case["operation"]
    if operation == "rename_key":
        return api.rename_key(case["source"], case["path"], case["new_key"])
    if operation == "insert_value":
        return api.insert_value(case["source"], case["path"], case["value"])
    return api.remove_value(case["source"], case["path"])


def validate(api: Any, backend: str) -> None:
    for case in all_cases():
        result = invoke(api, case)
        expected_bytes = case["expected"].encode("utf-8")
        if result.encode("utf-8") != expected_bytes:
            raise AssertionError(f"{backend} {case['name']}: byte output mismatch: {result!r}")
        actual = api.loads(result)
        if actual != case["semantic"]:
            raise AssertionError(f"{backend} {case['name']}: semantic mismatch: {actual!r}")


def benchmark(
    api: Any,
    backend: str,
    case: dict[str, Any],
    warmup: int,
    repeats: int,
    iterations: int,
) -> dict[str, Any]:
    def run_edit() -> str:
        return invoke(api, case)

    for _ in range(warmup):
        run_edit()
    samples = []
    for _ in range(repeats):
        start = time.perf_counter()
        for _ in range(iterations):
            run_edit()
        samples.append((time.perf_counter() - start) / iterations)
    return {
        "type": "result",
        "backend": backend,
        "scenario": case["name"],
        "operation": case["operation"],
        "source_bytes": len(case["source"].encode("utf-8")),
        "iterations": iterations,
        "warmup": warmup,
        "samples_seconds_per_operation": samples,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--warmup", type=int, default=100)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--iterations", type=int, default=100)
    args = parser.parse_args()
    if min(args.warmup, args.repeats, args.iterations) < 1:
        parser.error("warmup, repeats, and iterations must be positive")

    if not ktav._HAS_CORE:
        raise RuntimeError("A real native ktav source-edit extension is required")
    for name in NATIVE_EDIT_NAMES:
        function = getattr(ktav, name, None)
        if function is None or getattr(function, "_ktav_stub", False):
            raise RuntimeError(f"A real native source-edit function is required: {name}")
    validate(ktav, "native")
    validate(pure, "pure")
    metadata = {
        "type": "metadata",
        "python": platform.python_version(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "ktav_version": ktav.__version__,
        "pure_version": pure.__version__,
        "warmup": args.warmup,
        "repeats": args.repeats,
        "iterations": args.iterations,
    }
    print(json.dumps(metadata, ensure_ascii=False))
    for case in all_cases():
        samples_by_backend = {"native": [], "pure": []}
        backends = (("native", ktav), ("pure", pure))
        for repeat in range(args.repeats):
            order = backends if repeat % 2 == 0 else tuple(reversed(backends))
            for backend, api in order:
                result = benchmark(api, backend, case, args.warmup, 1, args.iterations)
                samples_by_backend[backend].extend(result["samples_seconds_per_operation"])
        for backend, _api in backends:
            result = {
                "type": "result",
                "backend": backend,
                "scenario": case["name"],
                "operation": case["operation"],
                "source_bytes": len(case["source"].encode("utf-8")),
                "iterations": args.iterations,
                "warmup": args.warmup,
                "samples_seconds_per_operation": samples_by_backend[backend],
                "order": "alternating native/pure by repeat",
            }
            print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
