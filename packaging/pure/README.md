# Pure (native-free) wheel of `ktav`.

This directory builds a `py3-none-any` wheel of the SAME distribution
(`ktav`) containing ONLY the pure-Python backend — no Rust, no maturin,
no compilation at install time. It exists because every other artifact
(sdist + platform wheels) requires a Rust toolchain when no prebuilt
wheel matches the platform.

Contents: `python/ktav/__init__.py`, `pure.py`, `py.typed`,
`_core.pyi`, `_pure/**` — nothing else. There is no `ktav/_core.py`
anywhere in the source tree (the compiled extension exists only inside
maturin-built wheels), so the pure wheel genuinely has no `ktav._core`.

Native wheels remain the PREFERRED install when available; use this
wheel only when a compiled wheel cannot be installed.

Versioning: `version = "0.8.1"` in `pyproject.toml` here is HARDCODED
and must be bumped in lockstep with the root `Cargo.toml` (which drives
the maturin wheels). CI cross-checks the two before building/publishing.

Coexistence: pip treats the pure wheel and a native wheel as the same
distribution (same name, same version); the shared pure-Python files are
byte-identical and only the native wheel adds `ktav._core`. Switching
between them therefore requires uninstall + reinstall — pip will
otherwise happily replace one with the other in place.
