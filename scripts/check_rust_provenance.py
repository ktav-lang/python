"""Fail-closed Rust provenance check for release builds.

Proves, from the workspace alone, that a native build compiles against
crates.io ``ktav`` at the expected version and checksum: the workspace
``Cargo.toml`` pins the expected package version and the compatible public
dependency range, and a generated ``Cargo.lock`` pins the exact ktav 0.8.1
resolution. Deliberately does NOT read any Python ``__version__`` — the
Rust core version is proven from the lock, not from host claims.

No writes, no network, no subprocess. Stdlib on Python 3.11+; Python 3.9/3.10
tooling uses the ``tomli`` backport.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

DEFAULT_VERSION = "0.8.1"
DEFAULT_CHECKSUM = "7140dfe2fa6c320e74768cd6a637828c2d26f81746254f4fcd805f3993bd3fd5"
DEFAULT_REQUIREMENT = ">=0.8.1, <0.9"
REGISTRY_SOURCE = "registry+https://github.com/rust-lang/crates.io-index"

REPO = Path(__file__).resolve().parent.parent


def die(reason: str) -> None:
    """Print a one-line failure reason and exit non-zero."""
    print(f"rust provenance check FAILED: {reason}", file=sys.stderr)
    raise SystemExit(1)


def load_toml(path: Path) -> dict:
    """Parse a TOML file, failing closed."""
    if not path.is_file():
        die(f"{path.name} not found ({path.parent})")
    with path.open("rb") as fh:
        return tomllib.load(fh)


def main() -> None:
    """Run all checks; print what was verified on success."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expect-version", default=DEFAULT_VERSION)
    parser.add_argument("--expect-checksum", default=DEFAULT_CHECKSUM)
    parser.add_argument("--ktav-requirement", default=DEFAULT_REQUIREMENT)
    parser.add_argument("--cargo-manifest", type=Path, default=REPO / "Cargo.toml")
    parser.add_argument("--cargo-lock", type=Path, default=REPO / "Cargo.lock")
    args = parser.parse_args()

    # 1. [package] version in the workspace Cargo.toml.
    manifest = load_toml(args.cargo_manifest)
    package = manifest.get("package")
    if not isinstance(package, dict) or "version" not in package:
        die("Cargo.toml has no [package] version")
    if package["version"] != args.expect_version:
        die(f"Cargo.toml package version {package['version']!r} != {args.expect_version!r}")

    # 2. The public ktav dependency range must stay intact.
    deps = manifest.get("dependencies", {})
    ktav_req = deps.get("ktav") if isinstance(deps, dict) else None
    if isinstance(ktav_req, dict):
        ktav_req = ktav_req.get("version")
    if ktav_req != args.ktav_requirement:
        die(f"Cargo.toml ktav requirement {ktav_req!r} != {args.ktav_requirement!r}")

    # 3. Cargo.lock pins the exact ktav source and checksum.
    lock = load_toml(args.cargo_lock)
    entries = [p for p in lock.get("package", []) if p.get("name") == "ktav"]
    if len(entries) != 1:
        die(f"Cargo.lock has {len(entries)} ktav [[package]] entries, expected exactly 1")
    entry = entries[0]
    for key, expected in (
        ("version", args.expect_version),
        ("source", REGISTRY_SOURCE),
        ("checksum", args.expect_checksum),
    ):
        if entry.get(key) != expected:
            die(f"Cargo.lock ktav {key} {entry.get(key)!r} != {expected!r}")

    print(
        "rust provenance OK: "
        f"package version {args.expect_version}, "
        f"ktav {args.ktav_requirement!r}, "
        f"lock resolves ktav {args.expect_version} from crates.io "
        f"(checksum {args.expect_checksum})"
    )


if __name__ == "__main__":
    main()
