"""Deterministic algorithmic regression checks for the pure backend.

NOT wall-clock benchmarks (wall-clock is banned from gating): these are
operation-COUNT and structural-invariant assertions over the pure
parser's hook points (``ktav._pure.parser.PlainParser`` is explicitly
subclassable — ``TriviaParser`` is the in-tree precedent) and over the
writer's output shape. They can prove:

- one insertion hook per pair/item line (no repeated full-subtree work
  or linear rescans per pair) — for the WIDE-object case the total hook
  count scales EXACTLY linearly when the input doubles; for the DOTTED
  case the per-document hook count is exactly `n + 1` (one hook per
  line plus the single root open), i.e. a constant-per-line cost; and
- emitted output that is exact in the input (each key written exactly
  once; a doubled document costs exactly one extra payload copy).

They CANNOT prove constant factors, allocation counts, or CPython
bytecode-level speed — those need a real profiler and are deliberately
out of scope here (see the plan's complexity notes for the algorithmic
argument: single byte-cursor pass, dict-based scopes, list+join writer).
"""

from __future__ import annotations

from typing import Any

from ktav import pure
from ktav._pure.parser import PlainParser


class CountingParser(PlainParser):
    """Counts the parser's value-attachment hooks — one per pair line,
    one per array-item line — plus compound opens."""

    def __init__(self, strict: bool = False) -> None:
        super().__init__(strict)
        self.pairs = 0
        self.items = 0
        self.opens = 0

    def _hook_pair(self, frame, key, value, line, line_text, span):  # type: ignore[no-untyped-def]
        self.pairs += 1
        super()._hook_pair(frame, key, value, line, line_text, span)

    def _hook_item(self, frame, value, line):  # type: ignore[no-untyped-def]
        self.items += 1
        super()._hook_item(frame, value, line)

    def _hook_open(self, frame):  # type: ignore[no-untyped-def]
        self.opens += 1
        super()._hook_open(frame)


def _wide_object(n: int) -> str:
    """n pairs, zero-padded keys so every line is the same length."""
    return "".join(f"k{i:06d}: {i}\n" for i in range(n))


def _dotted_document(n: int) -> str:
    return "".join(f"a.b{i:06d}: {i}\n" for i in range(n))


def _long_string(n: int) -> str:
    # plain text scalar, no escapes or structural characters
    return "s: " + "x" * n + "\n"


def _deep_inline(depth: int) -> str:
    return "[" * depth + "1" + "]" * depth


def test_wide_object_exactly_one_pair_hook_per_line() -> None:
    for n in (1_000, 2_000):
        parser = CountingParser()
        parser.parse(_wide_object(n))
        assert parser.pairs == n, "each pair line must cost exactly one insertion hook"
        assert parser.opens == 1, "one root scope, no synthetic re-opens"


def test_doubled_wide_object_pins_the_constant_per_line_cost() -> None:
    # Counts are pairs + opens: (1000 + 1, 2000 + 1). The exact doubling
    # relation does NOT hold across the +1 root-open constant, so pin the
    # honest invariant instead: an exact per-line constant cost. This is
    # a constant-per-line regression pin, NOT an asymptotic proof (no
    # wall-clock, no allocation counts are taken here).
    counts = []
    for n in (1_000, 2_000):
        parser = CountingParser()
        parser.parse(_wide_object(n))
        counts.append(parser.pairs + parser.opens)
    assert counts[0] == 1_001, "work must be exactly one hook per line plus one root open"
    assert counts[1] - counts[0] == 1_000, "each extra input line must cost exactly one hook"


def test_dotted_paths_one_hook_per_line_reopen_merge_is_hash_bookkeeping() -> None:
    for n in (1_000, 2_000):
        parser = CountingParser()
        parser.parse(_dotted_document(n))
        assert parser.pairs == n
        # The synthetic object for the `a.` prefix is created directly by
        # insert_value, which does NOT call _hook_open — only the root
        # frame does. Reopen/merge must therefore not re-open (or rescan)
        # anything per line: exactly ONE open for the whole document.
        assert parser.opens == 1
        value = pure.loads(_dotted_document(n))
        assert len(value["a"]) == n, "no line may be dropped or double-inserted"


def test_long_string_output_is_input_plus_constant() -> None:
    for n in (10_000, 20_000):
        out = pure.emit_canonical(pure.loads(_long_string(n)))
        # canonical spelling: `s: <n x's>\n` — exactly n payload chars
        assert len(out) == len("s: ") + n + 1


def test_doubled_long_string_costs_exactly_one_extra_payload_copy() -> None:
    out1 = pure.emit_canonical(pure.loads(_long_string(10_000)))
    out2 = pure.emit_canonical(pure.loads(_long_string(20_000)))
    # Both documents share the constant `s: ` prefix and `\n` suffix; the
    # only difference is the payload, so the exact (hand-computed)
    # relation is len(out2) == 2*(len(out1) - len("s: \n")) + len("s: \n").
    # A writer that re-copied growing tails could not keep this exact.
    prefix_len = len("s: \n")
    assert len(out2) == 2 * (len(out1) - prefix_len) + prefix_len


def test_wide_object_writer_writes_each_key_exactly_once() -> None:
    for n in (1_000, 2_000):
        out = pure.emit_canonical(pure.loads(_wide_object(n)))
        assert out.count(": ") == n
        assert out.count("k000000") == 1, "no key may be emitted twice"
    out1 = pure.emit_canonical(pure.loads(_wide_object(1_000)))
    out2 = pure.emit_canonical(pure.loads(_wide_object(2_000)))
    assert len(out2) == 2 * len(out1), "zero-padded keys make the doubling exact"


def test_deep_but_in_limit_document_parses_and_writes() -> None:
    depth = 100  # below the declared inline limit of 128
    value = pure.loads(_deep_inline(depth))
    nested: Any = value
    for _ in range(depth - 1):
        assert isinstance(nested, list)
        assert len(nested) == 1
        nested = nested[0]
    assert nested == [1]
    out = pure.dumps(value)
    assert pure.loads(out) == value, "deep structures must survive a write/read round trip"
