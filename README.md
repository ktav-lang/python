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

The default backend is native and includes our bundled Rust core in a matching platform wheel. No Python runtime dependency is required. Wheels target Python 3.9+ on supported platforms.

If no wheel matches, install from source: the native extension is compiled with Rust through maturin, so a Rust toolchain and Python development headers are needed. Source installation does not switch to pure mode.

### Pure Python

For a universal wheel, install the existing `py3-none-any` artifact explicitly:

```
pip install ./ktav-0.8.1-py3-none-any.whl
```

Then select the pure API directly:

```
from ktav import pure




doc = pure.loads("server.port: 8080")
text = pure.dumps({"server": {"port": 8080}})
formatted = pure.format(text)
```

The pure backend provides the full parser, writer, formatter, and Ktav errors using only the Python standard library. It does not require third-party packages and does not load `_core`, WASM, or invoke network or subprocesses. It is explicitly selected; the native default never silently falls back to it.

`tomli` may appear in test or development extras for tooling on older Python versions; it is not a runtime dependency.

```python
from ktav import pure

config = pure.loads(open("config.ktav").read())
text = pure.dumps({"port": 8080})
formatted = pure.format(open("config.ktav").read())
```

Pure mode implements the full public operation set — `loads`, `loads_strict`, `dumps`, `emit_canonical`, `dumps_force_strings`, `format`, `canonical_from_source` (plus `load`/`dump`) — with the same ten-field error envelope, against spec 0.8.1. Prefer it when you have no Rust toolchain, when no wheel exists for your platform, for embedding, or when you want an implementation you can audit in pure Python. The honest tradeoff: pure mode runs at Python speed, not the native extension's — no speed claims are made either way. There is no global backend flag and no silent fallback: you choose a backend by choosing which module you import.

Since 0.8.1 the pure backend also ships as a real install artifact: the universal pure wheel `ktav-0.8.1-py3-none-any.whl` (same distribution name, same version) is published on PyPI alongside the native platform wheels. To install it, download/select the pure wheel (`py3-none-any`) from the release or PyPI files; `pip` prefers a matching platform wheel automatically when one exists. The pure wheel installs with no Rust toolchain, no compiler and no maturin, and provides exactly the `ktav.pure` backend — the native top-level functions then raise a clear `ImportError` pointing at `from ktav import pure`.

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

> **Unreleased (0.9 preparation):** These editing APIs and updated diagnostics are not included in published 0.8.1 packages. Native backends require the pinned 0.9 core (C ABI 2 for C-FFI); pure backends remain standalone.

### Source edits — `edit_value` / `edit_value_segments`

```python
import ktav

out = ktav.edit_value("port: 8080\nhost: db\n", "port", 9090)
# "port: 9090\nhost: db\n"

out = ktav.edit_value_segments("a: {x: 1, y: 2}\n", ["a", "y"], {"n": [1]})
# "a: {x: 1, y: {n: [1]}}\n"
```

`edit_value` takes a textual path (`key1.key2.0.key4`): inside a
segment `\.` is a literal dot and `\\` a literal backslash; any other
escape raises `KtavInvalidPathError` whose `body` is the decimal UTF-8
byte offset of the problem. `edit_value_segments` takes
already-decoded literal segments with no extra unescaping — a numeric
segment is a string key inside an Object and a zero-based index inside
an Array. Only replacement of an existing value is supported; missing
keys, out-of-bounds indexes and descent through a scalar raise
`KtavNotFoundError`.

The edit is a source splice, not a parse→mutate→serialize of the whole
document: comments, key spelling, order, whitespace, BOM and
CR/LF/CRLF outside the effective change are preserved byte-for-byte,
dotted/inline/block forms are kept, and an equal replacement is a
byte-identical no-op — even for noncanonical spelling. Every
successful patch is re-parsed and semantically verified. When no
lossless patch exists (noncontiguous dotted/reopened targets, internal
comments under structural replacement, an unrepresentable value in the
target context) the call raises `KtavUnsupportedError` instead of
guessing. Long or multiline replacements unfold only the touched
inline wrappers; untouched nested branches stay inline. Both the
native and the pure backend implement the identical semantics.

