"""Ktav — a plain configuration format. Python bindings.

The public entry points mirror the standard library's ``json`` module::

    import ktav

    config = ktav.loads(open("config.ktav").read())
    text = ktav.dumps({"port": 8080, "name": "service"})
    formatted = ktav.format(open("config.ktav").read())  # normalise, keep comments

File-like convenience wrappers live alongside:

    with open("config.ktav") as f:
        config = ktav.load(f)

    with open("config.ktav", "w") as f:
        ktav.dump(config, f)

See https://github.com/ktav-lang/spec for the format specification.
"""

from __future__ import annotations

from typing import IO, TYPE_CHECKING, Any, NoReturn

if TYPE_CHECKING:
    from ktav._core import (
        KtavAlreadyExistsError,
        KtavDecodeError,
        KtavEditError,
        KtavEncodeError,
        KtavError,
        KtavInvalidPathError,
        KtavNotFoundError,
        KtavUnsupportedError,
        __spec_version__,
        __version__,
    )
    from ktav._core import (
        canonical_from_source as _canonical_from_source,
    )
    from ktav._core import (
        dumps as _dumps,
    )
    from ktav._core import (
        dumps_force_strings as _dumps_force_strings,
    )
    from ktav._core import (
        edit_value as _edit_value,
    )
    from ktav._core import (
        edit_value_segments as _edit_value_segments,
    )
    from ktav._core import (
        emit_canonical as _emit_canonical,
    )
    from ktav._core import (
        format as _format,
    )
    from ktav._core import (
        insert_value as _insert_value,
    )
    from ktav._core import (
        insert_value_segments as _insert_value_segments,
    )
    from ktav._core import (
        loads as _loads,
    )
    from ktav._core import (
        loads_strict as _loads_strict,
    )
    from ktav._core import (
        remove_value as _remove_value,
    )
    from ktav._core import (
        remove_value_segments as _remove_value_segments,
    )
    from ktav._core import (
        rename_key as _rename_key,
    )
    from ktav._core import (
        rename_key_segments as _rename_key_segments,
    )

_CORE_NAMES = (
    "KtavAlreadyExistsError",
    "KtavDecodeError",
    "KtavEditError",
    "KtavEncodeError",
    "KtavError",
    "KtavInvalidPathError",
    "KtavNotFoundError",
    "KtavUnsupportedError",
    "__spec_version__",
    "__version__",
    "canonical_from_source",
    "dumps",
    "dumps_force_strings",
    "edit_value",
    "edit_value_segments",
    "insert_value",
    "insert_value_segments",
    "remove_value",
    "remove_value_segments",
    "rename_key",
    "rename_key_segments",
    "emit_canonical",
    "format",
    "loads",
    "loads_strict",
)
_NATIVE_FUNCS = (
    "canonical_from_source",
    "dumps",
    "dumps_force_strings",
    "edit_value",
    "edit_value_segments",
    "insert_value",
    "insert_value_segments",
    "remove_value",
    "remove_value_segments",
    "rename_key",
    "rename_key_segments",
    "emit_canonical",
    "format",
    "loads",
    "loads_strict",
)
_ERROR_CLASSES = (
    "KtavAlreadyExistsError",
    "KtavDecodeError",
    "KtavEditError",
    "KtavEncodeError",
    "KtavError",
    "KtavInvalidPathError",
    "KtavNotFoundError",
    "KtavUnsupportedError",
)
_CORE_CHECKED = False
_HAS_CORE: bool


def _no_native(name: str) -> Any:
    def stub(*args: Any, **kwargs: Any) -> Any:
        if name in (
            "edit_value",
            "edit_value_segments",
            "insert_value",
            "insert_value_segments",
            "remove_value",
            "remove_value_segments",
            "rename_key",
            "rename_key_segments",
        ):
            raise ImportError(
                f"ktav.{name} requires a ktav._core built against the"
                " source-edit 0.9 core; the installed extension does not"
                " export it (an older native binary never falls back to the"
                " pure backend silently). Use ktav.pure.edit_value instead:"
                " from ktav import pure."
            )
        raise ImportError(
            f"ktav.{name} requires the native ktav._core extension, which is"
            " not installed; use the pure-Python backend instead:"
            " from ktav import pure (module ktav.pure)."
        )

    stub._ktav_stub = True  # type: ignore[attr-defined]
    return stub


