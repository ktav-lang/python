"""Проверить ABI и содержимое musllinux wheel."""

from __future__ import annotations

import base64
import csv
import hashlib
import io
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

MODULE = "ktav/_core.abi3.so"
MAX_MODULE_BYTES = 64 * 1024 * 1024


def _expected_machine(name: str) -> str:
    if re.search(r"-musllinux_\d+_\d+_x86_64\.whl$", name):
        return "Advanced Micro Devices X86-64"
    if re.search(r"-musllinux_\d+_\d+_aarch64\.whl$", name):
        return "AArch64"
    raise ValueError(f"unexpected musllinux wheel name: {name}")


def _module_bytes(path: Path, module: str = MODULE) -> bytes:
    with zipfile.ZipFile(path) as wheel:
        names = wheel.namelist()
        native = []
        for info in wheel.infolist():
            if info.is_dir():
                continue
            with wheel.open(info) as source:
                magic = source.read(8)
            binary_name = re.search(
                r"(?:\.so(?:\.\d+)*|\.pyd|\.dll|\.dylib|\.node|\.a|\.lib|\.exe)$",
                info.filename,
                re.IGNORECASE,
            )
            binary_magic = magic.startswith(
                (
                    b"\x7fELF",
                    b"MZ",
                    b"\x00asm",
                    b"!<arch>\n",
                    b"\xcf\xfa\xed\xfe",
                    b"\xfe\xed\xfa\xcf",
                    b"\xce\xfa\xed\xfe",
                    b"\xfe\xed\xfa\xce",
                    b"\xca\xfe\xba\xbe",
                    b"\xbe\xba\xfe\xca",
                )
            )
            if binary_name or binary_magic:
                native.append(info.filename)
        if native != [module]:
            raise ValueError(f"unexpected wheel native payload: {native!r}")
        info = wheel.getinfo(module)
        if info.file_size <= 0 or info.file_size > MAX_MODULE_BYTES:
            raise ValueError("invalid native module size")
        data = wheel.read(info)
        records = [name for name in names if name.endswith(".dist-info/RECORD")]
        if len(records) != 1 or records[0].count("/") != 1:
            raise ValueError(f"unexpected wheel RECORD: {records!r}")
        rows = list(csv.reader(io.StringIO(wheel.read(records[0]).decode("utf-8"))))
        matching = [row for row in rows if row and row[0] == module]
        digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=").decode()
        if matching != [[module, f"sha256={digest}", str(len(data))]]:
            raise ValueError("native module does not match wheel RECORD")
        return data


def _verify_elf(data: bytes, expected_machine: str) -> None:
    with tempfile.TemporaryDirectory() as temp:
        binary = Path(temp) / "native.so"
        binary.write_bytes(data)
        header = subprocess.check_output(["readelf", "-h", str(binary)], text=True)
        machine = re.search(r"^\s*Machine:\s*(.+)$", header, re.MULTILINE)
        if not machine or machine.group(1).strip() != expected_machine:
            raise ValueError("unexpected ELF machine")
        dynamic = subprocess.check_output(["readelf", "-d", str(binary)], text=True)
        needed = re.findall(r"Shared library: \[([^]]+)\]", dynamic)
        if needed != ["libc.so"]:
            raise ValueError(f"unexpected shared libraries: {needed!r}")
        versions = subprocess.check_output(["readelf", "--version-info", str(binary)], text=True)
        if re.search(r"\bGLIBC_[0-9]", versions):
            raise ValueError("glibc symbol version in musllinux module")
        symbols = subprocess.check_output(
            ["readelf", "--dyn-syms", "--wide", str(binary)], text=True
        )
        exports = [
            parts[7]
            for line in symbols.splitlines()
            if len(parts := line.split()) >= 8
            and parts[4] in ("GLOBAL", "WEAK")
            and parts[5] in ("DEFAULT", "PROTECTED")
            and parts[6] != "UND"
        ]
        if exports != ["PyInit__core"]:
            raise ValueError(f"unexpected exported symbols: {exports!r}")


def main() -> None:
    """Проверить wheel, ELF-зависимости и экспортируемые символы."""
    if len(sys.argv) != 2:
        raise SystemExit("usage: check_musllinux_wheel.py WHEEL")
    try:
        wheel = Path(sys.argv[1])
        _verify_elf(_module_bytes(wheel), _expected_machine(wheel.name))
    except (OSError, ValueError, subprocess.CalledProcessError, zipfile.BadZipFile) as exc:
        raise SystemExit(str(exc)) from exc
    print(f"musllinux wheel ABI verified: {wheel.name}")


if __name__ == "__main__":
    main()
