## https://qiita.com/soun1218/items/3f07fbaa7029208dd789

"""yt-dlp を使って動画・音声をダウンロードし、サムネイルを埋め込むモジュール。

A yt-dlp wrapper that downloads video/audio and embeds thumbnails.
Originally created for use from the iPhone Shortcut App.
"""

from __future__ import annotations

import argparse
import base64
import logging
import pathlib
import platform
import random
import string
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from enum import IntEnum

import ffmpeg
from mutagen.flac import Picture
from mutagen.id3 import APIC, ID3
from mutagen.oggopus import OggOpus

logger = logging.getLogger(__name__)

# ファイル名として使えない文字と置換先の対応表
# Mapping of characters invalid in filenames to their replacements.
_INVALID_CHARS = str.maketrans(
    {":": "-", "[": "「", "]": "」", "/": "／", "\n": " ", "'": "'"}
)

_RANDOM_TITLE_LEN = 20


class DownloadMode(IntEnum):
    """ダウンロードモードの定数。 / Download mode constants."""

    AUDIO_MP3 = 0       # bestaudio → mp3
    AUDIO_OPUS = 1      # bestaudio → opus
    VIDEO_720P = 2      # 720p mp4 (h264 + mp4a)
    VIDEO_BEST_H264 = 3 # best mp4 (h264 + mp4a)
    VIDEO_BEST_VP9 = 4  # best mp4 (vp9 + opus)


def _sanitize_filename(title: str) -> str:
    """ファイル名に使えない文字を全角等価文字に置換する。

    Replace characters invalid in filenames with full-width equivalents.
    """
    return title.translate(_INVALID_CHARS).strip()


def _random_str(n: int) -> str:
    """長さ n のランダムな英数字文字列を生成する。

    Generate a random alphanumeric string of length n.
    """
    return "".join(random.choices(string.ascii_letters + string.digits, k=n))


def get_playlist_title(playlist_url: str) -> str | None:
    """プレイリストのタイトルを取得する。

    Fetch the playlist title via yt-dlp.
    Returns None if the title cannot be retrieved.
    """
    cp = subprocess.run(
        [
            sys.executable, "-m", "yt_dlp",
            playlist_url,
            "-I", "1:1",
            "--print", "%(playlist_title)s",
            "--skip-download",
            "--flat-playlist",
            "--no-check-certificate",
        ],
        encoding="utf-8",
        capture_output=True,
    )
    title = _sanitize_filename(cp.stdout.split("\n")[0])
    return title if title else None


def split_playlist_url(playlist_url: str) -> list[str]:
    """プレイリスト内の各動画 URL を取得する。

    Fetch individual video URLs from a playlist.
    Raises ValueError if no URLs are found.
    """
    cp = subprocess.run(
        [
            sys.executable, "-m", "yt_dlp",
            playlist_url,
            "--print", "%(url)s",
            "--skip-download",
            "--flat-playlist",
            "--no-check-certificate",
        ],
        encoding="utf-8",
        capture_output=True,
    )
    list_url = [u for u in cp.stdout.split("\n") if u]
    if not list_url:
        raise ValueError("Failed to retrieve playlist url.")
    return list_url


def check_is_pc() -> bool:
    """実行環境が PC (Mac/Linux/Windows) かを判定する。

    Return True if running on a desktop OS, False if on iPhone/iPad.
    Raises ValueError for unsupported operating systems.
    """
    os_name = platform.system()
    device = platform.platform()
    if os_name in ("Darwin", "iOS", "iPadOS"):
        return not ("iPhone" in device or "iPad" in device)
    if os_name in ("Linux", "Windows"):
        return True
    raise ValueError(f"Unsupported operating system: {os_name}")


def str_to_bool(v: str | bool) -> bool:
    """コマンドライン引数の文字列を bool に変換する。

    Convert a command-line string argument to a boolean value.
    Used as the ``type`` function for argparse arguments.
    """
    if isinstance(v, bool):
        return v
    if v.lower() in ("yes", "true", "t", "y", "1"):
        return True
    if v.lower() in ("no", "false", "f", "n", "0"):
        return False
    raise argparse.ArgumentTypeError("Boolean value expected.")


