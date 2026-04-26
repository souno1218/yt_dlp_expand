"""ExpandYt_dlp クラスのモックテスト。 / Mock-based tests for ExpandYt_dlp."""

import pathlib
from unittest.mock import MagicMock, patch

import pytest

from yt_dlp_expand.main_script import DownloadMode, ExpandYt_dlp


# -------------------------------------------------------------------
# __init__ のテスト
# -------------------------------------------------------------------


def test_init_creates_output_dir(tmp_path: pathlib.Path) -> None:
    """指定パスが存在しない場合、ディレクトリが作成されること。"""
    new_dir = tmp_path / "new_output"
    with patch("yt_dlp_expand.main_script.check_is_pc", return_value=True):
        obj = ExpandYt_dlp(DownloadMode.AUDIO_MP3, "https://example.com/watch?v=test", new_dir)
    assert new_dir.is_dir()
    assert obj.ext == "mp3"
    assert obj.mode_num == 0


def test_init_raises_if_path_is_file(tmp_path: pathlib.Path) -> None:
    """パスがファイルの場合は ValueError を送出すること。"""
    file_path = tmp_path / "file.txt"
    file_path.touch()
    with patch("yt_dlp_expand.main_script.check_is_pc", return_value=True):
        with pytest.raises(ValueError, match="is a file"):
            ExpandYt_dlp(DownloadMode.AUDIO_MP3, "https://example.com/", file_path)


def test_init_invalid_download_mode(tmp_path: pathlib.Path) -> None:
    """範囲外の download_mode は ValueError を送出すること。"""
    with patch("yt_dlp_expand.main_script.check_is_pc", return_value=True):
        with pytest.raises(ValueError, match="download_mode must be"):
            ExpandYt_dlp(99, "https://example.com/", tmp_path)


@pytest.mark.parametrize(
    "mode, expected_ext",
    [
        (DownloadMode.AUDIO_MP3, "mp3"),
        (DownloadMode.AUDIO_OPUS, "opus"),
        (DownloadMode.VIDEO_720P, "mp4"),
        (DownloadMode.VIDEO_BEST_H264, "mp4"),
        (DownloadMode.VIDEO_BEST_VP9, "mp4"),
    ],
)
def test_init_ext_by_mode(
    tmp_path: pathlib.Path, mode: DownloadMode, expected_ext: str
) -> None:
    """DownloadMode ごとに正しい拡張子が設定されること。"""
    with patch("yt_dlp_expand.main_script.check_is_pc", return_value=True):
        obj = ExpandYt_dlp(mode, "https://example.com/", tmp_path)
    assert obj.ext == expected_ext


# -------------------------------------------------------------------
# run() のテスト（各メソッドをモック）
# -------------------------------------------------------------------


def _make_obj(tmp_path: pathlib.Path, mode: int = 0) -> ExpandYt_dlp:
    """テスト用の ExpandYt_dlp インスタンスを生成するヘルパー。"""
    with patch("yt_dlp_expand.main_script.check_is_pc", return_value=True):
        return ExpandYt_dlp(mode, "https://example.com/watch?v=test", tmp_path)


def test_run_calls_all_methods_mode0(tmp_path: pathlib.Path) -> None:
    """mode 0 (AUDIO_MP3) で必要なメソッドが全て呼ばれること。"""
    obj = _make_obj(tmp_path, 0)

    def mock_get_title() -> None:
        obj.title = "Test Title"

    with (
        patch.object(obj, "get_title", side_effect=mock_get_title) as m_title,
        patch.object(obj, "download_thumbnail_jpg") as m_thumb,
        patch.object(obj, "download_file") as m_file,
        patch.object(obj, "crop_thumbnail_square") as m_crop,
        patch.object(obj, "merge_file_thumbnail_mp3") as m_merge,
    ):
        # 最終ファイルを仮作成してリネームを通す
        (tmp_path / f"{obj.random_title}.mp3").touch()
        obj.run()

    m_title.assert_called_once()
    m_thumb.assert_called_once()
    m_file.assert_called_once()
    m_crop.assert_called_once()
    m_merge.assert_called_once()


def test_run_calls_all_methods_mode1(tmp_path: pathlib.Path) -> None:
    """mode 1 (AUDIO_OPUS) で必要なメソッドが全て呼ばれること。"""
    obj = _make_obj(tmp_path, 1)

    def mock_get_title() -> None:
        obj.title = "Test Opus"

    with (
        patch.object(obj, "get_title", side_effect=mock_get_title),
        patch.object(obj, "download_thumbnail_jpg"),
        patch.object(obj, "download_file"),
        patch.object(obj, "crop_thumbnail_square") as m_crop,
        patch.object(obj, "merge_file_thumbnail_opus") as m_merge,
    ):
        (tmp_path / f"{obj.random_title}.opus").touch()
        obj.run()

    m_crop.assert_called_once()
    m_merge.assert_called_once()


@pytest.mark.parametrize("mode", [2, 3, 4])
def test_run_calls_merge_mp4_for_video_modes(
    tmp_path: pathlib.Path, mode: int
) -> None:
    """mode 2/3/4 (video) で merge_file_thumbnail_mp4 が呼ばれること。"""
    obj = _make_obj(tmp_path, mode)

    def mock_get_title() -> None:
        obj.title = "Test Video"

    with (
        patch.object(obj, "get_title", side_effect=mock_get_title),
        patch.object(obj, "download_thumbnail_jpg"),
        patch.object(obj, "download_file"),
        patch.object(obj, "merge_file_thumbnail_mp4") as m_merge,
    ):
        (tmp_path / f"{obj.random_title}.mp4").touch()
        obj.run()

    m_merge.assert_called_once()


def test_run_renames_to_title(tmp_path: pathlib.Path) -> None:
    """run() 完了後にファイルがタイトル名にリネームされること。"""
    obj = _make_obj(tmp_path, 0)

    def mock_get_title() -> None:
        obj.title = "My Song"

    with (
        patch.object(obj, "get_title", side_effect=mock_get_title),
        patch.object(obj, "download_thumbnail_jpg"),
        patch.object(obj, "download_file"),
        patch.object(obj, "crop_thumbnail_square"),
        patch.object(obj, "merge_file_thumbnail_mp3"),
    ):
        (tmp_path / f"{obj.random_title}.mp3").touch()
        obj.run()

    assert (tmp_path / "My Song.mp3").exists()
