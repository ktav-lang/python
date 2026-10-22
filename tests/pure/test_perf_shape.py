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
  line plus the single root open), i.e. a constant-per-line cost;
- one key-segment DECODE per dotted-path segment, counted by wrapping
  ``ktav._pure.parser.decode_key_segment`` (a real scan work unit):
  a wide N-pair document decodes exactly N, a dotted document exactly
  2N (two segments per line — per-line O(1) path work, not a rescan
  per insert), and the ``format`` path exactly N; and
- emitted output that is exact in the input (hand-computed output
  LENGTH and exact output TEXT — each key appears exactly once).

They CANNOT prove constant factors, allocation counts, copy counts, or
CPython bytecode-level speed — those need a real profiler and are
deliberately out of scope here (see the plan's complexity notes for
the algorithmic argument: single byte-cursor pass, dict-based scopes,
list+join writer). Output-length bounds say nothing about HOW the
writer copies internally; they only pin the produced bytes.
"""

from __future__ import annotations

from typing import Any

from ktav import pure
from ktav._pure import parser as pure_parser
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
    """n pairs, zero-padded KEYS and VALUES so every line — and therefore
    every canonical output line — is the same length."""
    return "".join(f"k{i:06d}: v{i:06d}\n" for i in range(n))


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


def test_doubled_long_string_output_length_is_exact_in_input_length() -> None:
    out1 = pure.emit_canonical(pure.loads(_long_string(10_000)))
    out2 = pure.emit_canonical(pure.loads(_long_string(20_000)))
    # Both documents share the constant `s: ` prefix and `\n` suffix; the
    # only difference is the payload, so the exact (hand-computed)
    # relation is len(out2) == 2*(len(out1) - len("s: \n")) + len("s: \n").
    # This pins the OUTPUT BYTES only — output-length bounds cannot prove
    # anything about the writer's internal copying strategy; they just
    # fix the produced text exactly.
    prefix_len = len("s: \n")
    assert len(out2) == 2 * (len(out1) - prefix_len) + prefix_len


def test_wide_object_writer_writes_each_key_exactly_once() -> None:
    for n in (1_000, 2_000):
        out = pure.emit_canonical(pure.loads(_wide_object(n)))
        assert out.count(": ") == n
        assert out.count("k000000") == 1, "no key may be emitted twice"
    out1 = pure.emit_canonical(pure.loads(_wide_object(1_000)))
    out2 = pure.emit_canonical(pure.loads(_wide_object(2_000)))
    # Zero-padded KEYS and VALUES make every output line identical in
    # length, so the total output length doubles EXACTLY with the input.
    assert len(out2) == 2 * len(out1), "zero-padded keys and values make the doubling exact"


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


# ---------------------------------------------------------------------------
# DECODE-COUNT work counters over REAL scan work.
#
# Wrapping ``ktav._pure.parser.decode_key_segment`` counts exactly one
# real unit of scan work: the UTF-8/escape decode of ONE dotted-path
# key segment. What the counts DO prove: a wide N-pair document runs
# the segment decode exactly N times (one per key — no rescan of the
# whole key set per insert), a dotted `a.bNNN` document exactly 2N (two
# segments per line — constant path work per line, so reopen/merge is
# hash bookkeeping, not a rescan-per-insert), and the ``format`` path
# exactly N (one decode per pair line while rebuilding the trivia
# tree). What they DO NOT prove: allocation or copy counts, constant
# factors, or total byte-scan cost — those need profiler tooling that
# is deliberately banned here; the wrapper adds no product-code
# changes and the original function is restored on exit of the
# context manager.
# ---------------------------------------------------------------------------


class _DecodeCounter:
    """Context manager that counts decode_key_segment calls on the parser
    module (the parser resolves the name through its module globals, so
    a module-attribute wrap sees every internal call site)."""

    def __init__(self) -> None:
        self.count = 0
        self._original = pure_parser.decode_key_segment

    def __enter__(self) -> _DecodeCounter:
        original = self._original

        def counting(*args: Any, **kwargs: Any) -> Any:
            self.count += 1
            return original(*args, **kwargs)

        pure_parser.decode_key_segment = counting
        return self

    def __exit__(self, *exc: Any) -> None:
        pure_parser.decode_key_segment = self._original


def test_wide_object_decodes_exactly_one_key_segment_per_pair() -> None:
    for n in (1_000, 2_000):
        with _DecodeCounter() as counter:
            pure.loads(_wide_object(n))
        assert counter.count == n, "each single-segment key must decode exactly once"


def test_dotted_document_decodes_exactly_two_segments_per_line() -> None:
    for n in (1_000, 2_000):
        with _DecodeCounter() as counter:
            value = pure.loads(_dotted_document(n))
        assert counter.count == 2 * n, (
            "two segments per line — constant per-line path work, no rescan-per-insert"
        )
        assert len(value["a"]) == n


def test_format_path_decodes_exactly_one_segment_per_pair() -> None:
    # Product repair: _hook_pair decodes each key ONCE via insert_value's
    # `decoded` list and t_insert_decoded reuses it — so the whole format
    # path costs exactly N decodes for N pairs (t_insert, the decoding
    # wrapper, is no longer on this path at all).
    n = 1_000
    with _DecodeCounter() as counter:
        out = pure.format(_wide_object(n))
    assert counter.count == n, "the TriviaParser.format path must decode each key once"
    assert out.count(": ") == n


def test_trivia_tree_index_is_consistent_and_lookup_ready() -> None:
    """Structural pin on the data structure behind O(1) pair lookups.

    t_insert_decoded resolves each key through node["index"] (a dict,
    decoded key -> position in node["pairs"]) rather than scanning the
    pairs list — the decode count alone cannot distinguish that from a
    linear pairs-list scan (the old quadratic t_insert decoded the same
    N times). This test pins the index map itself: for a 1_000-pair
    document it must exist, hold exactly one entry per pair, and agree
    with `pairs` (each entry points at the pairs slot carrying the same
    decoded key).

    HONEST LIMITS: this proves the O(1)-lookup data structure is built
    and consistent; it does NOT count index.get() comparisons (not
    injectable without product-code hooks, and profiling is banned
    here), so a hypothetical dict implementation with pathological
    hashing would still pass. Comparison counts need a profiler.
    """
    n = 1_000
    doc = pure_parser.parse_with_trivia(_wide_object(n))
    root = doc["root"]
    assert root["k"] == "obj"
    index = root["index"]
    pairs = root["pairs"]
    assert len(index) == n, "one index entry per pair — no dropped or duplicated keys"
    assert len(pairs) == n
    for key, pos in index.items():
        entry = pairs[pos]
        assert entry[0] == key, "index entries must point at the pairs slot with the same key"
    # Every pairs slot is accounted for by exactly one index entry.
    assert sorted(index.values()) == list(range(n))
