import os
import yt_dlp

from ffmpeg_helper import get_ffmpeg_path

from enums import DownloadType, DownloadStatus


ffmpeg_path = get_ffmpeg_path()
os.environ["PATH"] = (
    os.path.abspath(os.path.dirname(ffmpeg_path)) + os.pathsep + os.environ["PATH"]
)


class PathInitializer:
    def __init__(self):
        """Initialize paths for the downloader."""
        self.root_path = "downloads"
        self.musics_path = f"{self.root_path}/musics"
        self.videos_path = f"{self.root_path}/videos"
        self.create_path()

    def create_path(self):
        """Create the app-related necessary directories if they do not exist."""
        os.makedirs(self.musics_path, exist_ok=True)
        os.makedirs(self.videos_path, exist_ok=True)

    def get_output_path(self, download_type: DownloadType):
        """Get the output path based on the download type."""
        if download_type == DownloadType.AUDIO:
            return self.musics_path
        elif download_type == DownloadType.VIDEO:
            return self.videos_path
        else:
            raise ValueError("Invalid download type specified.")


class YdlOpt:
    """Class to defibe yt-dlp options."""

    def __init__(self):
        """Initialize the YdlOpt class."""
        self.audio_ydl_opts = self.get_audio_ydl_opts()
        self.video_ydl_opts = self.get_video_ydl_opts()

    def get_audio_ydl_opts(self):
        """Get the yt-dlp options for audio download."""
        return {
            "format": "bestaudio/best",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
        }

    def get_video_ydl_opts(self):
        """Get the yt-dlp options for video download."""
        return {
            "format": "bestvideo+bestaudio/best",
            "merge_output_format": "mp4",
            "postprocessors": [],
        }


class YouTubeDownloader(PathInitializer, YdlOpt):
    def __init__(
        self,
        url,
        download_type: DownloadType = DownloadType.AUDIO,
        progress_callback=None,
    ):
        PathInitializer.__init__(self)
        YdlOpt.__init__(self)

        # Initialize attributes
        self.url: str = url
        self.download_type: str = download_type
        self.output_dir: str = self.get_output_path(self.download_type)
        self.progress_callback = progress_callback
        self.ydl_opts = self.get_ydl_opts()
        self.download_status: str = DownloadStatus.NOT_STARTED.value

    def get_ydl_opts(self):
        """Get the yt-dlp options based on the download type."""
        output_path = os.path.join(self.output_dir, "%(title)s.%(ext)s")
        ydl_opts = (
            self.audio_ydl_opts
            if self.download_type == DownloadType.AUDIO
            else self.video_ydl_opts
        )
        ydl_opts.update(
            {
                "outtmpl": output_path,
                "quiet": False,
                "noplaylist": True,
                "no_warnings": True,
            }
        )

        # Add progress hook if callback is provided
        if self.progress_callback:
            ydl_opts["progress_hooks"] = [self.progress_callback]

        return ydl_opts

    def download(self):
        """Download the YouTube content based on the specified type."""
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                self.download_status = DownloadStatus.IN_PROGRESS.value
                info_dict = ydl.extract_info(self.url, download=True)
                self.download_status = DownloadStatus.COMPLETED.value
                return (
                    f"{info_dict['title']}.mp3"
                    if self.download_type == DownloadType.AUDIO
                    else f"{info_dict['title']}.mp4"
                )
        except yt_dlp.utils.DownloadError as e:
            self.download_status = DownloadStatus.FAILED.value
            raise Exception(f"Download failed: {e}")
        except Exception as e:
            self.download_status = DownloadStatus.FAILED.value
            raise Exception("An unexpected error occurred during download.")
