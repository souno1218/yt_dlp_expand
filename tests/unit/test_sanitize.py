"""_sanitize_filename() のユニットテスト。 / Unit tests for _sanitize_filename()."""

import pytest

from yt_dlp_expand.main_script import _sanitize_filename


@pytest.mark.parametrize(
    "raw, expected",
    [
        # コロンはハイフンに置換されること
        ("title: subtitle", "title- subtitle"),
        # 角括弧は丸括弧に置換されること（全角ではなくASCII）
        ("[playlist] video", "(playlist) video"),
        # スラッシュはハイフンに置換されること（全角スラッシュは使わない）
        ("path/to/file", "path-to-file"),
        # バックスラッシュはハイフンに置換されること
        ("path\\to\\file", "path-to-file"),
        # 改行が空白に置換されること
        ("line1\nline2", "line1 line2"),
        # iOS で問題を起こす文字が除去されること
        ("what? * this", "what  this"),
        ('"quoted"', "quoted"),
        ("<tag>", "tag"),
        ("a|b", "ab"),
        # 前後の空白が除去されること
        ("  spaces  ", "spaces"),
        # 変換不要な文字は変わらないこと
        ("normal title", "normal title"),
        # シングルクォートはそのまま残ること
        ("it's fine", "it's fine"),
        # 空文字列
        ("", ""),
    ],
)
def test_sanitize_filename(raw: str, expected: str) -> None:
    assert _sanitize_filename(raw) == expected
