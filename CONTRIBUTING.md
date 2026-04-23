# Contributing to ktav (Python)

**Languages:** **English** · [Русский](CONTRIBUTING.ru.md) · [简体中文](CONTRIBUTING.zh.md)

## Core rules

### 1. Every bug fix ships with a regression test

When you find a bug, **before fixing it**, write a test that reproduces
it — the test **must fail on `main`** and pass after the fix. Include
both in the same PR.

Tests live under `tests/`:

| File                         | Scope                                        |
|------------------------------|----------------------------------------------|
| `test_loads.py`              | Parser behaviour.                            |
| `test_dumps.py`              | Serializer behaviour.                        |
| `test_roundtrip.py`          | `loads(dumps(x)) == x`.                      |
| `test_errors.py`             | Exception taxonomy and propagation.          |
| `test_load_dump.py`          | File-like wrappers.                          |
| `test_module.py`             | Module-level exports, version strings.       |
| `test_conformance.py`        | Cross-language conformance against the spec. |

### 2. Don't reinvent the format in the bindings

These Python bindings are deliberately a thin wrapper. Parser / format
behaviour belongs in the Rust crate
([`ktav-lang/rust`](https://github.com/ktav-lang/rust)) — changing it
there updates every language binding at once. Only **Python-specific
ergonomics** (file-like wrappers, exception types, type stubs) belong
in this repo.

If your change requires a format change, start a discussion in
[`ktav-lang/spec`](https://github.com/ktav-lang/spec) first.

### 3. Public API changes note compatibility

If you touch anything exported from `ktav` or `ktav._core`, say in the
PR description whether it is:

- **semver-compatible** (additions, looser types, doc changes); or
- **semver-breaking** (renamed / removed items, changed signatures,
  tightened types) — in which case the version bump lands in the next
  MINOR while we are pre-1.0.

Update `CHANGELOG.md` and the two translations in the same PR.

### 4. One concept per commit

Commits should be atomic: a bug fix and its test together, a feature
and its tests together, a rename on its own, a refactor on its own.
`git log --oneline` should read like a changelog. Don't prefix commit
messages with `feat:` / `fix:` — no conventional commits here.

## Dev setup

You need:

- Python **3.9+** (any version you plan to test against).
- A Rust toolchain via [`rustup`](https://rustup.rs/). MSRV: **1.70**.
- [`maturin`](https://www.maturin.rs/) plus the test tooling:

```
pip install -e ".[dev]"
```

Layout during development — these bindings resolve the `ktav` Rust
crate via a `path = "../rust"` dependency in `Cargo.toml`. Clone the
sibling repo next to this one:

```
ktav-lang/
├── python/   ← this repo
├── rust/     ← sibling Rust crate
└── spec/     ← conformance fixtures (optional but recommended)
```

Once `ktav` is published to crates.io, the path dependency goes away
and only the `version = "0.1"` requirement stays. See the comment on
that line in `Cargo.toml`.

### Build

```
make dev          # debug build (fast incremental)
make install      # release build (realistic perf)
```

Or directly:

```
maturin develop
maturin develop --release
```

`maturin develop` compiles the Rust extension and installs it into the
currently-active Python environment — run tests from the same env.

### Test

```
make test                          # full suite
pytest -v -k multiline             # filter by name
pytest -v tests/test_loads.py      # single file
```

The `test_conformance.py` module runs the cross-language fixture suite
from `ktav-lang/spec`. It resolves the spec directory via:

1. `KTAV_SPEC_DIR` environment variable, if set.
2. `../spec` relative to the repo root (the sibling-clone layout).

When neither resolves, conformance tests **skip** rather than fail, so
you can still work in an sdist-only checkout.

### Lint + typecheck

```
make lint         # ruff check + ruff format --check
make typecheck    # mypy --strict
make rust-lint    # cargo fmt --check + cargo clippy -D warnings
make all          # lint + typecheck + rust-lint + test
```

CI runs the same commands; run `make all` locally before pushing.

### Pre-commit

```
pre-commit install
pre-commit run --all-files
```

This wires ruff, mypy, rustfmt, clippy, and the standard whitespace /
EOL hooks into `git commit`.

## Philosophy

Ktav's motto: **"be the config's friend, not its examiner."** Before
proposing a new Python-specific feature, ask:

- Does this add a new rule the reader must hold in their head?
- Could this live in user code instead of the library?
- Does this erode the "no magic types" principle?

New rules are costly. Reject everything that doesn't clearly belong.

## Language policy

This repo participates in the org-wide three-language policy (EN / RU /
ZH). Every prose file lives in three parallel versions — see
[`ktav-lang/.github/AGENTS.md`](https://github.com/ktav-lang/.github/blob/main/AGENTS.md)
for the naming convention and the "update all three in one commit"
rule.

If you don't speak one of the languages, still open the PR in the
language you do speak, mark the untouched versions with
`<!-- TODO: sync with <name>.md -->` at the top, and a maintainer or
community contributor will fill the gap before merge.
