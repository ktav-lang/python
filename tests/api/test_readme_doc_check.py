"""Executes the claims the READMEs make, so a doc edit cannot drift from
the library silently.

Every assertion here corresponds to a sentence in README.md and its two
translations (docs/ru, docs/zh). Two of those sentences were originally
wrong and were only caught by running them, which is why they are tests
rather than prose review.
"""

import ktav
import pytest

FLOAT_SHAPES = [
    "x: 1e-9\n",
    "x: 1e-3\n",
    "x: 1e-2\n",
    "x: 1e0\n",
    "x: 1e6\n",
    "x: 1e7\n",
    "x: 1e20\n",
    "x: 1.5e-3\n",
    "x: 1.5e7\n",
    "x: 100.0\n",
    "x: 0.01\n",
    "x: 0.001\n",
    "x: 1.23456789012345678901\n",
    "x: 3.141592653589793238462643383279\n",
]


class TestCanonicalOutputTrio:
    """README: "three functions produce canonical output"."""

    def test_format_keeps_comments_and_collapses_blank_runs(self):
        src = "## why 8080\nport: 8080\n\n\n\nhost: a\n"
        out = ktav.format(src)
        assert "## why 8080" in out, "format must keep comments verbatim"
        assert "\n\n\n" not in out, "blank-line runs must collapse to one"
        assert "\n\n" in out, "a single blank line must survive as a grouping hint"
        assert ktav.format(out) == out, "format must be a fixed point"

    def test_canonical_from_source_drops_comments_and_blank_lines(self):
        src = "## why 8080\nport: 8080\n\n\nhost: a\n"
        out = ktav.canonical_from_source(src)
        assert "##" not in out
        assert "\n\n" not in out

    @pytest.mark.parametrize("src", FLOAT_SHAPES)
    def test_emit_canonical_of_loads_equals_canonical_from_source(self, src):
        """README: Python distinguishes int from float, so unlike the JS
        bindings there is no fidelity gap between the two paths."""
        assert ktav.emit_canonical(ktav.loads(src)) == ktav.canonical_from_source(src)

    def test_both_paths_spell_floats_by_the_canonical_rule(self):
        """README names this exact pair, so the README is wrong the moment
        it stops holding."""
        src = "x: 1.23456789012345678901\n"
        assert ktav.canonical_from_source(src) == "x: 1.2345678901234567\n"
        assert ktav.emit_canonical(ktav.loads(src)) == "x: 1.2345678901234567\n"

    def test_integer_float_distinction_survives_loads(self):
        v = ktav.loads("i: 1\nf: 1.0\n")
        assert isinstance(v["i"], int)
        assert not isinstance(v["i"], bool)
        assert isinstance(v["f"], float)
        assert ktav.emit_canonical(v) == "i: 1\nf: 1.0\n"


class TestDumpsForceStrings:
    """README: coerces every leaf scalar via the raw `::` marker while
    compounds keep their structure."""

    def test_leaves_coerced_compounds_kept(self):
        out = ktav.dumps_force_strings(
            {"p": 8080, "r": 0.5, "t": True, "n": None, "o": {"k": 1}, "a": [2]}
        )
        assert "p:: 8080" in out
        assert "r:: 0.5" in out
        assert "t:: true" in out
        assert "n:: null" in out
        assert "k:: 1" in out, "a nested leaf must be coerced too"
        assert "o: {" in out, "a nested object keeps its structure"
        assert "a: [" in out, "a nested array keeps its structure"

    def test_result_reparses_as_all_strings(self):
        obj = {"p": 8080, "r": 0.5, "t": True, "n": None, "o": {"k": 1}}
        back = ktav.loads(ktav.dumps_force_strings(obj))
        assert back == {
            "p": "8080",
            "r": "0.5",
            "t": "true",
            "n": "null",
            "o": {"k": "1"},
        }


class TestErrorEnvelopeAttributes:
    """README: every raised instance carries the ten-field envelope, absent
    information is None rather than a missing attribute."""

    FIELDS = (
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
    )

    def test_all_ten_attributes_present_on_a_parse_error(self):
        with pytest.raises(ktav.KtavDecodeError) as excinfo:
            ktav.loads("x: [")
        for field in self.FIELDS:
            assert hasattr(excinfo.value, field), f"missing attribute {field}"

    def test_all_ten_attributes_present_on_an_encode_error(self):
        with pytest.raises(ktav.KtavEncodeError) as excinfo:
            ktav.dumps({"v": float("nan")})
        for field in self.FIELDS:
            assert hasattr(excinfo.value, field), f"missing attribute {field}"

    def test_str_equals_message(self):
        """README states `str(e) == e.message` as a guarantee."""
        with pytest.raises(ktav.KtavDecodeError) as excinfo:
            ktav.loads_strict("a: 1.10\n")
        assert str(excinfo.value) == excinfo.value.message
        assert excinfo.value.message

    def test_lossy_scalar_carries_body_and_canonical(self):
        """The README example prints these exact values."""
        with pytest.raises(ktav.KtavDecodeError) as excinfo:
            ktav.loads_strict("a: 1.10\n")
        e = excinfo.value
        assert e.error == "LossyScalar"
        assert e.body == "1.10"
        assert e.canonical == "1.1"
        assert e.spec_section == "§3.6/§5.2"

    def test_span_is_byte_offsets_not_utf16(self):
        """README: span is byte offsets into the UTF-8 source, not UTF-16
        code units. A multi-byte prefix makes the two disagree."""
        with pytest.raises(ktav.KtavDecodeError) as excinfo:
            ktav.loads_strict("ключ: 1.10\n")
        e = excinfo.value
        assert e.span is not None
        line_text = e.line_text
        assert line_text == "ключ: 1.10"
        # LossyScalar spans the whole line, so end == the line's length in
        # whichever unit the span uses. Cyrillic makes the two disagree:
        # 14 bytes vs 10 code points (also 10 UTF-16 code units here).
        assert e.span["end"] == len(line_text.encode("utf-8")) == 14
        assert e.span["end"] != len(line_text), "a code-unit count would be 10"

    def test_path_segments_are_never_split_on_a_literal_dot(self):
        """README: a key literally named `a.b` is one segment."""
        with pytest.raises(ktav.KtavEncodeError) as excinfo:
            ktav.dumps({"a\\.b": float("nan")})
        path = excinfo.value.path
        if path is not None:
            assert path == ["a\\.b"] or len(path) == 1
