"""Проверить native payload и notices переносимого wheel."""

from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from cargo_notice_bundle import _verify
from check_musllinux_wheel import _module_bytes
from macos_native_imports import verify as verify_macos_imports


def _expected(name: str) -> tuple[str, str, set[str]]:
    match = re.fullmatch(r"ktav-[^-]+-cp39-abi3-(.+)\.whl", name)
    if not match:
        raise ValueError("unexpected native wheel ABI tag")
    platform = match.group(1)
    if platform.startswith("win_"):
        kind, module = "COFF", "ktav/_core.pyd"
    elif platform.startswith("manylinux"):
        kind, module = "ELF", "ktav/_core.abi3.so"
    elif platform.startswith("macosx_"):
        kind, module = "MachO", "ktav/_core.abi3.so"
    else:
        raise ValueError("unexpected native wheel platform")
    if platform.endswith(("_arm64", "_aarch64")):
        architectures = {"aarch64", "arm64"}
    elif platform.endswith(("_amd64", "_x86_64")):
        architectures = {"x86_64"}
    else:
        raise ValueError("unexpected native wheel architecture")
    return kind, module, architectures


def _readobj() -> Path:
    sysroot = subprocess.check_output(["rustc", "--print", "sysroot"], text=True).strip()
    rustc = subprocess.check_output(["rustc", "--version", "--verbose"], text=True)
    host = re.search(r"^host: (.+)$", rustc, re.MULTILINE)
    if not host:
        raise ValueError("missing Rust host triple")
    name = "llvm-readobj.exe" if os.name == "nt" else "llvm-readobj"
    tool = Path(sysroot) / "lib" / "rustlib" / host.group(1).strip() / "bin" / name
    if not tool.is_file():
        raise ValueError("missing llvm-tools-preview component")
    return tool


def _inspect(wheel: Path, bundle: Path) -> str:
    kind, module, architectures = _expected(wheel.name)
    _verify(wheel, bundle.read_bytes())
    data = _module_bytes(wheel, module)
    magic = {
        "COFF": (b"MZ",),
        "ELF": (b"\x7fELF",),
        "MachO": (b"\xcf\xfa\xed\xfe", b"\xfe\xed\xfa\xcf"),
    }
    if not data.startswith(magic[kind]):
        raise ValueError("native payload format differs from wheel platform")
    tool = _readobj()
    with tempfile.TemporaryDirectory() as temp:
        binary = Path(temp) / Path(module).name
        binary.write_bytes(data)
        header = subprocess.check_output([str(tool), "-h", str(binary)], text=True)
        arch = re.search(r"^Arch:\s*(\S+)\s*$", header, re.MULTILINE)
        if not arch or arch.group(1) not in architectures:
            raise ValueError("native payload architecture differs from wheel tag")
        if kind == "MachO":
            command = ["otool", "-L", str(binary)]
        else:
            option = "--coff-imports" if kind == "COFF" else "--needed-libs"
            command = [str(tool), option, str(binary)]
        imports = subprocess.check_output(command, text=True)
        if kind == "MachO":
            symbols = subprocess.check_output(["nm", "-u", str(binary)], text=True)
            verify_macos_imports(imports, symbols)
            imports += "\nUndefined symbols:\n" + symbols
    return f"wheel: {wheel.name}\nmodule: {module}\n{header}\n{imports}"


def main() -> None:
    """Сверить wheel и сохранить native headers/imports для аудита."""
    if len(sys.argv) != 4:
        raise SystemExit("usage: check_native_wheel.py WHEEL BUNDLE REPORT")
    try:
        report = _inspect(Path(sys.argv[1]), Path(sys.argv[2]))
        with Path(sys.argv[3]).open("x", encoding="utf-8") as output:
            output.write(report)
    except (OSError, ValueError, subprocess.CalledProcessError, zipfile.BadZipFile) as exc:
        raise SystemExit(str(exc)) from exc
    print(f"Native wheel payload and notices verified: {Path(sys.argv[1]).name}")


if __name__ == "__main__":
    main()
