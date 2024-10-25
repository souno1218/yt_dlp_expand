## https://qiita.com/soun1218/items/3f07fbaa7029208dd789

from mutagen.id3 import ID3
from mutagen.oggopus import OggOpus
from mutagen.flac import Picture
import os, ffmpeg, base64, pathlib, argparse, platform, subprocess


def main():
    parser = argparse.ArgumentParser()
    txt = "0:bestaudio(mp3),\n1:bestaudio(opus),\n2:720p,mp4(h264,mp4a),\n3:bestvideo(mp4(h264,mp4a)),\n4:bestvideo(mp4(vp9,opus))"
    parser.add_argument("DownloadMode", type=int, help=txt, choices=list(range(5)))
    parser.add_argument("url", type=str, help="url")
    parser.add_argument("-p", "--path", type=str, help="downloadMode dir path")
    args = parser.parse_args()
    Class_Yt_dlp = ExpandYt_dlp(args.DownloadMode, args.url, args.path)
    Class_Yt_dlp.main_func()


class ExpandYt_dlp:
    def __init__(self, DownloadMode, url, path=None):
        self.mode_num = DownloadMode
        self.download_url = url
        self.device_info()
        self.ext = {0: "mp3", 1: "opus", 2: "mp4", 3: "mp4", 4: "mp4"}[self.mode_num]
        if path is None:
            if self.is_pc:
                path = "~/Downloads"
            else:
                path = "~/Documents"
        self.output_path = pathlib.Path(path).expanduser()

    def device_info(self):
        os_name = platform.system()
        if not os_name in [
            "Darwin",
            "Linux",
            "Windows",
        ]:
            raise
        self.is_pc = True
        if os_name == "Darwin":
            device = platform.platform().split("-")[2]
            if ("iPhone" in device) or ("iPad" in device):
                self.is_pc = False

    def getTitle(self):
        script = f"yt-dlp '{self.download_url}' --skip-download --print 'title' --no-check-certificate --no-playlist --extractor-args youtube:lang=ja;player-client=web"
        cp = subprocess.run(script, encoding="utf-8", stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        # cp = subprocess.run(script, encoding='utf-8', stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True,capture_output=True,text=True)
        self.title = cp.stdout.replace("\n", "")
        replaceList = {":": "-", "[": "「", "]": "」", "/": "／", "\n": " ", "'": "’"}
        for key, value in replaceList.items():
            self.title = self.title.replace(key, value)
        print(f"getTitle Done : {self.title}")

    def download_thumbnail_jpg(self):
        self.thumbnail_path = f"{self.output_path}/{self.title}.jpg"
        script = (
            f"yt-dlp '{self.download_url}' --no-check-certificate  --no-playlist --skip-download "
            f"--write-thumbnail --convert-thumbnails jpg --output '{self.output_path}/{self.title}'"
        )  # 9/6 変更
        subprocess.run(script, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        print(f"download_thumbnail_jpg Done")

    def download_file(self):
        # 参考:https://vlike-vlife.netlify.app/posts/cli_yt-dl
        script = f"yt-dlp --no-check-certificate --no-playlist '{self.download_url}' "
        match self.mode_num:
            case 0:
                script += f"-o '{self.output_path}/{self.title}.%(ext)s' "
                script += "-f 'bestaudio' "
                script += "--extract-audio "
                script += "--audio-format mp3 "
                self.file_path = f"{self.output_path}/{self.title}.{self.ext}"
            case 1:
                script += f"-o '{self.output_path}/{self.title}.%(ext)s' "
                script += "-f 'bestaudio[acodec~=opus]' "
                script += "--extract-audio "
                self.file_path = f"{self.output_path}/{self.title}.{self.ext}"
            case 2:
                script += f"-o '{self.output_path}/{self.title}_before.%(ext)s' "
                script += "-f \"bestvideo*[height=720][fps<=30][vcodec~='^(avc|h264)']+bestaudio[acodec~=mp4a]\" "
                self.file_path = f"{self.output_path}/{self.title}_before.{self.ext}"
            case 3:
                script += f"-o '{self.output_path}/{self.title}_before.%(ext)s' "
                script += "-f \"bestvideo*[vcodec~='^(avc|h264)']+bestaudio[acodec~=mp4a]\" "
                self.file_path = f"{self.output_path}/{self.title}_before.{self.ext}"
            case 4:
                script += f"-o '{self.output_path}/{self.title}_before.%(ext)s' "
                script += "-f 'bestvideo+bestaudio/best' "
                script += "--merge-output-format mp4"
                self.file_path = f"{self.output_path}/{self.title}_before.{self.ext}"
        subprocess.run(script, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        print("UseYt_dlp_iphone Done")

    def marge_file_thumbnail_mp4(self):
        video = ffmpeg.input(self.file_path)
        cover = ffmpeg.input(self.thumbnail_path)  # 9/6 変更
        (
            ffmpeg.output(
                video,
                cover,
                f"{self.output_path}/{self.title}.mp4",
                c="copy",
                **{"c:v:1": "mjpeg"},
                **{"disposition:v:1": "attached_pic"},
            )
            .global_args("-map", "0")
            .global_args("-map", "1")
            .global_args("-loglevel", "error")
            .run(overwrite_output=True)
        )
        os.remove(self.thumbnail_path)
        os.remove(self.file_path)
        print("marge_file_thumbnail_mp4 Done")

    def crop_thumbnail_square(self):
        probe = ffmpeg.probe(self.thumbnail_path)
        width = min(probe["streams"][0]["width"], probe["streams"][0]["height"])
        ffmpeg.input(self.thumbnail_path).filter("crop", width, width).output(self.thumbnail_path).run(
            overwrite_output=True
        )
        print("crop_thumbnail_square Done")

    def marge_file_thumbnail_mp3(self):
        # 参考:https://qiita.com/moshi/items/0fd2cd8c394ffa927239
        tags = ID3(self.file_path)
        with open(self.thumbnail_path, "rb") as img_file:
            cover_img_byte_str = img_file.read()
            tags.mime = "image/jpeg"
            tags.type = 3
            tags.data = cover_img_byte_str
        tags.save()

        os.remove(self.thumbnail_path)
        print("marge_file_thumbnail_mp3 Done")

    def marge_file_thumbnail_opus(self):
        # 参考:https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/postprocessor/embedthumbnail.py
        pic = Picture()
        f = OggOpus(self.file_path)
        pic.mime = f"image/jpeg"
        with open(self.thumbnail_path, "rb") as thumbfile:
            pic.data = thumbfile.read()
        pic.type = 3  # front cover
        f["METADATA_BLOCK_PICTURE"] = base64.b64encode(pic.write()).decode("ascii")
        f.save()

        os.remove(self.thumbnail_path)
        print("marge_file_thumbnail_opus Done")

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
        print("all process Done")
