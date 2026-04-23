"""Error taxonomy and propagation."""

import ktav
import pytest


def test_decode_error_subclasses_ktav_error():
    assert issubclass(ktav.KtavDecodeError, ktav.KtavError)


def test_encode_error_subclasses_ktav_error():
    assert issubclass(ktav.KtavEncodeError, ktav.KtavError)


def test_ktav_error_is_exception():
    assert issubclass(ktav.KtavError, Exception)


def test_unbalanced_open_bracket():
    with pytest.raises(ktav.KtavDecodeError):
        ktav.loads("x: [")


def test_mismatched_bracket():
    with pytest.raises(ktav.KtavDecodeError):
        ktav.loads("x: [\n}")


def test_duplicate_key():
    with pytest.raises(ktav.KtavDecodeError):
        ktav.loads("a: 1\na: 2")


def test_inline_non_empty_compound():
    with pytest.raises(ktav.KtavDecodeError):
        ktav.loads("x: { a: 1 }")


def test_invalid_typed_scalar_body():
    with pytest.raises(ktav.KtavDecodeError):
        ktav.loads("n:i not-a-number")


def test_decode_error_message_is_non_empty():
    with pytest.raises(ktav.KtavDecodeError) as info:
        ktav.loads("x: [")
    assert str(info.value)


def test_encode_error_message_is_non_empty():
    with pytest.raises(ktav.KtavEncodeError) as info:
        ktav.dumps({"v": float("nan")})
    assert str(info.value)


def test_catching_base_catches_decode():
    try:
        ktav.loads("x: [")
    except ktav.KtavError:
        pass
    else:
        pytest.fail("expected KtavError to catch KtavDecodeError")


def test_catching_base_catches_encode():
    try:
        ktav.dumps({"v": float("inf")})
    except ktav.KtavError:
        pass
    else:
        pytest.fail("expected KtavError to catch KtavEncodeError")