class ExpandYt_dlp:
    """yt-dlp を使って動画・音声をダウンロードし、サムネイルを埋め込むクラス。

    Downloads video/audio via yt-dlp and embeds the thumbnail into the output file.

    Args:
        download_mode: DownloadMode (0–4) またはその int 値。 / DownloadMode value (0–4).
        url: ダウンロード対象の URL。 / URL of the video or audio to download.
        path: 保存先ディレクトリパス。None の場合はデフォルトパスを使用。
              / Output directory path. Defaults to ~/Downloads (PC) or ~/Documents (iOS).
    """

    def __init__(
        self,
        download_mode: int,
        url: str,
        path: str | pathlib.Path | None = None,
    ) -> None:
        if download_mode not in range(5):
            raise ValueError("download_mode must be an integer from 0 to 4.")
        self.mode_num: int = int(download_mode)
        self.download_url: str = url
        self.is_pc: bool = check_is_pc()
        self.ext: str = {0: "mp3", 1: "opus", 2: "mp4", 3: "mp4", 4: "mp4"}[self.mode_num]
        self.title: str = ""

        if path is None:
            default = "~/Downloads" if self.is_pc else "~/Documents"
            self.output_path = pathlib.Path(default).expanduser()
        else:
            self.output_path = pathlib.Path(path).expanduser()

        if self.output_path.is_file():
            raise ValueError(
                f"A path specified as a directory is a file: {self.output_path}"
            )
        self.output_path.mkdir(parents=True, exist_ok=True)

        # 一時ファイル名（既存ファイルと衝突しない名前を生成する）
        # Generate a temporary filename that does not collide with existing files.
        self.random_title: str = self._generate_unique_random_title()

    def _generate_unique_random_title(self) -> str:
        """衝突しない一時ファイル名を生成する。

        Generate a temporary filename guaranteed not to collide with existing files.
        """
        suffixes = [
            ".jpg", ".webp",
            "_before.jpg", "_before.webp",
            f".{self.ext}", ".webm",
            f"_before.{self.ext}", "_before.webm",
        ]
        while True:
            candidate = _random_str(_RANDOM_TITLE_LEN)
            if all(
                not (self.output_path / f"{candidate}{s}").exists()
                for s in suffixes
            ):
                return candidate

    def get_title(self) -> None:
        """yt-dlp で動画タイトルを取得し self.title に格納する。

        Fetch the video title via yt-dlp and store it as ``self.title``.
        Raises ValueError if the title cannot be retrieved.
        """
        cp = subprocess.run(
            [
                sys.executable, "-m", "yt_dlp",
                self.download_url,
                "--skip-download",
                "--print", "%(title)s",
                "--no-check-certificate",
                "--no-playlist",
            ],
            encoding="utf-8",
            capture_output=True,
        )
        title = _sanitize_filename(cp.stdout.replace("\n", ""))
        if not title:
            raise ValueError("Failed to retrieve title.")
        self.title = title
        logger.info("get_title done: %s", self.title)

    def download_thumbnail_jpg(self) -> None:
        """yt-dlp でサムネイルを JPEG としてダウンロードする。

        Download the video thumbnail as a JPEG file via yt-dlp.
        Raises ValueError if the thumbnail cannot be downloaded.
        """
        if self.mode_num in (0, 1):
            stem = self.output_path / f"{self.random_title}_before"
        else:
            stem = self.output_path / self.random_title

        subprocess.run(
            [
                sys.executable, "-m", "yt_dlp",
                self.download_url,
                "--no-check-certificate",
                "--no-playlist",
                "--skip-download",
                "--write-thumbnail",
                "--convert-thumbnails", "jpg",
                "--output", str(stem),
            ],
            capture_output=True,
        )

        jpg_path  = stem.with_suffix(".jpg")
        webp_path = stem.with_suffix(".webp")
        if jpg_path.exists():
            logger.info("download_thumbnail_jpg done")
        elif webp_path.exists():
            webp_path.rename(jpg_path)
            logger.info("download_thumbnail_jpg done (renamed from .webp)")
        else:
            raise ValueError("Failed to download thumbnail.")

    def download_file(self) -> None:
        """yt-dlp で動画・音声ファイルをダウンロードする。

        Download the video or audio file via yt-dlp based on ``self.mode_num``.
        Raises ValueError if the file cannot be downloaded.
        """
        if self.mode_num in (0, 1):
            stem = self.output_path / self.random_title
        else:
            stem = self.output_path / f"{self.random_title}_before"

        base_cmd = [
            sys.executable, "-m", "yt_dlp",
            "--no-check-certificate",
            "--no-playlist",
            self.download_url,
            "-o", f"{stem}.%(ext)s",
        ]

        match self.mode_num:
            case 0:
                extra: list[str] = ["-f", "bestaudio", "--extract-audio", "--audio-format", "mp3"]
            case 1:
                extra = ["-f", "bestaudio[acodec~=opus]", "--extract-audio"]
            case 2:
                extra = [
                    "-f",
                    "bestvideo*[height=720][fps<=30][vcodec~='^(avc|h264)']+bestaudio[acodec~=mp4a]",
                ]
            case 3:
                extra = [
                    "-f",
                    "bestvideo*[vcodec~='^(avc|h264)']+bestaudio[acodec~=mp4a]",
                ]
            case 4:
                extra = ["-f", "bestvideo+bestaudio/best", "--merge-output-format", "mp4"]
            case _:
                raise ValueError(f"Invalid mode_num: {self.mode_num}")

        subprocess.run(
            base_cmd + extra,
            capture_output=True,
        )

        file_path = stem.with_suffix(f".{self.ext}")
        webm_path = stem.with_suffix(".webm")
        if file_path.exists():
            logger.info("download_file done")
        elif webm_path.exists():
            webm_path.rename(file_path)
            logger.info("download_file done (renamed from .webm)")
        else:
            raise ValueError("Failed to download file.")

    def merge_file_thumbnail_mp4(self) -> None:
        """ffmpeg で MP4 ファイルにサムネイルを埋め込む。

        Embed the thumbnail image into the MP4 file as an attached picture stream.
        """
        before = self.output_path / f"{self.random_title}_before.{self.ext}"
        cover  = self.output_path / f"{self.random_title}.jpg"
        output = self.output_path / f"{self.random_title}.{self.ext}"

        (
            ffmpeg.output(
                ffmpeg.input(str(before)),
                ffmpeg.input(str(cover)),
                str(output),
                c="copy",
                **{"c:v:1": "mjpeg", "disposition:v:1": "attached_pic"},
            )
            .global_args("-map", "0")
            .global_args("-map", "1")
            .global_args("-loglevel", "error")
            .run(overwrite_output=True)
        )
        before.unlink()
        cover.unlink()

        if not output.exists():
            raise ValueError("merge_file_thumbnail_mp4 failed.")
        logger.info("merge_file_thumbnail_mp4 done")

    def crop_thumbnail_square(self) -> None:
        """サムネイルを正方形にクロップする。

        Crop the downloaded thumbnail to a square using the shorter dimension.
        """
        before = self.output_path / f"{self.random_title}_before.jpg"
        output = self.output_path / f"{self.random_title}.jpg"

        probe = ffmpeg.probe(str(before))
        width = min(probe["streams"][0]["width"], probe["streams"][0]["height"])
        (
            ffmpeg.input(str(before))
            .filter("crop", width, width)
            .output(str(output))
            .run(overwrite_output=True)
        )
        before.unlink()

        if not output.exists():
            raise ValueError("crop_thumbnail_square failed.")
        logger.info("crop_thumbnail_square done")

    def merge_file_thumbnail_mp3(self) -> None:
        """mutagen で MP3 ファイルに ID3 タグとしてサムネイルを埋め込む。

        Embed the thumbnail into the MP3 file as an ID3 APIC (attached picture) tag.
        """
        audio_path = self.output_path / f"{self.random_title}.{self.ext}"
        cover_path = self.output_path / f"{self.random_title}.jpg"

        tags = ID3(str(audio_path))
        with open(cover_path, "rb") as img_file:
            apic = APIC(
                encoding=3,
                mime="image/jpeg",
                type=3,   # front cover
                desc="Cover",
                data=img_file.read(),
            )
        tags.add(apic)
        tags.save(v2_version=3)
        cover_path.unlink()

        if not audio_path.exists():
            raise ValueError("merge_file_thumbnail_mp3 failed.")
        logger.info("merge_file_thumbnail_mp3 done")

    def merge_file_thumbnail_opus(self) -> None:
        """mutagen で Opus ファイルにサムネイルを埋め込む。

        Embed the thumbnail into the Opus file as METADATA_BLOCK_PICTURE.
        """
        audio_path = self.output_path / f"{self.random_title}.{self.ext}"
        cover_path = self.output_path / f"{self.random_title}.jpg"

        pic = Picture()
        pic.mime = "image/jpeg"
        with open(cover_path, "rb") as thumbfile:
            pic.data = thumbfile.read()
        pic.type = 3  # front cover

        f = OggOpus(str(audio_path))
        f["METADATA_BLOCK_PICTURE"] = base64.b64encode(pic.write()).decode("ascii")
        f.save()
        cover_path.unlink()

        if not audio_path.exists():
            raise ValueError("merge_file_thumbnail_opus failed.")
        logger.info("merge_file_thumbnail_opus done")

    def run(self) -> None:
        """ダウンロードの全工程を実行する。

        Execute the full download pipeline:

        1. タイトル取得・サムネイル DL・ファイル DL を並列実行する。
           Fetch title, thumbnail, and file in parallel.
        2. サムネイルをトリミングしてファイルに埋め込む。
           Crop the thumbnail and embed it into the downloaded file.
        3. 最終ファイルをタイトル名にリネームする。
           Rename the output file to the video title.
        """
        with ThreadPoolExecutor(max_workers=3) as executor:
            f_title = executor.submit(self.get_title)
            f_thumb = executor.submit(self.download_thumbnail_jpg)
            f_file  = executor.submit(self.download_file)
            # 例外が発生していればここで再 raise する
            # Re-raise any exceptions from the parallel tasks.
            f_title.result()
            f_thumb.result()
            f_file.result()

        match self.mode_num:
            case 0:
                self.crop_thumbnail_square()
                self.merge_file_thumbnail_mp3()
            case 1:
                self.crop_thumbnail_square()
                self.merge_file_thumbnail_opus()
            case 2 | 3 | 4:
                self.merge_file_thumbnail_mp4()

        final_path = self.output_path / f"{self.title}.{self.ext}"
        (self.output_path / f"{self.random_title}.{self.ext}").rename(final_path)

        if not final_path.exists():
            raise ValueError("Download pipeline failed: final file not found.")
        logger.info("all process done: %s", final_path)


