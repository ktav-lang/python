# Security Policy

**Languages:** **English** · [Русский](SECURITY.ru.md) · [简体中文](SECURITY.zh.md)

## Supported versions

While this package is pre-1.0 only the **latest published minor** is
maintained. Security fixes land on `main` and ship in a PATCH
release within a few days.

| Version | Supported          |
|---------|--------------------|
| 0.1.x   | ✅                 |
| older   | ❌ — upgrade first |

## Reporting a vulnerability

**Please do not open a public issue for security problems.**

Email **phpcraftdream@gmail.com** with:

- A short description of the vulnerability.
- Steps or a snippet to reproduce it (Ktav input that triggers the
  behaviour, the affected API — `loads` / `dumps` / file variants,
  expected vs actual).
- The ktav version you observed it on (`pip show ktav` output is
  usually enough), plus the OS / Python version so we know which
  abi3 wheel was in use.
- Your disclosure timeline preference, if you have one.

You should get an acknowledgement within **72 hours**. A published
fix typically follows within **a week** for high-impact issues, longer
if the fix needs to coordinate with the Rust crate or the format spec.

## Scope

Issues that count as security problems for this package:

- Out-of-bounds reads / writes or panics in the compiled `_core`
  extension module (PyO3 catches Rust panics and re-raises them as
  `pyo3_runtime.PanicException`, so the interpreter survives — but a
  panic on trusted input is still a bug worth reporting here).
- Runaway memory or CPU when parsing crafted input.
- Any behaviour that allows crafted Ktav input to escape the expected
  value-domain (arbitrary object construction, memory disclosure
  through the extension, etc.).
- Segfaults that bypass PyO3's panic bridge — these indicate real
  `unsafe` soundness issues and take priority.

Issues that are **not** security problems here — please use regular
issues for these:

- Performance regressions without crash / hang characteristics.
- Exception type mismatches that aren't exploitable (e.g. `ValueError`
  where `TypeError` would read better).
- Problems in the Ktav format itself — those belong in
  [`ktav-lang/spec`](https://github.com/ktav-lang/spec).
