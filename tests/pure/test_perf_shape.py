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
  ``ktav._pure._keys.decode_key_segment`` (a real scan work unit):
  a wide N-pair document decodes exactly N, a dotted document exactly
  2N (two segments per line — per-line O(1) path work, not a rescan
  per insert), and the ``format`` path exactly 2N (a preflight + commit
  two-pass trivia insertion); and
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
from ktav._pure import _keys as pure_keys
from ktav._pure import _trivia
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
# Wrapping ``ktav._pure._keys.decode_key_segment`` counts exactly one
# real unit of scan work: the UTF-8/escape decode of ONE dotted-path
# key segment (``_insert_walk`` resolves ``decode_key_segment`` through
# the ``_keys`` module globals, so a module-attribute wrap sees every
# internal call site — including the two ``TriviaParser._hook_pair``
# walks). What the counts DO prove: on the ``loads`` path a wide
# N-pair document runs the segment decode exactly N times (PlainParser
# _hook_pair -> insert_value -> ONE _insert_walk pass; no rescan of
# the whole key set per insert), a dotted `a.bNNN` document exactly 2N
# (two segments per line, same single pass — constant path work per
# line, so reopen/merge is hash bookkeeping, not a rescan-per-insert).
# On the ``format`` path ``TriviaParser._hook_pair`` runs _insert_walk
# TWICE per pair — a dry_run=True preflight validation pass and a
# dry_run=False commit pass (an accepted, documented O(path)-twice
# design) — so each key is decoded 2x and the total is exactly 2N;
# ``t_insert_decoded`` reuses the preflight's decoded segments and
# decodes NOTHING. What these counts DO NOT prove: allocation or copy
# counts, constant factors, or total byte-scan cost — those need
# profiler tooling that is deliberately banned here; the wrapper adds
# no product-code changes and the original function is restored on
# exit of the context manager.
# ---------------------------------------------------------------------------


class _DecodeCounter:
    """Context manager that counts decode_key_segment calls on the
    ``ktav._pure._keys`` module (the insert walk resolves the name
    through the module globals, so a module-attribute wrap sees every
    internal call site)."""

    def __init__(self) -> None:
        self.count = 0
        self._original = pure_keys.decode_key_segment

    def __enter__(self) -> _DecodeCounter:
        original = self._original

        def counting(*args: Any, **kwargs: Any) -> Any:
            self.count += 1
            return original(*args, **kwargs)

        pure_keys.decode_key_segment = counting
        return self

    def __exit__(self, *exc: Any) -> None:
        pure_keys.decode_key_segment = self._original


def test_wide_object_decodes_exactly_one_key_segment_per_pair() -> None:
    # PlainParser._hook_pair -> insert_value -> ONE _insert_walk pass;
    # each single-segment key is decoded exactly once.
    for n in (1_000, 2_000):
        with _DecodeCounter() as counter:
            pure.loads(_wide_object(n))
        assert counter.count == n, "each single-segment key must decode exactly once"


def test_dotted_document_decodes_exactly_two_segments_per_line() -> None:
    # Same single _insert_walk pass; `a.bNNN` has two segments per line,
    # so 2 decodes per line.
    for n in (1_000, 2_000):
        with _DecodeCounter() as counter:
            value = pure.loads(_dotted_document(n))
        assert counter.count == 2 * n, (
            "two segments per line — constant per-line path work, no rescan-per-insert"
        )
        assert len(value["a"]) == n


def test_format_path_decodes_exactly_two_passes_per_pair() -> None:
    # TriviaParser._hook_pair runs _insert_walk TWICE per pair — a
    # dry_run=True preflight validation pass and a dry_run=False commit
    # pass (an accepted two-O(path)-passes design) — so each
    # single-segment key is decoded 2x. t_insert_decoded reuses the
    # preflight's decoded segments and decodes NOTHING; trivia insertion
    # itself is decode-free.
    n = 1_000
    with _DecodeCounter() as counter:
        out = pure.format(_wide_object(n))
    assert counter.count == 2 * n, (
        "the TriviaParser.format path must decode each key twice (preflight + commit)"
    )
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


# ---------------------------------------------------------------------------
# INDEX-LOOKUP counting over the trivia tree's SINGLE lookup site.
#
# `ktav._pure._trivia._index_lookup` is the one function every trivia
# key resolution goes through (grep check: it is called only from
# t_insert_decoded's leaf branch at _trivia.py:61 and descend branch at
# _trivia.py:69, and itself only reads node["index"]). Wrapping it
# counts REAL dict-index lookups — the exact operation a linear
# pairs-list walk would replace with O(n) position comparisons.
#
# HONEST LIMITS: the count bounds HOOK CALLS, not dict comparison
# work — a hypothetical dict implementation with pathological hashing
# would still pass, and a linear-scan regression that bypassed this
# hook entirely (scanning `pairs` positions without calling
# _index_lookup) would keep the count at n while time exploded. That
# is precisely why test_trivia_tree_index_is_consistent_and_lookup_ready
# above pins the index DATA STRUCTURE too. Comparison counts need a
# profiler, which is banned here.
#
# EXACT ARITHMETIC (hand-derived from _trivia.py t_insert_decoded):
# - wide `kNNNNNN: vNNNNNN`, n pairs: each line is single-segment, so
#   every insert takes only the LAST-segment branch — exactly ONE leaf
#   _index_lookup per pair. Total: n.
# - dotted `a.bNNNNNN: i`, n pairs: each line has segments ["a",
#   "bNNNNNN"]; the NON-last segment `a` takes the descend branch,
#   which calls _index_lookup BEFORE checking the miss — including the
#   FIRST line, whose miss then creates the synthetic `a` object via
#   the miss branch (lines 85-89). So the descend lookup happens on
#   every one of the n lines (the first does NOT skip it), plus ONE
#   leaf lookup for `bNNNNNN`. Total: n descend + n leaf = 2n.
# ---------------------------------------------------------------------------


