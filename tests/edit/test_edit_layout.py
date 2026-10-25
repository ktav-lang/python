"""Layout regressions: exact output shape and minimal inline unfolding.

Port of the Rust reference suite
``tests/suite/api/text/edit_value/layout.rs`` — all 22 layout
regressions, not just the happy path. Every case runs on the pure
backend and, when the extension exposes the 0.9 symbols, on the native
backend with the same literal-output oracle.
"""

from __future__ import annotations

from typing import Any

import ktav.pure as pure
import pytest

from tests.edit._backends import edit_apis

APIS = edit_apis()


def check(api: Any, source: str, path: list[str], replacement: Any, expected: str) -> None:
    """Literal-output oracle for both API forms of the same edit."""
    textual = ".".join(segment.replace("\\", "\\\\").replace(".", "\\.") for segment in path)
    assert api.edit_value(source, textual, replacement) == expected, textual
    assert api.edit_value_segments(source, path, replacement) == expected


@pytest.mark.parametrize("api", APIS)
def test_deep_leaf_preserves_each_source_form(api: Any) -> None:
    for source in (
        "targets.storagehost.address: old\ntargets.storagehost.user: mcp-agent\n",
        "targets: {storagehost: {address: old, user: mcp-agent}}\n",
        "targets: {\n  storagehost: {\n    address: old\n    user: mcp-agent\n  }\n}\n",
    ):
        check(
            api,
            source,
            ["targets", "storagehost", "address"],
            "192.168.0.88:22",
            source.replace("old", "192.168.0.88:22"),
        )


@pytest.mark.parametrize("api", APIS)
def test_deep_array_leaf_preserves_mixed_forms(api: Any) -> None:
    for source in (
        "targets: [{storagehost: [old, keep]}, other]\n",
        "targets: [\n  {storagehost: [old, keep]}\n  other\n]\n",
        "targets: [\n  {\n    storagehost: [\n      old\n      keep\n    ]\n  }\n  other\n]\n",
    ):
        check(
            api,
            source,
            ["targets", "0", "storagehost", "0"],
            "new",
            source.replace("old", "new"),
        )


@pytest.mark.parametrize("api", APIS)
def test_whole_inline_containers_remain_inline(api: Any) -> None:
    for source, value, expected in (
        ("a: {x: 1}\n", {"y": 2}, "a: {y: 2}\n"),
        ("a: [1, 2]\n", [3, 4], "a: [3, 4]\n"),
        ("a: {}\n", {"y": 2}, "a: {y: 2}\n"),
        ("a: []\n", [3, 4], "a: [3, 4]\n"),
        ("a: {}\n", [3, 4], "a: [3, 4]\n"),
    ):
        check(api, source, ["a"], value, expected)


@pytest.mark.parametrize("api", APIS)
def test_emptying_block_containers_does_not_collapse_them(api: Any) -> None:
    check(api, "a: {\n  x: 1\n}\n", ["a"], {}, "a: {\n}\n")
    check(api, "a: [\n  1\n]\n", ["a"], [], "a: [\n]\n")


@pytest.mark.parametrize("api", APIS)
def test_newline_unfolds_only_inline_ancestor_chain(api: Any) -> None:
    check(
        api,
        "## top\na: [{x: old, untouched: [1, 2]}, {keep: yes}]\nz: keep\n",
        ["a", "0", "x"],
        "one\ntwo",
        "## top\na: [\n    {\n        x: ((\none\ntwo\n        ))\n"
        "        untouched: [1, 2]\n    }\n    {keep: yes}\n]\nz: keep\n",
    )


@pytest.mark.parametrize("api", APIS)
def test_newline_under_dotted_key_does_not_expand_dotted_ancestors(api: Any) -> None:
    check(
        api,
        "a.b: [old, keep]\na.c: other\n",
        ["a", "b", "0"],
        "one\ntwo",
        "a.b: [\n    ((\none\ntwo\n    ))\n    keep\n]\na.c: other\n",
    )


@pytest.mark.parametrize("api", APIS)
def test_dense_escapes_unfold_but_sparse_escapes_do_not(api: Any) -> None:
    check(api, "a: [old, keep]\n", ["a", "0"], "a,b,c,d,e", "a: [\n    a,b,c,d,e\n    keep\n]\n")
    check(api, "a: [old]\n", ["a", "0"], "a,b,c,d", "a: [a\\,b\\,c\\,d]\n")
    sparse = "x" * 30 + "a,b,c,d,e"
    escaped = sparse.replace(",", "\\,")
    check(api, "a: [old]\n", ["a", "0"], sparse, f"a: [{escaped}]\n")


@pytest.mark.parametrize("api", APIS)
def test_width_boundary_is_in_characters_not_bytes(api: Any) -> None:
    for size, expanded in ((95, False), (96, True)):
        value = "я" * size
        expected = f"a: [\n    {value}\n]\n" if expanded else f"a: [{value}]\n"
        check(api, "a: [old]\n", ["a", "0"], value, expected)


@pytest.mark.parametrize("api", APIS)
def test_already_long_line_only_unfolds_when_it_grows(api: Any) -> None:
    source = f"a: [{'x' * 120}, keep]\n"
    check(api, source, ["a", "0"], "y" * 120, source.replace("x", "y"))
    check(api, source, ["a", "0"], "y" * 121, f"a: [\n    {'y' * 121}\n    keep\n]\n")


