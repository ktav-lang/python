"""Fail-closed metadata check for the universal pure wheel."""

from __future__ import annotations

import email
import sys
import zipfile
from pathlib import Path


def main() -> None:
    """Require one ktav wheel METADATA file with no dependency declarations."""
    if len(sys.argv) != 2:
        raise SystemExit("usage: check_pure_wheel_metadata.py WHEEL")
    wheel = Path(sys.argv[1])
    with zipfile.ZipFile(wheel) as archive:
        entries = [name for name in archive.namelist() if name.endswith(".dist-info/METADATA")]
        if len(entries) != 1 or entries[0].count("/") != 1:
            raise SystemExit(f"expected exactly one root .dist-info/METADATA, got {entries!r}")
        if not entries[0].startswith("ktav-"):
            raise SystemExit(f"unexpected distribution metadata path: {entries[0]!r}")
        metadata = email.message_from_bytes(archive.read(entries[0]))
        dist_info = entries[0].split("/", 1)[0]
        root = Path(__file__).resolve().parent.parent
        for name in ("LICENSE-MIT", "LICENSE-APACHE"):
            candidates = [f"{dist_info}/{name}", f"{dist_info}/licenses/{name}"]
            matches = [entry for entry in archive.namelist() if entry in candidates]
            if len(matches) != 1 or archive.read(matches[0]) != (root / name).read_bytes():
                raise SystemExit(f"missing, duplicate or incorrect license file: {name}")
    if metadata.get("Name", "").lower() != "ktav" or metadata.get("Version") != "0.8.1":
        raise SystemExit("expected ktav 0.8.1 Name/Version metadata")
    metadata_versions = metadata.get_all("Metadata-Version", [])
    if len(metadata_versions) != 1 or metadata_versions[0] not in {"2.1", "2.2", "2.3", "2.4"}:
        raise SystemExit(f"unexpected Metadata-Version fields: {metadata_versions!r}")
    if metadata.get_all("Requires-Dist", []):
        raise SystemExit(
            f"pure wheel must declare no Requires-Dist: {metadata.get_all('Requires-Dist')!r}"
        )
    print(f"pure wheel metadata OK: {entries[0]}")


if __name__ == "__main__":
    main()
