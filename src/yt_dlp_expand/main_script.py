## https://qiita.com/soun1218/items/3f07fbaa7029208dd789

from mutagen.id3 import APIC, ID3
from mutagen.oggopus import OggOpus
from mutagen.flac import Picture
import os, ffmpeg, base64, pathlib, argparse, platform, subprocess


def main():
    parser = argparse.ArgumentParser()
    txt = "0:bestaudio(mp3),\n1:bestaudio(opus),\n2:720p,mp4(h264,mp4a),\n3:bestvideo(mp4(h264,mp4a)),\n4:bestvideo(mp4(vp9,opus))"
    parser.add_argument("DownloadMode", type=int, help=txt, choices=list(range(5)))
    parser.add_argument("url", type=str, help="url")
    parser.add_argument("-p", "--path", type=str, help="downloadMode dir path")
    parser.add_argument("-l", "--playlist", type=bool, help="use playlist or not ", default=False)
    args = parser.parse_args()
    if args.playlist and ("&list=" in args.url):
        is_pc = check_is_pc()
        if args.path is None:
            if is_pc:
                dir_path = "~/Downloads"
            else:
                dir_path = "~/Documents"
        else:
            dir_path = args.path if args.path[-1] != "/" else args.path[:-1]

        dir_path = pathlib.Path(dir_path).expanduser()

        playlist_title = get_playlist_title(args.url)
        if playlist_title is None:
            print("Failed to retrieve playlist title.")
        elif not os.path.isfile(dir_path):
            dir_path = f"{dir_path}/{playlist_title}"

        if os.path.isfile(dir_path):
            raise ValueError(f"A path specified as a directory is a file : {dir_path}")
        if not os.path.isdir(dir_path):
            os.makedirs(dir_path)

        list_url = split_playlist_url(args.url)
        for i in list_url:
            Class_Yt_dlp = ExpandYt_dlp(args.DownloadMode, i, dir_path)
            Class_Yt_dlp.main_func()
    else:
        Class_Yt_dlp = ExpandYt_dlp(args.DownloadMode, args.url, args.path)
        Class_Yt_dlp.main_func()


