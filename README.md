# yt_dlp_expand

yt-dlp を使って動画・音声をダウンロードし、サムネイルを自動埋め込みするラッパーパッケージです。  
iPhoneのショートカットApp + a-Shell からの呼び出しを想定して作成されました。

[iPhoneでショートカットappを使って、safariからYouTubeをダウンロードする](https://qiita.com/soun1218/items/3f07fbaa7029208dd789)

## Getting Started

### Prerequisites

以下が自動的にインストールされます。 / The following are installed automatically:

- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [mutagen](https://mutagen.readthedocs.io/en/latest/)
- [ffmpeg-python](https://github.com/kkroening/ffmpeg-python)

また、システムに **ffmpeg** がインストールされている必要があります。  
ffmpeg must also be installed on your system.

### Installing

**PyPI（a-Shell 推奨）:**
```bash
pip install yt_dlp_expand
```

**git から（mac/linux 等の通常環境）:**
```bash
pip install git+https://github.com/souno1218/yt_dlp_expand.git
```

## Download Modes

| Mode | 説明 |
|------|------|
| `0` | bestaudio → MP3（サムネイル埋め込み） |
| `1` | bestaudio → Opus（サムネイル埋め込み） |
| `2` | 720p MP4 (h264 + mp4a)（サムネイル埋め込み） |
| `3` | best MP4 (h264 + mp4a)（サムネイル埋め込み） |
| `4` | best MP4 (vp9 + opus)（サムネイル埋め込み） |

## Usage

### Terminal / CLI

```bash
yt_dlp_expand [-h] [-p PATH] [-l DOWNLOAD_PLAYLIST] download_mode url
```

**positional arguments:**

| 引数 | 説明 |
|------|------|
| `download_mode` | ダウンロードモード (0〜4) |
| `url` | 動画またはプレイリストの URL |

**options:**

| オプション | 説明 |
|-----------|------|
| `-p PATH`, `--path PATH` | 保存先ディレクトリパス（省略時: PC → `~/Downloads`, iOS → `~/Documents`） |
| `-l`, `--download_playlist` | プレイリスト全体をダウンロードするか（default: False） |

**Examples:**
```bash
# MP3 でダウンロード
yt_dlp_expand 0 "https://www.youtube.com/watch?v=xxxx"

# 720p MP4 で指定ディレクトリに保存
yt_dlp_expand 2 "https://www.youtube.com/watch?v=xxxx" -p ~/Movies

# プレイリストをまとめてダウンロード
yt_dlp_expand 1 "https://www.youtube.com/playlist?list=xxxx" -l true
```

### Python ライブラリとして使う

```python
from yt_dlp_expand import DownloadMode, ExpandYt_dlp

obj = ExpandYt_dlp(DownloadMode.AUDIO_MP3, "https://www.youtube.com/watch?v=xxxx")
obj.run()
```

## Built With

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) — 動画ダウンロード
- [mutagen](https://mutagen.readthedocs.io/en/latest/) — MP3/Opus へのサムネイル埋め込み
- [ffmpeg-python](https://github.com/kkroening/ffmpeg-python) — MP4 へのサムネイル埋め込み・クロップ

## Authors

- **河野 颯之介 (Sonosuke Kono)**

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
