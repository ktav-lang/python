"""File-like wrappers — :func:`ktav.load` / :func:`ktav.dump`."""

import io

import ktav


def test_load_text_stream():
    fp = io.StringIO("name: hello")
    assert ktav.load(fp) == {"name": "hello"}


def test_load_binary_stream():
    fp = io.BytesIO(b"name: hello")
    assert ktav.load(fp) == {"name": "hello"}


def test_dump_text_stream():
    fp = io.StringIO()
    ktav.dump({"name": "hello"}, fp)
    fp.seek(0)
    assert fp.read() == "name: hello\n"


def test_dump_binary_stream():
    fp = io.BytesIO()
    ktav.dump({"name": "hello"}, fp)
    assert fp.getvalue() == b"name: hello\n"


def test_dump_to_file_path(tmp_path):
    path = tmp_path / "c.ktav"
    with path.open("w", encoding="utf-8") as f:
        ktav.dump({"port": 8080, "name": "service"}, f)
    assert path.read_text(encoding="utf-8") == "port:i 8080\nname: service\n"


def test_load_from_file_path(tmp_path):
    path = tmp_path / "c.ktav"
    path.write_text("port:i 8080\nname: service\n", encoding="utf-8")
    with path.open(encoding="utf-8") as f:
        assert ktav.load(f) == {"port": 8080, "name": "service"}


def test_load_from_file_path_binary(tmp_path):
    path = tmp_path / "c.ktav"
    path.write_bytes(b"port:i 8080\nname: service\n")
    with path.open("rb") as f:
        assert ktav.load(f) == {"port": 8080, "name": "service"}
