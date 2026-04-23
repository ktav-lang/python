"""Parser behaviour — :func:`ktav.loads` across the format's constructs."""

import ktav


def test_empty_document_is_empty_object():
    assert ktav.loads("") == {}


def test_whitespace_only_document():
    assert ktav.loads("   \n\n\t\n") == {}


def test_comment_only_document():
    assert ktav.loads("# comment\n# another one\n") == {}


def test_simple_scalar_string():
    assert ktav.loads("name: hello") == {"name": "hello"}


def test_multiple_scalars_preserve_order():
    result = ktav.loads("b: 1\na: 2\nc: 3")
    assert list(result) == ["b", "a", "c"]


def test_keyword_null():
    assert ktav.loads("x: null") == {"x": None}


def test_keyword_booleans():
    assert ktav.loads("on: true\noff: false") == {"on": True, "off": False}


def test_scalar_without_marker_stays_string():
    # Ktav philosophy: no magic types. Unmarked `8080` is a string.
    assert ktav.loads("port: 8080") == {"port": "8080"}


def test_integer_marker_gives_int():
    assert ktav.loads("port:i 8080") == {"port": 8080}


def test_float_marker_gives_float():
    assert ktav.loads("ratio:f 0.5") == {"ratio": 0.5}


def test_negative_integer_marker():
    assert ktav.loads("offset:i -42") == {"offset": -42}


def test_big_integer_preserves_precision():
    huge = "1" + "0" * 40
    assert ktav.loads(f"n:i {huge}") == {"n": int(huge)}


def test_literal_string_marker():
    assert ktav.loads("pattern:: [a-z]+") == {"pattern": "[a-z]+"}


def test_literal_string_preserves_keyword_like():
    assert ktav.loads("flag:: true") == {"flag": "true"}


def test_dotted_keys_expand():
    result = ktav.loads("server.host: a.example\nserver.port:i 80")
    assert result == {"server": {"host": "a.example", "port": 80}}


def test_array_of_scalars():
    text = "tags: [\n  a\n  b\n  c\n]"
    assert ktav.loads(text) == {"tags": ["a", "b", "c"]}


def test_nested_object_multiline():
    text = "srv: {\n  host: a.example\n  port:i 80\n}"
    assert ktav.loads(text) == {"srv": {"host": "a.example", "port": 80}}


def test_empty_compounds():
    assert ktav.loads("meta: {}\ntags: []") == {"meta": {}, "tags": []}


def test_multiline_string_stripped():
    text = "body: (\n  hello\n  world\n)"
    assert ktav.loads(text) == {"body": "hello\nworld"}


def test_multiline_string_verbatim():
    text = "body: ((\n  hello\n))"
    assert ktav.loads(text) == {"body": "  hello"}


def test_bytes_input_decodes_utf8():
    assert ktav.loads(b"name: hello") == {"name": "hello"}


def test_bytes_input_non_ascii():
    assert ktav.loads("city: Москва".encode()) == {"city": "Москва"}


def test_array_of_objects():
    text = (
        "upstreams: [\n"
        "  {\n    host: a.example\n    port:i 80\n  }\n"
        "  {\n    host: b.example\n    port:i 81\n  }\n"
        "]"
    )
    assert ktav.loads(text) == {
        "upstreams": [
            {"host": "a.example", "port": 80},
            {"host": "b.example", "port": 81},
        ]
    }
