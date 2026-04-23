# Changelog — `ktav` (Python bindings)

**Languages:** **English** · [Русский](CHANGELOG.ru.md) · [简体中文](CHANGELOG.zh.md)

All notable changes to the `ktav` Python package are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
this package adheres to [Semantic Versioning](https://semver.org/) with
the pre-1.0 convention that a MINOR bump is breaking.

For the format specification's own history, see
[`ktav-lang/spec`](https://github.com/ktav-lang/spec). For the
underlying Rust implementation, see
[`ktav-lang/rust`](https://github.com/ktav-lang/rust).

## [0.1.0] — 2026-04-22

Initial release. Implements [Ktav spec 0.1.0](https://github.com/ktav-lang/spec/blob/main/versions/0.1/spec.md)
via PyO3 bindings over the reference Rust implementation.

### Added

- `ktav.loads(s)` — parse a Ktav string (or UTF-8 `bytes`) into native
  Python values.
- `ktav.dumps(obj)` — serialise a native Python value into Ktav text.
- `ktav.load(fp)` / `ktav.dump(obj, fp)` — file-like wrappers that work
  for both text-mode and binary-mode files.
- Exception hierarchy: `KtavError` (base), `KtavDecodeError`,
  `KtavEncodeError`.
- Type mapping honouring Ktav's "no magic types" principle:
  - bare scalars → `str`;
  - `:i` marker → `int` (arbitrary precision round-trips);
  - `:f` marker → `float` (decimal point always present on output);
  - keywords `null` / `true` / `false` → `None` / `bool`;
  - `[ ... ]` → `list`;
  - `{ ... }` → `dict` (insertion order preserved).
- `NaN` / `±Infinity` rejected by the serialiser — Ktav 0.1.0 does not
  represent them.
- Bundled `.pyi` type stubs and `py.typed` marker (PEP 561).
- `ktav.__version__` — package version.
- `ktav.__spec_version__` — Ktav format version these bindings
  implement.

### Supported platforms

Prebuilt wheels:

- **Linux** (manylinux + musllinux) — `x86_64`, `aarch64`
- **macOS** — `x86_64`, `arm64`
- **Windows** — `x64`, `arm64`

Wheels use the stable ABI (`abi3-py39`); one wheel per platform serves
every supported CPython release.

### MSRV

Rust **1.70** or newer — matches the underlying `ktav` crate.
