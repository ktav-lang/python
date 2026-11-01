"""Проверить exact-source compiler grants без запуска toolchain."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "rust_compiler_notices", ROOT / "scripts/rust_compiler_notices.py"
)
assert spec is not None
assert spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
RUSTC = (
    "rustc 1.99.1 (fixture)\nhost: x86_64-unknown-linux-gnu\nrelease: 1.99.1\n"
    f"commit-hash: {module.RUST_REVISION}\nLLVM version: 23.1.1\n"
)


def test_complete_original_source_and_legal_materials() -> None:
    record = module.collect(ROOT, RUSTC)
    profile = json.loads((ROOT / "ci/rust-compiler-notices.json").read_text(encoding="utf-8"))
    assert record["compiler_builtins_license"] == "MIT AND Apache-2.0 WITH LLVM-exception"
    assert record["libm_license"] == "MIT"
    assert record["rust_revision"] == module.RUST_REVISION
    assert len(record["materials"]) == 14
    assert sum(item["legal_document"] for item in record["materials"]) == 4
    assert len(profile["materials"]) == 14
    for expected, actual in zip(profile["materials"], record["materials"]):
        original = (ROOT / expected["path"]).read_bytes().decode("utf-8")
        assert actual == {**expected, "text": original}


def test_libm_and_legacy_attribution_is_preserved() -> None:
    materials = module.collect(ROOT, RUSTC)["materials"]
    text = "\n".join(item["text"] for item in materials if item["legal_document"])
    assert "Copyright (c) 2018 Jorge Aparicio" in text
    assert "Copyright © 2005-2020 Rich Felker, et al." in text
    assert "Copyright (c) 2009-2016" in text
    assert "LLVM Exceptions to the Apache 2.0 License" in text


@pytest.mark.parametrize(
    "rustc",
    [
        "",
        "rustc 1.99.1",
        RUSTC.replace("1.99.1", "1.88.0"),
        RUSTC.replace(module.RUST_REVISION, "0" * 40),
    ],
)
def test_unknown_compiler_is_rejected(rustc: str) -> None:
    with pytest.raises(ValueError, match="compiler source identity"):
        module.collect(ROOT, rustc)


def test_changed_profile_is_rejected(tmp_path: Path) -> None:
    (tmp_path / "ci").mkdir()
    (tmp_path / "ci/rust-compiler-notices.json").write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="profile differs from review"):
        module.collect(tmp_path, RUSTC)


def test_missing_profile_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="missing or symlinked"):
        module.collect(tmp_path, RUSTC)


def test_changed_and_missing_original_are_rejected(tmp_path: Path) -> None:
    (tmp_path / "ci").mkdir()
    profile = (ROOT / "ci/rust-compiler-notices.json").read_bytes()
    (tmp_path / "ci/rust-compiler-notices.json").write_bytes(profile)
    item = json.loads(profile)["materials"][0]
    original = tmp_path / item["path"]
    original.parent.mkdir(parents=True)
    original.write_bytes(b"changed")
    with pytest.raises(ValueError, match="original identity differs"):
        module.collect(tmp_path, RUSTC)
    original.unlink()
    with pytest.raises(ValueError, match="missing or symlinked"):
        module.collect(tmp_path, RUSTC)


def test_collection_is_read_only_and_deterministic() -> None:
    before = (ROOT / "ci/rust-compiler-notices.json").read_bytes()
    assert module.collect(ROOT, RUSTC) == module.collect(ROOT, RUSTC)
    assert (ROOT / "ci/rust-compiler-notices.json").read_bytes() == before


def test_oversized_input_is_rejected(tmp_path: Path) -> None:
    source = tmp_path / "large.txt"
    source.write_bytes(b"12345")
    with pytest.raises(ValueError, match="exceeds bound"):
        module._read(source, 4)


def test_actual_container_binding_preserves_compiler_grants() -> None:
    binding_spec = importlib.util.spec_from_file_location(
        "bind_native_compiler", ROOT / "scripts/bind_native_compiler.py"
    )
    assert binding_spec is not None
    assert binding_spec.loader is not None
    binding = importlib.util.module_from_spec(binding_spec)
    binding_spec.loader.exec_module(binding)
    collection = module.collect(ROOT, RUSTC)
    bundle = {
        "schema_version": 1,
        "rustc": RUSTC,
        "rust_standard_library": {"text": "copyright", "sha256": "fixture"},
        "rust_compiler_builtins": collection,
    }
    actual = RUSTC.replace("x86_64", "aarch64")
    result = json.loads(binding._bind(bundle, actual))
    assert result["rustc"] == actual
    assert result["rust_compiler_builtins"] == collection
    assert result["rust_standard_library"]["report_compiler"] == RUSTC
