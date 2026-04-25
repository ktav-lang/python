# ktav (Python)

> Python bindings for [Ktav](https://github.com/ktav-lang/spec) — a plain
> configuration format. JSON-shape, no quotes, no commas, dotted keys.
> Powered by Rust under the hood.

**Languages:** **English** · [Русский](README.ru.md) · [简体中文](README.zh.md)

**Specification:** this package implements **Ktav 0.1**. The format is
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
port:i 8080
ratio:f 0.75
tls: true
tags: [
    prod
    eu-west-1
]
db.host: primary.internal
db.timeout:i 30
"""

cfg = ktav.loads(src)

service: str = cfg["service"]
port:    int = cfg["port"]
ratio: float = cfg["ratio"]
tls:    bool = cfg["tls"]
tags: list[str] = cfg["tags"]
db_host:    str = cfg["db"]["host"]
db_timeout: int = cfg["db"]["timeout"]
```

### Walk — dispatch on the runtime type

```python
for k, v in cfg.items():
    if v is None:              kind = "null"
    elif isinstance(v, bool):  kind = f"bool={v}"   # bool first — True is also an int!
    elif isinstance(v, int):   kind = f"int={v}"
    elif isinstance(v, float): kind = f"float={v}"
    elif isinstance(v, str):   kind = f"str={v!r}"
    elif isinstance(v, list):  kind = f"array({len(v)})"
    elif isinstance(v, dict):  kind = f"object({len(v)})"
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
# port:i 8443
# tls: true
# ratio:f 0.95
# upstreams: [
#     { host: a.example  port:i 1080 }
#     { host: b.example  port:i 1080 }
# ]
# notes: null
```

A complete runnable version lives in [`examples/basic.py`](examples/basic.py).

Four entry points mirror the standard library `json` module:

| Function              | Purpose                                      |
|-----------------------|----------------------------------------------|
| `ktav.loads(s)`       | Parse a Ktav string (or UTF-8 `bytes`).      |
| `ktav.dumps(obj)`     | Serialise a native Python value.             |
| `ktav.load(fp)`       | Parse from a file-like object.               |
| `ktav.dump(obj, fp)`  | Serialise to a file-like object.             |

`load` / `dump` accept both text-mode and binary-mode files.

## Type mapping

| Ktav                 | Python   |
|----------------------|----------|
| `null`               | `None`   |
| `true` / `false`     | `bool`   |
| `:i <digits>`        | `int`    |
| `:f <number>`        | `float`  |
| bare scalar          | `str`    |
| `[ ... ]`            | `list`   |
| `{ ... }`            | `dict`   |

Ktav keeps **"no magic types"** — a bare `port: 8080` stays a string at
the parser level. Use the typed markers `:i` / `:f` when you want
numbers, or type-coerce at the application layer.

`dict` preserves insertion order (Python 3.7+ guarantee), matching the
ordered-object semantics of Ktav.

Serialisation is the inverse:

- Python `int` → `:i` marker (including arbitrary-precision bigints).
- Python `float` → `:f` marker (decimal point always present;
  `NaN` / `±Infinity` are rejected — Ktav 0.1.0 does not represent them).
- Python `tuple` is accepted as an array, for symmetry with `list`.
- Non-`str` keys in a `dict` raise `KtavEncodeError`.

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

## Related projects

- [`ktav-lang/spec`](https://github.com/ktav-lang/spec) — canonical
  format specification and language-agnostic conformance test suite.
- [`ktav-lang/rust`](https://github.com/ktav-lang/rust) — reference Rust
  implementation. These Python bindings are a thin PyO3 wrapper around
  that crate.

## Versioning

This package follows [Semantic Versioning](https://semver.org/) with the
pre-1.0 convention that a MINOR bump is breaking. The package version
and the `ktav` crate version move together. `ktav.__spec_version__`
reports the Ktav format version this binding supports.

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for the dev setup, test layout,
and the contribution workflow.

## Support the project

The author has many ideas that could be broadly useful to IT worldwide —
not limited to Ktav. Realizing them requires funding. If you'd like to
help, please reach out at **phpcraftdream@gmail.com**.

## License

MIT. See [LICENSE](LICENSE).
