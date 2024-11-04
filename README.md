# yt_dlp_expand
Originally created for use from the iPhone shortcut app in an article called Qiita.   
Uploaded for download.   
[iPhoneでショートカットappを使って、safariからYouTubeをダウンロードする](https://qiita.com/soun1218/items/3f07fbaa7029208dd789)   

## Getting Started
### Prerequisites
Requires yt-dlp,mutagen,ffmpeg-python. If not, installation is automatic.

### Installing
First, activate the virtual environment if it is separated by conda.
```bash
#examples
conda activate myenv
```
Download and Installation
```bash
pip install git+https://github.com/souno1218/yt_dlp_expand.git
```

## Running
#### Use directly from Terminal or other sources
```bash
yt_dlp_expand [-h] [-p PATH] Download_mode url
```
positional arguments:
  Download_mode         0:bestaudio(mp3),
                        1:bestaudio(opus),
                        2:720p,mp4(h264,mp4a),
                        3:bestvideo(mp4(h264,mp4a)),
                        4:bestvideo(mp4(vp9,opus))
  url                   url

options:
  -h, --help            show this help message and exit
  -p PATH, --path PATH  downloadMode dir path, 

path default: PC -> "~/Downloads" , iOS -> "~/Documents"

#### Used from python
```python
from yt_dlp_expand import ExpandYt_dlp
Class_Yt_dlp = ExpandYt_dlp(DownloadMode, url, path)
Class_Yt_dlp.main_func()
```
For each argument, see Terminal use.

## Built With
* [yt-dlp](https://github.com/yt-dlp/yt-dlp) - main
* [mutagen](https://mutagen.readthedocs.io/en/latest/) - marge file thumbnail mp3,opus
* [ffmpeg-python](https://github.com/kkroening/ffmpeg-python) - marge file thumbnail mp4 , crop thumbnail square

## Authors
* **河野 颯之介(Sonosuke Kono)**

## License
This project is licensed under Apache License, Version 2.0 - see the [LICENSE.md](LICENSE.md) file for details.   
