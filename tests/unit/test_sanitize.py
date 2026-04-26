"""_sanitize_filename() のユニットテスト。 / Unit tests for _sanitize_filename()."""

import pytest

from yt_dlp_expand.main_script import _sanitize_filename


@pytest.mark.parametrize(
    "raw, expected",
    [
        # ファイル名禁止文字が置換されること
        ("title: subtitle", "title- subtitle"),
        ("[playlist] video", "「playlist」 video"),
        ("path/to/file", "path／to／file"),
        # シングルクォートが右シングルクォート(U+2019)に置換されること
        ("it’s fine", "it’s fine"),
        # 改行が空白に置換されること
        ("line1\nline2", "line1 line2"),
        # 前後の空白が除去されること
        ("  spaces  ", "spaces"),
        # 変換不要な文字は変わらないこと
        ("normal title", "normal title"),
        # 空文字列
        ("", ""),
    ],
)
def test_sanitize_filename(raw: str, expected: str) -> None:
    assert _sanitize_filename(raw) == expected