def _load_core() -> bool:
    """Resolve the native backend once, only when a native API is used."""
    global _CORE_CHECKED, _HAS_CORE
    if _CORE_CHECKED:
        return _HAS_CORE
    from importlib import import_module

    try:
        _core = import_module("._core", __name__)
    except ImportError:
        from ktav._pure import (
            KtavAlreadyExistsError,
            KtavDecodeError,
            KtavEditError,
            KtavEncodeError,
            KtavError,
            KtavInvalidPathError,
            KtavNotFoundError,
            KtavUnsupportedError,
            __spec_version__,
            __version__,
        )

        globals().update(
            KtavAlreadyExistsError=KtavAlreadyExistsError,
            KtavDecodeError=KtavDecodeError,
            KtavEditError=KtavEditError,
            KtavEncodeError=KtavEncodeError,
            KtavError=KtavError,
            KtavInvalidPathError=KtavInvalidPathError,
            KtavNotFoundError=KtavNotFoundError,
            KtavUnsupportedError=KtavUnsupportedError,
            __spec_version__=__spec_version__,
            __version__=__version__,
        )
        for _name in _NATIVE_FUNCS:
            globals()["_" + _name] = _no_native(_name)
        _HAS_CORE = False
    else:
        for _name in _CORE_NAMES:
            if _name in _NATIVE_FUNCS:
                continue
            # A stale native binary predating the source-edit 0.9 symbols
            # must degrade into a LOUD stub, never a silent pure fallback.
            value = getattr(_core, _name, None)
            if value is None and _name in _ERROR_CLASSES:
                from ktav import _pure as _puremod

                value = getattr(_puremod, _name)
            if value is None:
                value = _no_native(_name)
            globals()[_name] = value
        for _name in _NATIVE_FUNCS:
            value = getattr(_core, _name, None)
            globals()["_" + _name] = value if value is not None else _no_native(_name)
        _HAS_CORE = True
    _CORE_CHECKED = True
    return _HAS_CORE


def __getattr__(name: str) -> Any:
    """Загрузить выбранный модуль или явно запрошенный native API."""
    if name == "pure":
        from importlib import import_module

        return import_module(".pure", __name__)
    if name == "_HAS_CORE" or name in _CORE_NAMES:
        _load_core()
        try:
            return globals()[name]
        except KeyError:
            raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from None
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "KtavAlreadyExistsError",
    "KtavDecodeError",
    "KtavEditError",
    "KtavEncodeError",
    "KtavError",
    "KtavInvalidPathError",
    "KtavNotFoundError",
    "KtavUnsupportedError",
    "__spec_version__",
    "__version__",
    "canonical_from_source",
    "dump",
    "dumps",
    "dumps_force_strings",
    "edit_value",
    "edit_value_segments",
    "emit_canonical",
    "format",
    "insert_value",
    "insert_value_segments",
    "load",
    "loads",
    "loads_strict",
    "remove_value",
    "remove_value_segments",
    "rename_key",
    "rename_key_segments",
]


def _reraise_as_backend_error(exc: Any) -> NoReturn:
    """Re-raise a pure-backend decode error under the ACTIVE error class.

    The shared byte boundary runs before the native call, so its
    :class:`KtavDecodeError` would otherwise be the pure class while the
    backend advertised by this module is the native one — and
    ``except ktav.KtavDecodeError`` would miss it. The ten-field
    envelope is copied verbatim.
    """
    cls = globals().get("KtavDecodeError", type(exc))
    err = cls(str(exc))
    for name in (
        "error",
        "reason",
        "line",
        "line_text",
        "span",
        "path",
        "body",
        "canonical",
        "spec_section",
        "message",
    ):
        setattr(err, name, getattr(exc, name, None))
    raise err from exc


