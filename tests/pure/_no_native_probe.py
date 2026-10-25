"""Runs in a FRESH interpreter with ``ktav._core`` hard-blocked via
``sys.meta_path`` — the no-native scenario the pure backend must own.

Blocking (rather than relying on the environment) makes this probe
meaningful in BOTH CI jobs: where the compiled extension is installed
(the regular ``test`` job) the block hides it; where it is absent (the
pure-mode job) the block is a belt-and-braces guard against any
accidental import path.

Exits 0 printing exactly ``ok`` on success; any assertion aborts with a
non-zero exit status that fails the calling pytest test.
"""

import sys


class _BlockCore:
    """A meta_path finder whose only job is to make `import ktav._core`
    raise ImportError, wherever it would otherwise come from."""

    def find_spec(self, fullname, path=None, target=None):  # type: ignore[no-untyped-def]
        if fullname == "ktav._core":
            raise ImportError("ktav._core blocked by tests/pure/_no_native_probe.py")
        return None

    def find_module(self, fullname, path=None):  # type: ignore[no-untyped-def]
        return None


sys.meta_path.insert(0, _BlockCore())

# 1. The top-level import must not fail or warn when _core is absent.
import ktav  # noqa: E402

assert not hasattr(ktav, "_core"), "ktav._core leaked past the meta_path block"
assert ktav._HAS_CORE is False

# 2. Every native-backed top-level function must raise the documented
#    clean ImportError pointing at ktav.pure — no AttributeError, no
#    silent fallback to the pure backend.
for name in (
    "loads",
    "loads_strict",
    "dumps",
    "emit_canonical",
    "dumps_force_strings",
    "format",
    "canonical_from_source",
    "edit_value",
    "edit_value_segments",
):
    func = getattr(ktav, name)
    parses_text = name in ("loads", "loads_strict", "format", "canonical_from_source")
    try:
        if name == "edit_value":
            func("a: 1\n", "a", 2)
        elif name == "edit_value_segments":
            func("a: 1\n", ["a"], 2)
        else:
            func("x: 1\n" if parses_text else {})
    except ImportError as exc:
        # Public contract (python/ktav/__init__.py _no_native stub): the
        # message must contain BOTH the import fix and the backend name.
        if "from ktav import pure" not in str(exc) or "ktav.pure" not in str(exc):
            raise SystemExit(
                f"{name}: ImportError must mention 'from ktav import pure' and ktav.pure: {exc}"
            ) from exc
    except Exception as exc:
        raise SystemExit(f"{name}: expected ImportError, got {type(exc).__name__}: {exc}") from exc
    else:
        raise SystemExit(f"{name}: expected ImportError, call succeeded")

# 3. The pure backend must be fully functional in the same process.
import ktav.pure  # noqa: E402

assert ktav.pure.loads("a: 1\n") == {"a": 1}
assert ktav.pure.loads("a.b: 1\na.c: 2\n") == {"a": {"b": 1, "c": 2}}
assert ktav.pure.loads_strict("a: 1.0\n") == {"a": 1.0}
assert ktav.pure.dumps({"a": [1, "x", True, None]}) == ktav.pure.emit_canonical(
    ktav.pure.loads(ktav.pure.dumps({"a": [1, "x", True, None]}))
)
formatted = ktav.pure.format("## c\na: 1\n\n\n\n")
assert "## c" in formatted, "format must keep comments verbatim"
assert ktav.pure.format(formatted) == formatted, "format must be a fixed point"
assert (
    ktav.pure.canonical_from_source("a: {b: {c: 1}}") == "a: {\n    b: {\n        c: 1\n    }\n}\n"
)
assert ktav.pure.edit_value("a: 1\n", "a", 2) == "a: 2\n"
assert ktav.pure.edit_value_segments("a: [x]\n", ["a", "0"], "y") == "a: [y]\n"
with __import__("io").StringIO("a: 1\n") as handle:
    assert ktav.pure.load(handle) == {"a": 1}

print("ok")
