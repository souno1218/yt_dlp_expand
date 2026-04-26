"""str_to_bool() のユニットテスト。 / Unit tests for str_to_bool()."""

import argparse

import pytest

from yt_dlp_expand.main_script import str_to_bool


@pytest.mark.parametrize("value", ["yes", "true", "True", "TRUE", "t", "y", "1"])
def test_str_to_bool_true(value: str) -> None:
    assert str_to_bool(value) is True


@pytest.mark.parametrize("value", ["no", "false", "False", "FALSE", "f", "n", "0"])
def test_str_to_bool_false(value: str) -> None:
    assert str_to_bool(value) is False


@pytest.mark.parametrize("value", [True, False])
def test_str_to_bool_passthrough_bool(value: bool) -> None:
    """bool が渡された場合はそのまま返す。 / Passthrough when already a bool."""
    assert str_to_bool(value) is value


@pytest.mark.parametrize("value", ["maybe", "2", "on", "off", ""])
def test_str_to_bool_invalid(value: str) -> None:
    with pytest.raises(argparse.ArgumentTypeError, match="Boolean value expected"):
        str_to_bool(value)
