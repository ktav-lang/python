"""Every raised exception carries the ten-field structured envelope."""

import json

import ktav
import pytest

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


def test_all_ten_fields_present_on_decode_error() -> None:
    with pytest.raises(ktav.KtavDecodeError) as exc_info:
        ktav.loads("a: 1\na: 2")
    e = exc_info.value
    for field in FIELDS:
        assert hasattr(e, field)
    assert e.error == "DuplicateKey"
    assert e.line == 2
    assert e.path == ["a"]
    assert e.reason is None
    assert e.line_text == "a: 2"
    assert isinstance(e.span, dict)
    assert {"start", "end"} <= set(e.span)
    assert e.span["end"] >= e.span["start"]
    assert e.spec_section == "§6.2"
    assert e.body is None
    assert e.canonical is None


def test_lossy_scalar_surfaces_body_canonical_spec_section() -> None:
    with pytest.raises(ktav.KtavDecodeError) as exc_info:
        ktav.loads_strict("version: 1.10")
    e = exc_info.value
    for field in FIELDS:
        assert hasattr(e, field)
    assert e.error == "LossyScalar"
    assert e.body == "1.10"
    assert e.canonical == "1.1"
    assert e.spec_section == "§3.6/§5.2"
    assert e.line == 1
    assert e.line_text == "version: 1.10"


def test_writer_refusal_carries_reason_and_honest_nulls() -> None:
    with pytest.raises(ktav.KtavEncodeError) as exc_info:
        ktav.dumps({"v": float("nan")})
    e = exc_info.value
    for field in FIELDS:
        assert hasattr(e, field)
    assert e.error == "Unrepresentable"
    assert e.reason == "NonFiniteFloat"
    assert e.spec_section == "§5.9.0"
    assert e.line is None
    assert e.line_text is None
    assert e.span is None
    assert e.path is None
    assert e.body is None
    assert e.canonical is None


def test_scalar_root_refusal() -> None:
    with pytest.raises(ktav.KtavEncodeError) as exc_info:
        ktav.dumps("just a string")
    e = exc_info.value
    for field in FIELDS:
        assert hasattr(e, field)
    assert e.error == "Unrepresentable"
    assert e.reason == "ScalarRoot"


def test_unrepresentable_at_carries_exact_path() -> None:
    # CR bytes in string values are not pre-checked by the binding, so
    # this rejection comes from the crate's path-tracking pass and
    # carries the decoded key path (spec § 5.9.7).
    with pytest.raises(ktav.KtavEncodeError) as exc_info:
        ktav.dumps({"metrics": {"log": "line1\rline2"}})
    e = exc_info.value
    for field in FIELDS:
        assert hasattr(e, field)
    assert e.error == "UnrepresentableAt"
    assert e.reason == "CRByte"
    assert e.path == ["metrics", "log"]
    assert e.spec_section == "§5.9.7"


def test_nested_nan_is_pathless_because_the_binding_guard_fires_first() -> None:
    # py_to_value rejects NaN / ±Infinity before the Value reaches the
    # crate's path-tracking representability pass, so this stays
    # `Unrepresentable` with an honest null path.
    with pytest.raises(ktav.KtavEncodeError) as exc_info:
        ktav.dumps({"metrics": {"cpu": float("nan")}})
    assert exc_info.value.error == "Unrepresentable"
    assert exc_info.value.reason == "NonFiniteFloat"
    assert exc_info.value.path is None


def test_dotted_key_is_one_segment() -> None:
    with pytest.raises(ktav.KtavEncodeError) as exc_info:
        ktav.dumps({"a.b": "x\ry"})
    e = exc_info.value
    assert e.error == "UnrepresentableAt"
    assert e.path == ["a.b"]  # one segment — never split on the dot


def test_message_class_errors_come_out_as_envelope() -> None:
    with pytest.raises(ktav.KtavEncodeError) as exc_info:
        ktav.dumps({1: "x"})
    e = exc_info.value
    for field in FIELDS:
        assert hasattr(e, field)
    assert e.error == "Message"
    assert e.reason is None
    assert e.line is None


def test_str_is_human_readable_never_json() -> None:
    with pytest.raises(ktav.KtavError) as decode_info:
        ktav.loads("x: [")
    decode_str = str(decode_info.value)
    assert decode_str
    assert not decode_str.startswith("{")
    with pytest.raises(json.JSONDecodeError):
        json.loads(decode_str)

    with pytest.raises(ktav.KtavError) as encode_info:
        ktav.dumps({"v": float("nan")})
    encode_str = str(encode_info.value)
    assert encode_str
    assert not encode_str.startswith("{")
    with pytest.raises(json.JSONDecodeError):
        json.loads(encode_str)


def test_format_errors_carry_envelope_too() -> None:
    with pytest.raises(ktav.KtavDecodeError) as unclosed:
        ktav.format("x: [")
    e = unclosed.value
    for field in FIELDS:
        assert hasattr(e, field)
    # UnclosedCompound is an end-of-input class: span and line_text are
    # populated, but there is no line number.
    assert e.error == "UnclosedCompound"
    assert e.line_text == "x: ["
    assert e.line is None
    assert isinstance(e.span, dict)

    with pytest.raises(ktav.KtavDecodeError) as dup:
        ktav.format("a: 1\na: 2")
    assert dup.value.error == "DuplicateKey"
    assert dup.value.line == 2
    assert dup.value.path == ["a"]


def test_base_class_catches_and_fields_present_on_both_leaves() -> None:
    caught: list[ktav.KtavError] = []
    try:
        ktav.loads("a: 1\na: 2")
    except ktav.KtavError as e:
        caught.append(e)
    try:
        ktav.dumps({"v": float("inf")})
    except ktav.KtavError as e:
        caught.append(e)
    assert len(caught) == 2
    assert isinstance(caught[0], ktav.KtavDecodeError)
    assert isinstance(caught[1], ktav.KtavEncodeError)
    for e in caught:
        for field in FIELDS:
            assert hasattr(e, field)


def test_message_matches_str_and_is_the_native_rendering() -> None:
    """`message` is the crate's own Display text.

    This binding has always used it for `str(exc)` — PyO3 hands the
    error straight to the exception constructor. The attribute exists so
    the envelope has the same ten-field shape here as it does over the C
    ABI, where `message` is the only way a host can reach that text
    without assembling its own. Five bindings used to assemble one, and
    all five disagreed with what this test pins.
    """
    with pytest.raises(ktav.KtavDecodeError) as exc_info:
        ktav.loads_strict("version: 1.10\n")
    e = exc_info.value
    expected = (
        "Syntax error: Line 1: LossyScalar: '1.10' would be inferred as a "
        "number and silently canonicalised to '1.1'; append '::' to keep it "
        "a String or write the canonical form"
    )
    assert e.message == expected
    assert str(e) == expected


def test_message_is_never_none() -> None:
    """Unlike the nine structured fields, `message` always has a value."""
    cases = (
        (ktav.loads, "a: 1\na: 2"),
        (ktav.loads, "a: ["),
        (ktav.loads_strict, "version: 1.10"),
    )
    for fn, src in cases:
        with pytest.raises(ktav.KtavError) as exc_info:
            fn(src)
        assert isinstance(exc_info.value.message, str)
        assert exc_info.value.message != ""