def main() -> None:
    """CLI エントリポイント。 / CLI entry point."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(prog="yt_dlp_expand")
    mode_help = (
        "0: bestaudio (mp3)\n"
        "1: bestaudio (opus)\n"
        "2: 720p mp4 (h264 + mp4a)\n"
        "3: best mp4 (h264 + mp4a)\n"
        "4: best mp4 (vp9 + opus)"
    )
    parser.add_argument("download_mode", type=int, help=mode_help, choices=list(range(5)))
    parser.add_argument(
        "url", type=str, help="動画またはプレイリストの URL / Video or playlist URL"
    )
    parser.add_argument(
        "-p", "--path", type=str, help="保存先ディレクトリパス / Download directory path"
    )
    parser.add_argument(
        "-l",
        "--download_playlist",
        help="プレイリスト全体をダウンロードするか (default: False) / Download entire playlist",
        type=str_to_bool,
        default=False,
    )

    args = parser.parse_args()
    is_url_contain_playlist = ("&list=" in args.url) or ("playlist?list=" in args.url)

    if args.download_playlist and is_url_contain_playlist:
        logger.info("Downloading playlist...")
        is_pc = check_is_pc()
        if args.path is None:
            dir_path = pathlib.Path("~/Downloads" if is_pc else "~/Documents").expanduser()
        else:
            dir_path = pathlib.Path(args.path.rstrip("/")).expanduser()

        playlist_title = get_playlist_title(args.url)
        if playlist_title is None:
            logger.warning("Failed to retrieve playlist title.")
        elif not dir_path.is_file():
            logger.info("playlist_title: %s", playlist_title)
            dir_path = dir_path / playlist_title

        if dir_path.is_file():
            raise ValueError(f"A path specified as a directory is a file: {dir_path}")
        dir_path.mkdir(parents=True, exist_ok=True)

        for video_url in split_playlist_url(args.url):
            ExpandYt_dlp(args.download_mode, video_url, dir_path).run()
    else:
        if is_url_contain_playlist:
            logger.info(
                "Playlist URL detected, but --download_playlist is False. "
                "Downloading single video."
            )
        ExpandYt_dlp(args.download_mode, args.url, args.path).run()