### Source-edit cookbook

These examples describe the unreleased 0.9 API, not the published 0.8.1 package. They replace existing values only: keys are not renamed, missing paths are not created, and entries are not removed. Each snippet is independent; Rust `?` assumes an enclosing `Result`-returning function. Go examples panic only for these fixed, known-valid inputs; applications should handle the returned error.

The binding examples use the standalone pure backend, without a native binary. Native entry points accept the same paths and values: `ktav.EditValue` (Go), `Ktav.editValue` (Java), `KtavApi.EditValue(..., KtavBackend.Native)` (C#), `Ktav::editValue` (PHP), the package's native/FFI exports (JS), and `ktav.edit_value` (Python). C-ABI backends require ABI 2; PyO3/N-API/WASM require the matching preparing-0.9 core. Bun/Deno FFI calls return promises: use `await`; pure/Node/WASM examples shown here are synchronous.

```python
import ktav.pure as ktav
```

#### 1. Dotted deployment settings

Only the address changes; the comment, dotted form and neighbouring user entry remain byte-for-byte unchanged.

```python
source = "## deployment\ntargets.storagehost.address: old\ntargets.storagehost.user: mcp-agent\n"
updated = ktav.edit_value(source, "targets.storagehost.address", "192.168.0.88:22")
```

Result:

```ktav
## deployment
targets.storagehost.address: 192.168.0.88:22
targets.storagehost.user: mcp-agent
```

#### 2. Literal dots: textual path or segments

The quoted source key is literally `a.b`. The textual path escapes its dot; the segments call passes the decoded key directly. Both calls return the same result.

```python
source = "\"a.b\": {port: 80}\n"
updated = ktav.edit_value(source, "a\\.b.port", 90)
same = ktav.edit_value_segments(source, ["a.b", "port"], 90)
```

Result:

```ktav
"a.b": {port: 90}
```

#### 3. A leaf inside a mixed-form array

`0` is an array index here. Inside an Object, the same segment would address the key named `0`; untouched containers remain inline.

```python
source = "servers: [{host: old, keep: yes}, standby]\n"
updated = ktav.edit_value_segments(source, ["servers", "0", "host"], "new")
```

Result:

```ktav
servers: [{host: new, keep: yes}, standby]
```

#### 4. A numeric-looking String stays a String

The replacement is a String, not an Integer. The raw marker preserves that distinction. Supply a typed Integer when a numeric value is intended.

```python
source = "port: 8080\n"
updated = ktav.edit_value(source, "port", "9090")
```

Result:

```ktav
port:: 9090
```

#### 5. Multiline replacement: expand only what is necessary

The changed array expands with four-space indentation. The untouched object stays inline, and verbatim string contents are not reindented.

```python
source = "a: [old, {keep: yes}]\n"
updated = ktav.edit_value(source, "a.0", "x\ny")
```

Result:

```ktav
a: [
    ((
x
y
    ))
    {keep: yes}
]
```

#### 6. No-op preserves noncanonical spelling

The Integer value is already 1. Equality returns the original bytes, including `+1` and the original separator spacing; readability thresholds are bypassed.

```python
source = "n  : +1\n"
updated = ktav.edit_value(source, "n", 1)
assert updated == source
```

Result:

```ktav
n  : +1
```

#### 7. BOM, CRLF and an unterminated final line

The returned string keeps the BOM and CRLF, and does not gain a final newline. Its escaped representation is shown to make the bytes visible.

```python
source = "\ufeffport: 8080\r\nhost: db"
updated = ktav.edit_value(source, "port", 9090)
```

Result:

```text
"\uFEFFport: 9090\r\nhost: db"
```

Expansion is deterministic: a multiline replacement, growth beyond `max(100, original line length)`, or at least four escapes with at least 25% encoding overhead for an individual replacement string. Width counts Unicode scalar values, not UTF-8 bytes or terminal columns. An already-long line without growth is kept. New levels use four spaces and the source EOL. If CR or a `))` data line prevents lossless standalone encoding, a valid inline candidate is retained; these characters do not automatically make every inline edit unsupported.

#### 8. Exact Integer replacement

The source Integer domain is signed 64-bit. This value exceeds JavaScript's safe-Number range but fits i64; use an exact host representation, not a rounded floating-point value. A typed Integer outside i64 cannot be preserved as an Integer in source and is refused instead of truncated. Use a String when a large identifier is text. Float identity distinguishes negative and positive zero; Object no-op equality ignores key order, while Array order remains significant.

```python
updated = ktav.edit_value("n: 1\n", "n", 9007199254740993)
```

```ktav
n: 9007199254740993
```

### Diagnostics and safe failures in 0.9

Source coordinates are UTF-8 byte offsets, including a BOM; spans are half-open `[start, end)`, and lines are 1-based. LF, lone CR and CRLF are handled, with CRLF counted as one terminator. A Unicode character may occupy several bytes.

An unfinished `a: [\n` reports `UnclosedCompound`, line 1 and span `3..5`: the span begins at the innermost unmatched opener, not the start of its key or line. For raw bytes `61 3A 20 FF` (`a: ` followed by invalid UTF-8), validation reports `InvalidUtf8`, line 1 and a covering span `3..4`; `line_text` is null rather than fabricated by lossy decoding. UTF-8 validation precedes grammar processing.

A malformed textual path, including an empty textual path or empty textual segment, is `EditInvalidPath`; its offset is measured in the path's UTF-8 bytes. An empty segments list, missing key, out-of-range index or scalar descent is `EditNotFound`. Object numeric segments remain keys; array indexes use ASCII digits, allow leading zeros and reject signs.

Whole dotted/reopened intermediate objects may occupy several physical ranges and are `EditUnsupported`; their existing leaves can still be edited. Replacing a container must not discard interior comments. No failed call returns a partial patch or changes the supplied source. The returned text is re-parsed and semantically checked: the target must equal the replacement and the rest of the value tree must remain equal.

For bindings, invalid source is reported with the ordinary parser envelope before path validation. Malformed wire payloads are `Message` errors without invented source coordinates. The wire envelope has `error`, `reason`, `line`, `line_text`, `span`, `path`, `body`, `canonical`, `spec_section` and `message`; host accessor names are documented in the errors section. `body` carries the decimal path-byte offset for `EditInvalidPath`, null for `EditNotFound`, and the refusal reason for `EditUnsupported`.

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
| bare integer (fits signed 64-bit) | `int`    |
| integer beyond 64-bit             | `str`    |
| bare decimal         | `float`  |
| other scalar         | `str`    |
| `[ ... ]`            | `list`   |
| `{ ... }`            | `dict`   |

Ktav types numbers by **lexical form** — a bare `port: 8080` is an
`int`, `ratio: 0.5` a `float`, and anything that isn't a bare number
stays a `str`. Force a numeric-looking value to stay a string with
`::` (`zip:: 01007`).

The Integer domain matches the native extension's (signed 64-bit): an
integer literal beyond `i64` parses as a `str`, re-emitted via the raw
`::` marker so it stays a string — the same behaviour in both backends.

`dict` preserves insertion order (Python 3.7+ guarantee), matching the
ordered-object semantics of Ktav.

Serialisation is the inverse:

- Python `int` → bare integer (including arbitrary-precision bigints;
  reading such a literal back yields a `str` — see above).
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

Both backends raise the same exceptions carrying the identical
ten-field envelope. One deliberate delta: for a `str` input containing
literal lone surrogates, pure mode raises `KtavDecodeError` with the
error category `InvalidUtf8` and a nonempty span over the malformed
bytes, where the native extension surfaces a `UnicodeEncodeError`.

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

Two backends ship in this package. The **native** backend is the
default: the top-level `ktav` API is a thin PyO3 wrapper around the
Rust core (0.8.1). The **pure** backend, `ktav.pure`, is a complete
parser and generator in pure Python — no compiled extension required.
There is no global backend flag and no silent fallback: you choose a
backend by importing it, and CI asserts byte-identical canonical
output across both. The pure backend also ships as the universal pure
wheel (`ktav-0.8.1-py3-none-any.whl`), published alongside the native
platform wheels.

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
