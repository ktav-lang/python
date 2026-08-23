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

## [0.6.4] — 2026-08-23

Synchronized with Ktav spec and Rust core 0.6.4.

### Added

- Added `ktav.loads_strict()` for strict canonical-scalar validation.
  Canonical scientific float forms emitted by the writer are accepted.

### Changed

- Package version and spec metadata are now `0.6.4`.
- The Rust dependency uses `ktav = "0.6"`, selecting the latest compatible
  patch release in the 0.6 minor line.
- Spec submodule is pinned to the published Ktav 0.6.4 commit.

## [0.6.1] — 2026-06-05

- Docs: rewrite all README examples to spec 0.6 syntax (bare numbers instead of removed `:i`/`:f` markers; `##` comments instead of `#`).

## [0.6.0] — 2026-06-01

Sync to Ktav 0.6.0 — keys now support escaping.

### Added

- Keys process the full §3.7 escape set, with two new escapes:
  - `\.` → `.` (literal dot — does **not** split a dotted path)
  - `\:` → `:` (literal colon — does **not** act as the key/value separator)
- Examples: `a\.b: v` → `{"a.b": "v"}`, `a\:b: v` → `{"a:b": "v"}`,
  `x.y\.z: v` → `{"x": {"y.z": "v"}}`.

### Breaking

- A literal backslash inside a key now requires `\\` (previously `\` in
  a key was a plain byte). Rare in practice; per pre-1.0 SemVer this is
  a MINOR bump.

### Changed

- Tracks ktav-rust 0.6.0 / Ktav spec 0.6.0. Binding source unchanged —
  the escape change is internal to the Rust core and transparent across
  the PyO3 boundary.

---

## [0.5.0] — 2026-05-28

Breaking release implementing Ktav specification 0.5.0.

### Breaking

- **Typed markers `:i` and `:f` removed.** Numbers, booleans, and `null`
  are inferred from the scalar's lexical form (spec §§ 3.6, 5.2).
  `port: 8080` now yields `int(8080)`; use `port:: 8080` to keep a String.
- **Comments use `##`** (line-start only). A single `#` byte is content —
  `color: #FF0000` is a valid string value.
- **Inline compounds** `{k: v, …}` / `[i, …]` are now valid (spec § 5.8).
  The `InlineNonEmptyCompound` error is no longer emitted by the parser.

### Added

- **`ktav.emit_canonical(obj)`** — emit the normalised (spec § 5.9)
  byte-deterministic canonical form of a Python value.
- **Number literal grammar** — hex (`0x`), octal (`0o`), binary (`0b`),
  decimal, and underscore separators; i64 overflow falls back to String.
- **Eight escape sequences** in inline scalars (spec § 3.7):
  `\\`, `\,`, `\}`, `\]`, `\{`, `\[`, `\n`, `\r`.

### Changed

- License: `MIT` → `MIT OR Apache-2.0`. Added `LICENSE-APACHE`;
  renamed `LICENSE` → `LICENSE-MIT`.
- Spec submodule pinned to `v0.5.0`.
- Picked up `ktav 0.5.0`.

---

## [0.3.1] — 2026-05-10

Backward-compatible feature release: top-level Arrays and a new
`dumps_force_strings` entry point.

### Added

- **Top-level Array support** (spec 0.1.1, § 5.0.1) — the parser now
  recognises documents whose first content line is an array-item
  shape (a bare scalar, `:: text`, `:i 42`, `:f 3.14`, a lone `{` /
  `[`, or a multi-line opener `(` / `((`) as a root-level Array.
  `ktav.loads(":i 1\n:i 2")` returns `[1, 2]`. Object documents are
  unchanged. The serialiser accepts top-level `list` / `tuple` and
  emits items bare, one per line, with no surrounding `[...]`.
- **`ktav.dumps_force_strings(obj)`** — render every leaf scalar as
  a String (typed integers, typed floats, booleans, and `None` are
  flattened to their textual form via the raw `::` marker so the
  output round-trips back as the same string scalars). Compounds
  preserve their structure; only leaves are coerced. The
  Python-idiomatic snake_case parallel to `dumps` / `loads`.

### Changed

- **Picked up `ktav 0.3.1`** — adds the format-level top-level
  Array support and the `to_string_force_strings` API the new
  Python entry point delegates to. See the
  [`ktav` crate CHANGELOG](https://github.com/ktav-lang/rust/blob/main/CHANGELOG.md#031--2026-05-10).
- `ktav.dumps(list_or_tuple)` no longer raises — it now renders a
  top-level Array per spec § 5.0.1.
- `__spec_version__` bumped to `0.1.1`.

### Spec

- spec submodule synced to `7256816` (Ktav 0.1.1 — top-level Array
  fixtures under `versions/0.1/tests/valid/top_level_array/` and
  `versions/0.1/tests/invalid/top_level/`).


## [0.3.0] — 2026-05-08

### Changed (breaking)

- **Picked up `ktav 0.3.0`** — the upstream Rust crate's reject-paren-strings
  change. Inline paren-wrapped scalars like `a: (hello)` and `a: ((wrapped))`
  are now decode errors. The PyO3 binding inherits this behaviour
  transparently. See the
  [`ktav` crate CHANGELOG](https://github.com/ktav-lang/rust/blob/main/CHANGELOG.md#030--2026-05-08).

### Spec

- spec submodule synced to `46d94a7` (new invalid fixtures
  `inline_paren_string_double` and `inline_paren_string_single`,
  tightened `partial_parens` valid-fixture).


## [0.2.0] — 2026-05-07

### Changed (breaking)

- **Picked up `ktav 0.2.0`** — multi-line strings now serialize in the
  indented stripped `( ... )` form by default. `:f 42` accepts integer
  literals (parsed as `42.0`). See the
  [`ktav` crate CHANGELOG](https://github.com/ktav-lang/rust/blob/main/CHANGELOG.md#020--2026-05-07).

  Code comparing serialized output byte-for-byte to a baked-in
  `((...))` literal must be updated. Round-trip is unchanged.

### Spec

- spec submodule synced (typed_float_integer_body fixture; oracle 42.0).


## [0.1.2] — 2026-05-03

### Changed

- **Picked up `ktav 0.1.5`** — the upstream Rust crate's structured
  errors API (`Error::Structured(ErrorKind)` with byte-offset spans),
  retroactive `#[non_exhaustive]` on the error enums, and the public
  `ktav::thin` event-based parser. The PyO3 binding's user-visible
  behaviour is unchanged: `KtavDecodeError` / `KtavEncodeError` still
  carry the same human-readable messages (Display strings for the
  seven canonical categories are byte-identical to ktav 0.1.4).
  Mapping `ktav::ErrorKind` to a structured Python exception
  hierarchy (`MissingSeparatorSpace`, `DuplicateKey`, etc.) is
  separate follow-up work tracked in the workspace's
  [`STRUCTURED_ERRORS.md`](https://github.com/ktav-lang/.github/blob/main/STRUCTURED_ERRORS.md).

PyPI: `ktav==0.1.2`.

## [0.1.1] — 2026-04-26

### Changed

- **Picked up `ktav 0.1.4`** — the upstream Rust crate's untyped
  `parse() → Value` path (which the PyO3 binding uses) is now ~30%
  faster on small documents and ~13% faster on large ones, just from
  a one-line `Frame::Object` capacity tweak (4 → 8). Every
  `ktav.loads` call benefits transparently.

PyPI: `ktav==0.1.1`.

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