def _as_text(s: str | bytes | bytearray | memoryview) -> str:
    """UTF-8 byte boundary for every text entry point (§ 6.15).

    Raw bytes are validated (never lossily decoded) BEFORE any grammar
    processing, so a malformed tail cannot lose to an earlier grammar
    error and both backends raise the same structured ``InvalidUtf8``
    envelope with raw-byte offsets.
    """
    if isinstance(s, (bytes, bytearray, memoryview)):
        from ktav._pure._text import validate_utf8

        try:
            return validate_utf8(bytes(s))
        except Exception as exc:
            _reraise_as_backend_error(exc)
    return s


def loads(s: str | bytes | bytearray) -> Any:
    """Parse a Ktav document from a string (or UTF-8 bytes)."""
    _load_core()
    return _loads(_as_text(s))


def loads_strict(s: str | bytes | bytearray) -> Any:
    """Parse a Ktav document with strict canonical-scalar validation."""
    _load_core()
    return _loads_strict(_as_text(s))


def dumps(obj: Any) -> str:
    """Serialize ``obj`` as a Ktav document string.

    The top-level value must be a mapping (``dict``) or a sequence
    (``list`` / ``tuple``). Top-level Arrays render as bare
    item-per-line — no surrounding ``[...]`` brackets (spec § 5.0.1,
    added in 0.1.1). Raises :class:`KtavEncodeError` otherwise.
    """
    _load_core()
    return _dumps(obj)


def emit_canonical(obj: Any) -> str:
    """Emit the canonical (normalised) form of ``obj`` as a Ktav document.

    The output is byte-deterministic across all compliant implementations
    (spec § 5.9): numbers are normalised, redundant whitespace stripped,
    and inline forms expanded to multi-line. The top-level value must be
    a mapping (``dict``) or a sequence (``list`` / ``tuple``). Raises
    :class:`KtavEncodeError` otherwise.
    """
    _load_core()
    return _emit_canonical(obj)


def format(s: str | bytes | bytearray) -> str:
    """Format a Ktav document: text in, normalised text out.

    Normalises the document's structure to the canonical shape
    (spec § 5.9) while preserving every comment line and blank-line
    grouping. Comments survive verbatim (spec § 3.4: a comment owns a
    whole line); a run of two or more blank lines collapses to exactly
    one and blank padding immediately inside a bracket is dropped, so
    formatting is a fixed point: ``format(format(x)) == format(x)``.
    Key order is never changed (canonical form has no sorting rule).

    For a document with no comments and no blank lines the result
    equals :func:`emit_canonical` of its parse.

    Raises :class:`KtavDecodeError` on malformed input.
    """
    _load_core()
    return _format(_as_text(s))


def canonical_from_source(s: str | bytes | bytearray) -> str:
    """Re-emit a Ktav document in canonical form: text in, text out.

    The result equals ``emit_canonical(loads(s))``, but the document
    never becomes a Python object on the way, so spec § 5.9 stays
    decided in the one layer that owns it.

    Unlike :func:`format`, comments and blank lines do NOT survive —
    canonical form carries no trivia. Use :func:`format` to tidy a file
    a human will read, and this to produce a byte-stable form to hash,
    diff or store.

    Raises :class:`KtavDecodeError` on malformed input.
    """
    _load_core()
    return _canonical_from_source(_as_text(s))


def dumps_force_strings(obj: Any) -> str:
    """Serialize ``obj`` as a Ktav document with every scalar coerced to a String.

    Typed integers, typed floats, booleans, and ``None`` are flattened
    to their textual form and emitted via the raw ``::`` marker so the
    output round-trips back through the parser as the same string
    scalars. Compounds (``dict`` / ``list`` / ``tuple``) preserve their
    structure; only leaf scalars are coerced.

    Useful for "everything is a string" downstream consumers — e.g.
    environment variables, or diffs where the textual form is the
    canonical source of truth.

    Raises :class:`KtavEncodeError` on unsupported types or
    unrepresentable values.
    """
    _load_core()
    return _dumps_force_strings(obj)