def get_playlist_title(playlist_url):
    script = (
        f"yt-dlp '{playlist_url}' "
        "-I 1:1 "
        "--print '%(playlist_title)s' "
        "--skip-download "
        "--flat-playlist "
        "--no-check-certificate "
    )
    cp = subprocess.run(script, encoding="utf-8", stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    playlist_title = cp.stdout.split("\n")[0]

    replaceList = {":": "-", "[": "「", "]": "」", "/": "／", "\n": " ", "'": "’"}
    for key, value in replaceList.items():
        playlist_title = playlist_title.replace(key, value)

    if len(playlist_title) == 0:
        return None
    else:
        return playlist_title


def split_playlist_url(playlist_url):
    script = f"yt-dlp '{playlist_url}' --print '%(url)s' --skip-download --flat-playlist --no-check-certificate"
    cp = subprocess.run(script, encoding="utf-8", stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    list_url = []
    for i in cp.stdout.split("\n"):
        if not len(i) == 0:
            list_url.append(i)

    if len(list_url) == 0:
        raise ValueError("Failed to retrieve playlist url.")
    else:
        return list_url


def check_is_pc():
    os_name = platform.system()
    if not os_name in [
        "Darwin",
        "Linux",
        "Windows",
    ]:
        raise ValueError("Use on an operating system that is not intended for")

    is_pc = True
    if os_name == "Darwin":
        device = platform.platform().split("-")[2]
        if ("iPhone" in device) or ("iPad" in device):
            is_pc = False
    return is_pc


def exist(path):
    return os.path.exists(path)


class ExpandYt_dlp:
    def __init__(self, DownloadMode, url, path=None):
        if not DownloadMode in [0, 1, 2, 3, 4]:
            raise ValueError("DownloadMode must be selected from 0~4,int.")
        else:
            self.mode_num = DownloadMode
        self.download_url = url
        self.is_pc = check_is_pc()
        self.ext = {0: "mp3", 1: "opus", 2: "mp4", 3: "mp4", 4: "mp4"}[self.mode_num]
        if path is None:
            if self.is_pc:
                path = "~/Downloads"
            else:
                path = "~/Documents"
        self.output_path = pathlib.Path(path).expanduser()
        if os.path.isfile(self.output_path):
            raise ValueError(f"A path specified as a directory is a file : {self.output_path}")
        if not os.path.isdir(self.output_path):
            os.makedirs(self.output_path)

    def getTitle(self):
        # get title
        script = (
            f"yt-dlp '{self.download_url}' "
            "--skip-download "
            "--print '%(title)s' "
            "--no-check-certificate "
            "--no-playlist "
        )
        cp = subprocess.run(script, encoding="utf-8", stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        self.title = cp.stdout.replace("\n", "")
        replaceList = {":": "-", "[": "「", "]": "」", "/": "／", "\n": " ", "'": "’"}
        for key, value in replaceList.items():
            self.title = self.title.replace(key, value)
        if len(self.title) != 0:
            print(f"getTitle Done : {self.title}")
        else:
            raise ValueError("Failed to retrieve title.")

        # make thumbnail path
        thumbnail_path_no_ext = f"{self.output_path}/{self.title}"
        if exist(f"{thumbnail_path_no_ext}.jpg") or exist(f"{thumbnail_path_no_ext}_before.jpg"):
            n = 0
            is_exist = exist(f"{thumbnail_path_no_ext}_{n}.jpg") or exist(f"{thumbnail_path_no_ext}_{n}_before.jpg")
            while is_exist:
                n += 1
                is_exist = exist(f"{thumbnail_path_no_ext}_{n}.jpg") or exist(f"{thumbnail_path_no_ext}_{n}_before.jpg")
                if n == 10000:
                    raise ValueError(f"Too many files with duplicate names. : {thumbnail_path_no_ext}_N.jpg")
            thumbnail_path_no_ext = f"{thumbnail_path_no_ext}_{n}"
        self.final_thumbnail_path = f"{thumbnail_path_no_ext}.jpg"
        if self.mode_num in [0, 1]:
            thumbnail_path_no_ext = f"{thumbnail_path_no_ext}_before"
        self.thumbnail_path = f"{thumbnail_path_no_ext}.jpg"
        self.thumbnail_path_no_ext = thumbnail_path_no_ext

        # make file path
        file_path_no_ext = f"{self.output_path}/{self.title}"
        if exist(f"{file_path_no_ext}.{self.ext}") or exist(f"{file_path_no_ext}_before.{self.ext}"):
            n = 0
            is_exist = exist(f"{file_path_no_ext}_{n}.{self.ext}") or exist(f"{file_path_no_ext}_{n}_before.{self.ext}")
            while is_exist:
                n += 1
                is_exist = exist(f"{file_path_no_ext}_{n}.{self.ext}") or exist(
                    f"{file_path_no_ext}_{n}_before.{self.ext}"
                )
                if n == 10000:
                    raise ValueError(f"Too many files with duplicate names. : {file_path_no_ext}_N.{self.ext}")
            file_path_no_ext = f"{file_path_no_ext}_{n}"
        self.final_file_path = f"{file_path_no_ext}.{self.ext}"
        if self.mode_num in [2, 3, 4]:
            file_path_no_ext = f"{file_path_no_ext}_before"
        self.file_path = f"{file_path_no_ext}.{self.ext}"
        self.file_path_no_ext = file_path_no_ext

    def download_thumbnail_jpg(self):
        # download thumbnail
        script = (
            f"yt-dlp '{self.download_url}' "
            "--no-check-certificate "
            "--no-playlist "
            "--skip-download "
            "--write-thumbnail "
            "--convert-thumbnails jpg "
            f"--output '{self.thumbnail_path_no_ext}'"
        )
        subprocess.run(script, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)

        if exist(self.thumbnail_path):
            print(f"download_thumbnail_jpg Done")
        else:
            raise ValueError("Failed download_thumbnail_jpg")

    def download_file(self):
        # download file
        script = f"yt-dlp --no-check-certificate --no-playlist '{self.download_url}' "
        match self.mode_num:
            case 0:
                script += f"-o '{self.file_path_no_ext}.%(ext)s' -f 'bestaudio' --extract-audio --audio-format mp3"
            case 1:
                script += f"-o '{self.file_path_no_ext}.%(ext)s' -f 'bestaudio[acodec~=opus]' --extract-audio"
            case 2:
                script += (
                    f"-o '{self.file_path_no_ext}.%(ext)s' "
                    "-f \"bestvideo*[height=720][fps<=30][vcodec~='^(avc|h264)']"
                    '+bestaudio[acodec~=mp4a]" '
                )
            case 3:
                script += (
                    f"-o '{self.file_path_no_ext}.%(ext)s' "
                    "-f \"bestvideo*[vcodec~='^(avc|h264)']+bestaudio[acodec~=mp4a]\" "
                )
            case 4:
                script += (
                    f"-o '{self.file_path_no_ext}.%(ext)s' "
                    "-f 'bestvideo+bestaudio/best' "
                    "--merge-output-format mp4"
                )
        subprocess.run(script, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)

        if exist(self.file_path):
            print("download_file Done")
        else:
            raise ValueError("Failed download_file")

    def marge_file_thumbnail_mp4(self):
        video = ffmpeg.input(self.file_path)
        cover = ffmpeg.input(self.final_thumbnail_path)
        (
            ffmpeg.output(
                video,
                cover,
                self.final_file_path,
                c="copy",
                **{"c:v:1": "mjpeg"},
                **{"disposition:v:1": "attached_pic"},
            )
            .global_args("-map", "0")
            .global_args("-map", "1")
            .global_args("-loglevel", "error")
            .run(overwrite_output=True)
        )
        os.remove(self.final_thumbnail_path)
        os.remove(self.file_path)

        if exist(self.final_file_path):
            print("marge_file_thumbnail_mp4 Done")
        else:
            raise ValueError("Failed marge_file_thumbnail_mp4")

    def crop_thumbnail_square(self):
        probe = ffmpeg.probe(self.thumbnail_path)
        width = min(probe["streams"][0]["width"], probe["streams"][0]["height"])
        (
            ffmpeg.input(self.thumbnail_path)
            .filter("crop", width, width)
            .output(self.final_thumbnail_path)
            .run(overwrite_output=True)
        )
        os.remove(self.thumbnail_path)

        if exist(self.final_thumbnail_path):
            print("crop_thumbnail_square Done")
        else:
            raise ValueError("Failed crop_thumbnail_square")

    def marge_file_thumbnail_mp3(self):
        file = ID3(self.final_file_path)
        meta_data = APIC()
        with open(self.final_thumbnail_path, "rb") as img_file:
            meta_data.encoding = 3
            meta_data.mime = "image/jpeg"
            meta_data.type = 3
            meta_data.desc = "Cover"
            meta_data.data = img_file.read()
            file.add(meta_data)
        file.save(v2_version=3)

        os.remove(self.final_thumbnail_path)

        if exist(self.final_file_path):
            print("marge_file_thumbnail_mp3 Done")
        else:
            raise ValueError("Failed marge_file_thumbnail_mp3")

    def marge_file_thumbnail_opus(self):
        pic = Picture()
        f = OggOpus(self.final_file_path)
        pic.mime = f"image/jpeg"
        with open(self.final_thumbnail_path, "rb") as thumbfile:
            pic.data = thumbfile.read()
        pic.type = 3  # front cover
        f["METADATA_BLOCK_PICTURE"] = base64.b64encode(pic.write()).decode("ascii")
        f.save()

        os.remove(self.final_thumbnail_path)

        if exist(self.final_file_path):
            print("marge_file_thumbnail_opus Done")
        else:
            raise ValueError("Failed marge_file_thumbnail_opus")

    def main_func(self):
        self.getTitle()
        self.download_thumbnail_jpg()
        self.download_file()
        match self.mode_num:
            case 0:  # bestaudio(mp3)
                self.crop_thumbnail_square()
                self.marge_file_thumbnail_mp3()
            case 1:  # bestaudio(opus)
                self.crop_thumbnail_square()
                self.marge_file_thumbnail_opus()
            case 2:  # 720p,mp4(h264,mp4a)
                self.marge_file_thumbnail_mp4()
            case 3:  # bestvideo(mp4(h264,mp4a))
                self.marge_file_thumbnail_mp4()
            case 4:  # bestvideo(mp4(vp9,opus))
                self.marge_file_thumbnail_mp4()
        if exist(self.final_file_path):
            print("all process Done")
        else:
            raise ValueError("Failed.")