@pytest.mark.parametrize("api", APIS)
def test_width_expansion_stops_when_inner_line_fits(api: Any) -> None:
    value = "x" * 91
    check(api, "a: [{x: old}]\n", ["a", "0", "x"], value, f"a: [\n    {{x: {value}}}\n]\n")


@pytest.mark.parametrize("api", APIS)
def test_escape_overhead_boundary_is_exact(api: Any) -> None:
    dense = "x" * 7 + "a,b,c,d,e"
    sparse = "x" * 8 + "a,b,c,d,e"
    check(api, "a: [old]\n", ["a", "0"], dense, f"a: [\n    {dense}\n]\n")
    escaped = sparse.replace(",", "\\,")
    check(api, "a: [old]\n", ["a", "0"], sparse, f"a: [{escaped}]\n")


@pytest.mark.parametrize("api", APIS)
def test_long_changed_leaf_does_not_unfold_unrelated_nested_branches(api: Any) -> None:
    value = "x" * 100
    check(
        api,
        "a: [old, {untouched: [1, 2]}]\n",
        ["a", "0"],
        value,
        f"a: [\n    {value}\n    {{untouched: [1, 2]}}\n]\n",
    )


@pytest.mark.parametrize("api", APIS)
def test_promoted_siblings_keep_values_when_inline_escapes_lose_meaning(api: Any) -> None:
    check(
        api,
        "a: [old, a\\,b, \\u00342, :: literal]\n",
        ["a", "0"],
        "x\ny",
        "a: [\n    ((\nx\ny\n    ))\n    a,b\n    :: 42\n    :: :: literal\n]\n",
    )


@pytest.mark.parametrize("api", APIS)
def test_promoted_pairs_keep_key_spelling_and_raw_markers(api: Any) -> None:
    check(
        api,
        'a: {"x.y": old, nested.key::  42, n: 0007}\n',
        ["a", "x.y"],
        "x\ny",
        'a: {\n    "x.y": ((\nx\ny\n    ))\n    nested.key::  42\n    n: 0007\n}\n',
    )


@pytest.mark.parametrize("api", APIS)
def test_root_inline_promotion_preserves_bom_and_eof(api: Any) -> None:
    check(api, "﻿[old, keep]", ["0"], "x\ny", "﻿[\n    ((\nx\ny\n    ))\n    keep\n]")


@pytest.mark.parametrize("api", APIS)
def test_promotion_preserves_eol_comments_and_no_final_terminator(api: Any) -> None:
    for eol in ("\n", "\r", "\r\n"):
        source = f"## header{eol}a: [old, keep]"
        expected = f"## header{eol}a: [{eol}    (({eol}x{eol}y{eol}    )){eol}    keep{eol}]"
        check(api, source, ["a", "0"], "x\ny", expected)


@pytest.mark.parametrize("api", APIS)
def test_comments_outside_promoted_inline_value_remain_byte_exact(api: Any) -> None:
    check(
        api,
        "list: [\n  ## before\n  {x: old}\n  ## after\n]\n",
        ["list", "0", "x"],
        "x\ny",
        "list: [\n  ## before\n  {\n      x: ((\nx\ny\n      ))\n  }\n  ## after\n]\n",
    )


@pytest.mark.parametrize("api", APIS)
def test_noop_ignores_all_readability_thresholds(api: Any) -> None:
    source = f"a: [{'x' * 140}, a\\,b\\,c\\,d\\,e]\n"
    check(api, source, ["a", "0"], "x" * 140, source)
    check(api, source, ["a", "1"], "a,b,c,d,e", source)


@pytest.mark.parametrize("api", APIS)
def test_type_change_does_not_force_unrelated_layout_changes(api: Any) -> None:
    check(api, "a: {x: [1], keep: [2]}\n", ["a", "x"], True, "a: {x: true, keep: [2]}\n")
    check(api, "a: [1]\n", ["a"], "42", "a:: 42\n")


@pytest.mark.parametrize("api", APIS)
def test_reopened_inline_parent_promotes_only_its_physical_definition(api: Any) -> None:
    check(
        api,
        "a: {x: old}\n## gap\na.y: keep\n",
        ["a", "x"],
        "x\ny",
        "a: {\n    x: ((\nx\ny\n    ))\n}\n## gap\na.y: keep\n",
    )


@pytest.mark.parametrize("api", APIS)
def test_impossible_block_encoding_keeps_valid_inline_form(api: Any) -> None:
    for value in ("a\rb", "a\n))\nb"):
        encoded = value.replace("\r", "\\r").replace("\n", "\\n")
        check(api, "a: [old]\n", ["a", "0"], value, f"a: [{encoded}]\n")
    check(api, "a: [old, a\\rb]\n", ["a", "0"], "x\ny", "a: [x\\ny, a\\rb]\n")


@pytest.mark.parametrize("api", APIS)
def test_unsafe_comment_loss_still_fails_closed(api: Any) -> None:
    for source in ("a: {\n ## keep\n x: 1\n}\n", "a: [\n ## keep\n 1\n]\n"):
        with pytest.raises(api.KtavUnsupportedError):
            api.edit_value_segments(source, ["a"], None)


@pytest.mark.parametrize("api", APIS)
def test_results_reparse_to_the_expected_tree(api: Any) -> None:
    """Beyond literals: every expansion result parses to the edited tree."""
    source = "a: [old, keep]\n"
    out = api.edit_value_segments(source, ["a", "0"], "one\ntwo")
    assert pure.loads(out) == {"a": ["one\ntwo", "keep"]}
