# ktav (Python)

[![PyPI](https://img.shields.io/pypi/v/ktav?style=flat-square&logo=pypi&logoColor=white&label=PyPI)](https://pypi.org/project/ktav/)
[![CI](https://img.shields.io/github/actions/workflow/status/ktav-lang/python/CI.yml?style=flat-square&logo=github&label=CI)](https://github.com/ktav-lang/python/actions)
![License: MIT OR Apache-2.0](https://img.shields.io/badge/license-MIT%20OR%20Apache--2.0-blue?style=flat-square)
[![Playground](https://img.shields.io/badge/playground-try%20online-7c3aed?style=flat-square&logo=rocket&logoColor=white)](https://ktav-lang.github.io/)

> Python bindings for [Ktav](https://github.com/ktav-lang/spec) — a plain
> configuration format. JSON-shape, no required quotes, no commas, dotted keys.
> Powered by Rust under the hood.

**Languages:** **English** · [Русский](docs/ru/README.ru.md) · [简体中文](docs/zh/README.zh.md)

**Playground:** convert JSON / YAML / TOML / INI ⇄ Ktav in your browser at **[ktav-lang.github.io](https://ktav-lang.github.io/)**.

**Specification:** this package implements **Ktav**. The format is
versioned and maintained independently of this package — see
[`ktav-lang/spec`](https://github.com/ktav-lang/spec) for the formal
document.

---

## Install

```
pip install ktav
```

Wheels are published for every major platform and every supported
Python version:

- **Linux** (manylinux + musllinux) — `x86_64`, `aarch64`
- **macOS** — `x86_64`, `arm64` (Apple Silicon)
- **Windows** — `x64`, `arm64`

Python **3.9+** is required. The wheels target the stable ABI
(`abi3-py39`), so a single wheel per platform serves every supported
CPython release.

If no prebuilt wheel matches your platform, `pip` falls back to the
source distribution and compiles it locally — you need a Rust toolchain
(`rustup`) and the Python development headers.

## Quick start

### Parse — read typed fields straight off the dict

```python
import ktav

src = """
service: web
port: 8080
ratio: 0.75
tls: true
tags: [
    prod
    eu-west-1
]
db.host: primary.internal
db.timeout: 30
"""

cfg = ktav.loads(src)

service: str = cfg["service"]
port: int = cfg["port"]
ratio: float = cfg["ratio"]
tls: bool = cfg["tls"]
tags: list[str] = cfg["tags"]
db_host: str = cfg["db"]["host"]
db_timeout: int = cfg["db"]["timeout"]
```

### Walk — dispatch on the runtime type

```python
for k, v in cfg.items():
    if v is None:
        kind = "null"
    elif isinstance(v, bool):
        kind = f"bool={v}"  # bool first — True is also an int!
    elif isinstance(v, int):
        kind = f"int={v}"
    elif isinstance(v, float):
        kind = f"float={v}"
    elif isinstance(v, str):
        kind = f"str={v!r}"
    elif isinstance(v, list):
        kind = f"array({len(v)})"
    elif isinstance(v, dict):
        kind = f"object({len(v)})"
    print(f"{k} -> {kind}")
```

### Build & render — construct a document in code

```python
doc = {
    "name": "frontend",
    "port": 8443,
    "tls": True,
    "ratio": 0.95,
    "upstreams": [
        {"host": "a.example", "port": 1080},
        {"host": "b.example", "port": 1080},
    ],
    "notes": None,
}
text = ktav.dumps(doc)
# name: frontend
# port: 8443
# tls: true
# ratio: 0.95
# upstreams: [
#     { host: a.example  port: 1080 }
#     { host: b.example  port: 1080 }
# ]
# notes: null
```

A complete runnable version lives in [`examples/basic.py`](examples/basic.py).

### Format — normalise a file, keep the comments

```python
import ktav

print(ktav.format(open("config.ktav").read()))
```

`ktav.format` rewrites a document in canonical form (spec § 5.9) while
preserving every comment verbatim. Blank-line runs collapse to one and
blank padding inside brackets is dropped, so formatting is a fixed
point — safe to run in a pre-commit hook. Key order is never changed.

Three functions produce canonical output and they differ in what they
accept and what they keep:

| | input | comments | blank lines |
| --- | --- | --- | --- |
| `ktav.format(src)` | source text | **kept** | **kept** (runs collapse to one) |
| `ktav.canonical_from_source(src)` | source text | dropped | dropped |
| `ktav.emit_canonical(obj)` | a Python object | none to keep | none to keep |

Pick by what you are holding: `emit_canonical` when you have an object,
`canonical_from_source` when you have text and want no Python value
built in between, `format` when you want the document's own comments and
grouping to survive.

Unlike the JavaScript bindings, `canonical_from_source` buys you no extra
numeric fidelity here — Python distinguishes `int` from `float`, so the
Ktav Integer/Float distinction survives `loads`, and
`emit_canonical(loads(src))` produces the same bytes as
`canonical_from_source(src)`. Both spell a float by the canonical rule
(§ 5.9.8) rather than by copying the source, so `1.23456789012345678901`
becomes `1.2345678901234567` down either path.

`ktav.dumps_force_strings(obj)` renders like `dumps` but coerces every
leaf scalar — integer, float, bool, null — to a String via the raw `::`
marker. Compounds keep their structure.

Four entry points mirror the standard library `json` module:

| Function              | Purpose                                      |
|-----------------------|----------------------------------------------|
| `ktav.loads(s)`       | Parse a Ktav string (or UTF-8 `bytes`).      |
| `ktav.dumps(obj)`     | Serialise a native Python value.             |
| `ktav.load(fp)`       | Parse from a file-like object.               |
| `ktav.dump(obj, fp)`  | Serialise to a file-like object.             |

`load` / `dump` accept both text-mode and binary-mode files.

For validation at trust boundaries, `ktav.loads_strict(s)` applies the
specification's canonical-scalar rules and raises `KtavDecodeError` for a
lossy scalar spelling. Canonical writer forms such as `1e-3` and `1e10` are
accepted and produce the same native values as `loads`.

## Type mapping

| Ktav                 | Python   |
|----------------------|----------|
| `null`               | `None`   |
| `true` / `false`     | `bool`   |
| bare integer         | `int`    |
| bare decimal         | `float`  |
| other scalar         | `str`    |
| `[ ... ]`            | `list`   |
| `{ ... }`            | `dict`   |

Ktav types numbers by **lexical form** — a bare `port: 8080` is an
`int`, `ratio: 0.5` a `float`, and anything that isn't a bare number
stays a `str`. Force a numeric-looking value to stay a string with
`::` (`zip:: 01007`).

`dict` preserves insertion order (Python 3.7+ guarantee), matching the
ordered-object semantics of Ktav.

Serialisation is the inverse:

- Python `int` → bare integer (including arbitrary-precision bigints).
- Python `float` → bare decimal (decimal point always present;
  `NaN` / `±Infinity` are rejected — Ktav does not represent them).
- Python `tuple` is accepted as an array, for symmetry with `list`.
- Non-`str` keys in a `dict` raise `KtavEncodeError`.

## Key escaping

Since spec 0.6.4 a literal `.` or `:` inside a key segment is written
with a backslash:

```text
a\.b: v
a\:b: v
x.y\.z: v
a."b.c".d: v
"\u0041": v
```

A literal backslash in a key is `\\`. Since spec 0.7, a whole segment
may instead use double quotes, single quotes or backticks. Quotes only
delimit key segments, not values; `\uXXXX` decodes a Unicode code point.

## Errors

```python
import ktav

try:
    ktav.loads("x: [")
except ktav.KtavDecodeError as e:
    print("decode:", e)

try:
    ktav.dumps({"v": float("nan")})
except ktav.KtavEncodeError as e:
    print("encode:", e)

# Catching the base class catches either.
try:
    ktav.loads("a: 1\na: 2")
except ktav.KtavError:
    ...
```

| Exception           | Raised by   | Base                |
|---------------------|-------------|---------------------|
| `KtavError`         | (base)      | `Exception`         |
| `KtavDecodeError`   | `loads` / `load` | `KtavError`    |
| `KtavEncodeError`   | `dumps` / `dump` | `KtavError`    |

Since 0.7.1 every raised instance also carries the structured error
envelope as attributes: `error`, `reason`, `line`, `line_text`, `span`,
`path`, `body`, `canonical`, `spec_section`. Absent information is
`None`, never a missing attribute. `span` is `{"start": …, "end": …}`
byte offsets into the UTF-8 source; `path` is the list of exact decoded
key segments (a key literally named `a.b` is one segment, never split).
`str(e)` stays a human-readable message — the raw envelope is never
substituted for it.

`e.message` carries that same text as an attribute, so **`str(e) ==
e.message`**. It is redundant here by design: this binding has always
used the core's own rendering for `str(e)`, and the attribute exists so
the envelope has the same ten-field shape in Python that it has in every
other language — where `message` is the only way to reach the text. Use
it rather than rebuilding a sentence from `error`, `line` and `body`: a
reassembled message differs between bindings, and this one does not.

## Philosophy

Ktav is intentionally small. Its five design principles
(from [`spec/CONTRIBUTING.md`](https://github.com/ktav-lang/spec/blob/main/CONTRIBUTING.md)):

1. **Locality** — a line's meaning does not depend on another line.
2. **One sentence** — any new rule fits in one sentence of the spec.
3. **No whitespace sensitivity** (line breaks aside).
4. **No magic types** — the format never decides `"8080"` means a number.
5. **Explicit over clever** — `::` is verbose on purpose.

The Python bindings honour this: they add no schema inference, no
auto-casting, no defaulting. If you want typing, you do it at the
boundary with your own tool — `pydantic`, `dataclasses`, `attrs` —
against the native Python structures this library returns.

## Other Ktav implementations

- [`spec`](https://github.com/ktav-lang/spec) — specification + conformance suite
- [`rust`](https://github.com/ktav-lang/rust) — reference Rust crate (`cargo add ktav`); these Python bindings are a thin PyO3 wrapper around it
- [`csharp`](https://github.com/ktav-lang/csharp) — C# / .NET (`dotnet add package Ktav`)
- [`golang`](https://github.com/ktav-lang/golang) — Go (`go get github.com/ktav-lang/golang`)
- [`java`](https://github.com/ktav-lang/java) — Java / JVM (`io.github.ktav-lang:ktav` on Maven Central)
- [`js`](https://github.com/ktav-lang/js) — JS / TS (`npm install @ktav-lang/ktav`)
- [`php`](https://github.com/ktav-lang/php) — PHP (`composer require ktav-lang/ktav`)

## Versioning

This package follows [Semantic Versioning](https://semver.org/) with the
pre-1.0 convention that a MINOR bump is breaking. The package version
and the `ktav` crate version move together. `ktav.__spec_version__`
reports the Ktav format version this binding supports.

## Development

See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for the dev setup, test layout,
and the contribution workflow.

## Support the project

The author has many ideas that could be broadly useful to IT worldwide —
not limited to Ktav. Realizing them requires funding. If you'd like to
help, please reach out at **phpcraftdream@gmail.com**.

## License

MIT OR Apache-2.0. See [LICENSE-MIT](LICENSE-MIT) and [LICENSE-APACHE](LICENSE-APACHE).
