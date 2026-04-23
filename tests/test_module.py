"""Module-level surface area: exported names, version strings."""

import re

import ktav


def test_version_is_semver_string():
    assert isinstance(ktav.__version__, str)
    assert re.fullmatch(r"\d+\.\d+\.\d+(?:[-.].*)?", ktav.__version__)


def test_spec_version_is_declared():
    assert isinstance(ktav.__spec_version__, str)
    assert re.fullmatch(r"\d+\.\d+\.\d+", ktav.__spec_version__)


def test_public_names_exported():
    names = set(ktav.__all__)
    expected = {
        "KtavDecodeError",
        "KtavEncodeError",
        "KtavError",
        "__spec_version__",
        "__version__",
        "dump",
        "dumps",
        "load",
        "loads",
    }
    assert expected <= names


def test_public_symbols_resolve():
    for name in ktav.__all__:
        assert getattr(ktav, name) is not None, name
