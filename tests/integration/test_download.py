"""実際のダウンロードを行う統合テスト。

End-to-end integration tests that perform real downloads.
Run with: pytest -m integration tests/integration/

Note: Requires network access, yt-dlp, and ffmpeg to be installed.
"""

import pathlib

import pytest

from tests.conftest import TEST_VIDEO_URL
from yt_dlp_expand.main_script import DownloadMode, ExpandYt_dlp


def _run_download(tmp_path: pathlib.Path, mode: DownloadMode) -> pathlib.Path:
    """ダウンロードを実行して出力ファイルのパスを返すヘルパー。

    Run a download and return the output file path.
    """
    obj = ExpandYt_dlp(mode, TEST_VIDEO_URL, tmp_path)
    obj.run()
    ext = {
        DownloadMode.AUDIO_MP3: "mp3",
        DownloadMode.AUDIO_OPUS: "opus",
        DownloadMode.VIDEO_720P: "mp4",
        DownloadMode.VIDEO_BEST_H264: "mp4",
        DownloadMode.VIDEO_BEST_VP9: "mp4",
    }[mode]
    files = list(tmp_path.glob(f"*.{ext}"))
    assert len(files) == 1, f"Expected 1 .{ext} file, found {len(files)}"
    return files[0]


@pytest.mark.integration
def test_download_audio_mp3(tmp_path: pathlib.Path) -> None:
    """mode 0: MP3 ファイルが生成され、ID3 タグにサムネイルが埋め込まれること。"""
    from mutagen.id3 import ID3

    out = _run_download(tmp_path, DownloadMode.AUDIO_MP3)
    assert out.stat().st_size > 0
    tags = ID3(str(out))
    assert any(k.startswith("APIC:") for k in tags), "Thumbnail should be embedded as APIC tag"


@pytest.mark.integration
def test_download_audio_opus(tmp_path: pathlib.Path) -> None:
    """mode 1: Opus ファイルが生成され、サムネイルが埋め込まれること。"""
    import base64

    from mutagen.oggopus import OggOpus

    out = _run_download(tmp_path, DownloadMode.AUDIO_OPUS)
    assert out.stat().st_size > 0
    f = OggOpus(str(out))
    assert "METADATA_BLOCK_PICTURE" in f, "Thumbnail should be embedded"
    # base64 としてデコードできること
    base64.b64decode(f["METADATA_BLOCK_PICTURE"][0])


@pytest.mark.integration
def test_download_video_720p(tmp_path: pathlib.Path) -> None:
    """mode 2: 720p MP4 ファイルが生成されること。"""
    out = _run_download(tmp_path, DownloadMode.VIDEO_720P)
    assert out.stat().st_size > 0


@pytest.mark.integration
def test_download_video_best_h264(tmp_path: pathlib.Path) -> None:
    """mode 3: best MP4 (h264) ファイルが生成されること。"""
    out = _run_download(tmp_path, DownloadMode.VIDEO_BEST_H264)
    assert out.stat().st_size > 0


@pytest.mark.integration
def test_download_video_best_vp9(tmp_path: pathlib.Path) -> None:
    """mode 4: best MP4 (vp9) ファイルが生成されること。"""
    out = _run_download(tmp_path, DownloadMode.VIDEO_BEST_VP9)
    assert out.stat().st_size > 0