def edit_value(source: str | bytes | bytearray, path: str, replacement: Any) -> str:
    r"""Replace the value at the textual ``path`` in ``source``.

    ``path`` is the dotted form (``key1.key2.0.key4``) where ``\\.``
    escapes a literal dot and ``\\\\`` a literal backslash; any other
    escape raises :class:`KtavInvalidPathError` whose ``body`` is the
    decimal UTF-8 byte offset of the problem. The source must parse;
    only the bytes of the target value (plus inline wrappers the layout
    rules force to unfold) change — comments, key spelling, whitespace,
    BOM and CR/LF/CRLF survive. An equal replacement is a byte-identical
    no-op.

    ``replacement`` is a native Python value. Raises
    :class:`KtavNotFoundError` when the path addresses nothing and
    :class:`KtavUnsupportedError` when no lossless splice exists.
    """
    _load_core()
    text = _as_text(source)
    _loads(text)
    return _edit_value(text, path, replacement)


def _backend_message_error(message: str) -> Any:
    """Создать Message-конверт под активным классом backend."""
    cls = globals().get("KtavEditError", KtavEditError)
    err = cls(message)
    err.error = "Message"
    err.reason = None
    err.line = None
    err.line_text = None
    err.span = None
    err.path = None
    err.body = None
    err.canonical = None
    err.spec_section = None
    err.message = message
    return err


def edit_value_segments(source: str | bytes | bytearray, segments: Any, replacement: Any) -> str:
    """:func:`edit_value` with already-decoded literal path segments.

    ``segments`` is a sequence of exact key strings — no additional
    unescaping. A numeric segment is a string key inside an Object and a
    zero-based ASCII-digits index inside an Array (leading zeros
    allowed, signs are not indexes). An empty sequence raises
    :class:`KtavNotFoundError`.
    """
    _load_core()
    text = _as_text(source)
    _loads(text)
    decoded = list(segments)  # materialize once — segments may be a generator
    if any(not isinstance(segment, str) for segment in decoded):
        raise _backend_message_error("edit path segments must be strings")
    return _edit_value_segments(text, decoded, replacement)


def insert_value(source: str | bytes | bytearray, path: str, replacement: Any) -> str:
    """Insert a value at the textual ``path`` in ``source``."""
    _load_core()
    text = _as_text(source)
    _loads(text)
    return _insert_value(text, path, replacement)


def insert_value_segments(source: str | bytes | bytearray, segments: Any, replacement: Any) -> str:
    """Insert a value using already-decoded literal path ``segments``."""
    _load_core()
    text = _as_text(source)
    _loads(text)
    decoded = list(segments)
    if any(not isinstance(segment, str) for segment in decoded):
        raise _backend_message_error("edit path segments must be strings")
    return _insert_value_segments(text, decoded, replacement)


def remove_value(source: str | bytes | bytearray, path: str) -> str:
    """Remove the value at the textual ``path`` in ``source``."""
    _load_core()
    text = _as_text(source)
    _loads(text)
    return _remove_value(text, path)


def remove_value_segments(source: str | bytes | bytearray, segments: Any) -> str:
    """Remove a value using already-decoded literal path ``segments``."""
    _load_core()
    text = _as_text(source)
    _loads(text)
    decoded = list(segments)
    if any(not isinstance(segment, str) for segment in decoded):
        raise _backend_message_error("edit path segments must be strings")
    return _remove_value_segments(text, decoded)


def rename_key(source: str | bytes | bytearray, path: str, new_key: str) -> str:
    """Rename the key at the textual ``path`` in ``source``."""
    _load_core()
    text = _as_text(source)
    _loads(text)
    return _rename_key(text, path, new_key)


def rename_key_segments(source: str | bytes | bytearray, segments: Any, new_key: str) -> str:
    """Rename a key using already-decoded literal path ``segments``."""
    _load_core()
    text = _as_text(source)
    _loads(text)
    decoded = list(segments)
    if any(not isinstance(segment, str) for segment in decoded):
        raise _backend_message_error("edit path segments must be strings")
    return _rename_key_segments(text, decoded, new_key)


def load(fp: IO[Any]) -> Any:
    """Parse a Ktav document read from a file-like object.

    Accepts both text-mode (``str``) and binary-mode (``bytes``) files.
    """
    return loads(fp.read())


def dump(obj: Any, fp: IO[Any]) -> None:
    """Serialize ``obj`` as a Ktav document and write it to ``fp``.

    Accepts both text-mode and binary-mode files. Binary mode writes
    UTF-8 bytes.
    """
    text = dumps(obj)
    try:
        fp.write(text)
    except TypeError:
        fp.write(text.encode("utf-8"))
