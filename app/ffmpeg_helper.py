import os
import platform
import shutil
import subprocess
import tarfile
import zipfile
from urllib.request import urlopen
from io import BytesIO

FFMPEG_DIR = "ffmpeg_bin"


def get_ffmpeg_exec():
    """Return local path to ffmpeg executable if exists, else None."""
    system = platform.system()
    if system == "Windows":
        ffmpeg_path = os.path.join(FFMPEG_DIR, "ffmpeg.exe")
    else:
        ffmpeg_path = os.path.join(FFMPEG_DIR, "ffmpeg")
    return ffmpeg_path if os.path.isfile(ffmpeg_path) else None


def is_ffmpeg_available():
    """Check if ffmpeg is available either locally or in system PATH."""
    if get_ffmpeg_exec():
        return True

    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        return True
    except Exception:
        return False


def download_ffmpeg():
    """Download and extract static ffmpeg binaries to local folder."""
    system = platform.system()
    arch = platform.machine()

    print(f"🔽 Downloading FFmpeg for {system} {arch}...")

    if system == "Windows":
        url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    elif system == "Darwin":
        url = "https://evermeet.cx/ffmpeg/getrelease/zip"
    elif system == "Linux":
        url = "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"
    else:
        raise RuntimeError("Unsupported OS for automatic FFmpeg download")

    os.makedirs(FFMPEG_DIR, exist_ok=True)

    try:
        with urlopen(url) as response:
            data = response.read()

        print("📦 Extracting FFmpeg...")

        if system == "Windows":
            with zipfile.ZipFile(BytesIO(data)) as z:
                ffmpeg_files = [f for f in z.namelist() if "ffmpeg.exe" in f]
                if not ffmpeg_files:
                    raise RuntimeError("FFmpeg executable not found in archive.")

                ffmpeg_file = ffmpeg_files[0]
                with z.open(ffmpeg_file) as src, open(
                    os.path.join(FFMPEG_DIR, "ffmpeg.exe"), "wb"
                ) as dst:
                    shutil.copyfileobj(src, dst)

        elif system == "Darwin":
            with zipfile.ZipFile(BytesIO(data)) as z:
                ffmpeg_files = [f for f in z.namelist() if f.endswith("/ffmpeg")]
                if not ffmpeg_files:
                    raise RuntimeError("FFmpeg binary not found in zip.")
                ffmpeg_file = ffmpeg_files[0]
                with z.open(ffmpeg_file) as src, open(
                    os.path.join(FFMPEG_DIR, "ffmpeg"), "wb"
                ) as dst:
                    shutil.copyfileobj(src, dst)

        elif system == "Linux":
            temp_extract = os.path.join(FFMPEG_DIR, "temp_extract")
            with tarfile.open(fileobj=BytesIO(data), mode="r:xz") as tar:
                members = [m for m in tar.getmembers() if m.name.endswith("/ffmpeg")]
                if not members:
                    raise RuntimeError("FFmpeg binary not found in tar.xz")
                os.makedirs(temp_extract, exist_ok=True)
                tar.extract(members[0], path=temp_extract)

                # Move to root
                src_path = os.path.join(temp_extract, members[0].name)
                dst_path = os.path.join(FFMPEG_DIR, "ffmpeg")
                shutil.move(src_path, dst_path)
                shutil.rmtree(temp_extract)

        if system != "Windows":
            os.chmod(os.path.join(FFMPEG_DIR, "ffmpeg"), 0o755)

        print("✅ FFmpeg downloaded and ready!")

    except Exception as e:
        print(f"[ERROR] FFmpeg download failed: {e}")
        raise


def ensure_ffmpeg():
    """Ensure FFmpeg is available, download if missing."""
    if is_ffmpeg_available():
        return get_ffmpeg_exec() or "ffmpeg"
    else:
        print("⚠️ FFmpeg not found, attempting download...")
        download_ffmpeg()
        return get_ffmpeg_exec()


def get_ffmpeg_path():
    """Return the absolute FFmpeg path for yt-dlp usage."""
    return ensure_ffmpeg()