class _IndexLookupCounter:
    """Context manager counting _index_lookup calls on the trivia module
    (t_insert_decoded resolves the name through its module globals, so a
    module-attribute wrap sees every call site)."""

    def __init__(self) -> None:
        self.count = 0
        self._original = _trivia._index_lookup

    def __enter__(self) -> _IndexLookupCounter:
        original = self._original

        def counting(node: Any, key: Any) -> Any:
            self.count += 1
            return original(node, key)

        _trivia._index_lookup = counting
        return self

    def __exit__(self, *exc: Any) -> None:
        _trivia._index_lookup = self._original


def test_wide_object_makes_exactly_one_index_lookup_per_pair() -> None:
    n = 1_000
    with _IndexLookupCounter() as counter:
        doc = pure_parser.parse_with_trivia(_wide_object(n))
    assert counter.count == n, (
        "one leaf index lookup per single-segment pair line — no extra lookups"
    )
    assert len(doc["root"]["index"]) == n


def test_dotted_document_makes_exactly_two_index_lookups_per_line() -> None:
    n = 1_000
    with _IndexLookupCounter() as counter:
        doc = pure_parser.parse_with_trivia(_dotted_document(n))
    # n descend lookups (every line resolves `a`, miss-including-first)
    # + n leaf lookups (one per `bNNNNNN`).
    assert counter.count == 2 * n, (
        "exactly one descend + one leaf lookup per dotted line; the first "
        "line's descend miss creates the synthetic object but still looks up"
    )
    assert len(doc["root"]["index"]) == 1, "the root holds exactly the synthetic `a` object"
    assert len(doc["root"]["pairs"][0][2]["index"]) == n


# ---------------------------------------------------------------------------
# ANTI-LINEAR-SCAN control: prove _index_lookup / t_insert_decoded
# resolve keys through the STORED INDEX (a dict .get — legitimate)
# WITHOUT iterating the pairs list. The pairs list below raises on ANY
# iteration, so a linear-scan regression (`next((i for i, e in
# enumerate(node["pairs"]) if e[0] == key), None)` inside _index_lookup,
# or a direct pairs walk in t_insert_decoded) raises AssertionError and
# fails this test, while pure indexed access stays legal.
#
# SCOPE NOTE: whole-render iteration over pairs in the FORMATTER is
# legitimate (it must walk every pair to emit them) — this test pins
# the INSERTION lookup boundary only.
#
# list.append does NOT iterate the list (CPython amortized append), so
# t_insert_decoded's miss branch appending a synthetic child to the
# root's banning pairs list stays legal; only __iter__ is banned.
# ---------------------------------------------------------------------------


class _PairsThatBanScanning(list):  # type: ignore[type-arg]
    """Pairs list whose iteration/scan raises — indexed access stays legal."""

    def __iter__(self) -> Any:
        # Any linear scan of the pairs list iterates -> boom.
        raise AssertionError("trivia insertion scanned the pairs list (linear lookup regression)")

    def __getitem__(self, index: Any) -> Any:
        # Indexed positions are legitimate (index[pos] entry reads).
        return super().__getitem__(index)


def test_insert_decoded_never_scans_the_pairs_list() -> None:
    """500 dotted inserts into a hand-built root whose pairs list raises
    on iteration: every lookup must go through the stored index. The
    call-count hook still holds exactly (n descend + n leaf = 2n), and
    the resulting index structure stays coherent."""
    n = 500
    root: dict[str, Any] = {"pairs": _PairsThatBanScanning(), "index": {}}
    with _IndexLookupCounter() as counter:
        # First insert: creates the synthetic `a` child (a legal miss-
        # branch list.append in the root — append does NOT iterate).
        _trivia.t_insert_decoded(root, ["a", "b0"], [], 0)
        # Guard the CHILD's pairs list too: product code created it as a
        # plain list, so a leaf-only linear-scan regression (indexed
        # descent through the root, then iterating the growing child
        # pairs) would otherwise pass silently. Wrap it with the same
        # banning list — list.__init__ iterating a PLAIN list is fine.
        child = root["pairs"][0][2]
        child["pairs"] = _PairsThatBanScanning(list(child["pairs"]))
        for i in range(1, n):
            _trivia.t_insert_decoded(root, ["a", f"b{i}"], [], i)
    assert counter.count == 2 * n, "500 descend lookups on `a` + 500 leaf lookups on `b{i}`"
    assert root["index"] == {"a": 0}, "the synthetic `a` child sits at root pairs position 0"
    assert len(child["index"]) == n, "all 500 b-keys indexed in the synthetic child"
    assert len(child["pairs"]) == n
    for key, pos in child["index"].items():
        assert child["pairs"][pos][0] == key, "index entries must point at matching pairs slots"
    # Counterfactual (FAILS this test): replacing _index_lookup's body
    # with a linear scan —
    #     return next(
    #         (i for i, e in enumerate(node["pairs"]) if e[0] == key), None
    #     )
    # — iterates the banning list and raises
    # "trivia insertion scanned the pairs list (linear lookup regression)"
    # on the very first insert. The same holds for any direct pairs walk
    # inside t_insert_decoded — including a LEAF-ONLY scan: after the
    # first insert the synthetic child's pairs list is ALSO a banning
    # wrapper, so a mutation that descends the root by index but scans
    # the leaf pairs fails on insert #1 of the remaining n-1 loop.
    #
    # CPython-semantics note: `append` is inherited from `list` and does
    # NOT iterate the list (amortized C-level append), so the miss
    # branch appending to the wrapped child list stays legal; only
    # `__iter__` is banned — see the class comment above.
