import os
import platform
import subprocess
import tkinter as tk

from tkinter import messagebox, ttk

from ffmpeg_helper import ensure_ffmpeg

from downloader import YouTubeDownloader, PathInitializer

from enums import DownloadType


class YouTubeDownloaderApp(PathInitializer):
    def __init__(self, root):
        """Initialize the YouTube Downloader GUI application."""
        super().__init__()

        # Root window setup
        self.root = root
        self.root.title("YouTube Downloader")
        self.root.geometry("950x500")

        # Variables
        self.download_format = tk.StringVar(value=DownloadType.AUDIO.value)
        self.progress_var = tk.StringVar()

        # Initialize GUI and populate file list
        self.setup_ui()
        self.refresh_lists()

    def setup_ui(self):
        """Set up the layout and widgets of the GUI."""
        # Left Panel for URL input and controls
        left_frame = tk.Frame(self.root)
        left_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        # Label for URL input
        tk.Label(left_frame, text="Enter YouTube Video URL:", font=("Arial", 10)).grid(
            row=0, column=0, sticky="w", pady=(0, 5)
        )

        # URL Entry Frame (holds Text box and erase button side-by-side)
        url_frame = tk.Frame(left_frame)
        url_frame.grid(row=1, column=0, pady=(0, 10), sticky="w")

        # URL Text Box (pack first, left side)
        self.url_entry = tk.Text(url_frame, width=55, height=2, font=("Arial", 10))
        self.url_entry.pack(side="left")

        # Erase Button (small, red, right side)
        erase_button = tk.Button(
            url_frame,
            text="✕",
            command=self.clear_url,
            width=2,
            height=1,
            fg="white",
            bg="red",
            font=("Arial", 10, "bold"),
            relief="flat",
            bd=0,
            activebackground="#cc0000",
            cursor="hand2",
        )
        erase_button.pack(side="left", padx=(5, 0), pady=(10, 10))

        # Radio Buttons for download format selection
        radio_frame = tk.Frame(left_frame)
        radio_frame.grid(column=0, pady=(0, 10))
        radio_frame.grid_columnconfigure(0, weight=1)

        tk.Radiobutton(
            radio_frame,
            text="Audio (MP3)",
            variable=self.download_format,
            value=DownloadType.AUDIO.value,
            command=self.update_download_type,
        ).pack(side="left", padx=10)

        tk.Radiobutton(
            radio_frame,
            text="Video (MP4)",
            variable=self.download_format,
            value=DownloadType.VIDEO.value,
            command=self.update_download_type,
        ).pack(side="left")

        # Download Button
        self.download_button = tk.Button(
            left_frame, text="Download Audio", command=self.start_download, width=30
        )
        self.download_button.grid(row=3, column=0, pady=(0, 10))

        # Progress Label (hidden by default)
        self.progress_label = tk.Label(
            left_frame, textvariable=self.progress_var, fg="blue", font=("Arial", 9)
        )

        # Progress Bar (hidden by default)
        self.progress_bar = ttk.Progressbar(
            left_frame, orient="horizontal", length=400, mode="determinate"
        )

        # Right Panel for downloaded files
        right_frame = tk.Frame(self.root)
        right_frame.grid(row=0, column=1, padx=10, pady=20, sticky="nsew")

        # Music List
        tk.Label(right_frame, text="🎵 Musics", font=("Arial", 10, "bold")).pack(
            anchor="w"
        )
        self.music_listbox = tk.Listbox(
            right_frame, width=40, height=10, font=("Arial", 10)
        )
        self.music_listbox.pack(fill="x", pady=(0, 10))
        self.music_listbox.bind(
            "<Double-Button-1>", lambda event: self.on_file_click(event, "music")
        )

        # Video List
        tk.Label(right_frame, text="🎬 Videos", font=("Arial", 10, "bold")).pack(
            anchor="w"
        )
        self.video_listbox = tk.Listbox(
            right_frame, width=40, height=10, font=("Arial", 10)
        )
        self.video_listbox.pack(fill="x")
        self.video_listbox.bind(
            "<Double-Button-1>", lambda event: self.on_file_click(event, "video")
        )

        # Configure layout resizing behavior
        self.root.columnconfigure(0, weight=3)
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)

    def update_download_type(self):
        """Update the button label based on selected download type."""
        btn_label = (
            "Download Audio"
            if self.download_format.get() == "audio"
            else "Download Video"
        )
        self.download_button.config(text=btn_label)

    def ydl_progress_hook(self, d):
        """Callback function to update the progress bar during download."""
        if d["status"] == "downloading":
            total_bytes = d.get("total_bytes") or d.get("total_bytes_estimate")
            downloaded = d.get("downloaded_bytes", 0)
            if total_bytes:
                percent = int(downloaded / total_bytes * 100)
                self.progress_bar["value"] = percent
                self.progress_var.set(f"⬇ Downloading... {percent}%")
                self.root.update_idletasks()
        elif d["status"] == "finished":
            self.progress_var.set("✅ Finished")
            self.progress_bar["value"] = 100

    def start_download(self):
        """Start downloading the media based on the input URL and format."""
        url = self.url_entry.get("1.0", tk.END).strip()
        if not url:
            messagebox.showwarning(
                "Input Required", "Please enter a YouTube Video URL."
            )
            return

        # Disable button and show progress
        self.download_button.config(state="disabled")
        self.progress_label.grid(row=4, column=0, sticky="w")
        self.progress_bar.grid(row=5, column=0, pady=(10, 0))
        self.progress_bar["value"] = 0
        self.progress_var.set("🔄 Downloading...")
        self.root.update()

        try:
            # Determine download type
            dtype = (
                DownloadType.AUDIO
                if self.download_format.get() == "audio"
                else DownloadType.VIDEO
            )

            # Create downloader and start download
            downloader = YouTubeDownloader(
                url, download_type=dtype, progress_callback=self.ydl_progress_hook
            )
            filename = downloader.download()

            # Update status and UI
            self.progress_var.set("✅ Finished")
            self.refresh_lists()
            messagebox.showinfo("Success", f"Downloaded: {filename}")

        except Exception as e:
            print(f"Error during download: {e}")
            self.progress_var.set("❌ Failed")
            messagebox.showerror("Error", str(e))

        finally:
            self.download_button.config(state="normal")

    def refresh_lists(self):
        """Refresh the list of downloaded music and video files."""
        self.music_listbox.delete(0, tk.END)
        self.video_listbox.delete(0, tk.END)

        # Load music files
        if os.path.exists(self.musics_path):
            musics = sorted(
                [
                    f
                    for f in os.listdir(self.musics_path)
                    if os.path.isfile(os.path.join(self.musics_path, f))
                ]
            )
            for idx, file in enumerate(musics, 1):
                self.music_listbox.insert(tk.END, f"{idx}. {file}")

        # Load video files
        if os.path.exists(self.videos_path):
            videos = sorted(
                [
                    f
                    for f in os.listdir(self.videos_path)
                    if os.path.isfile(os.path.join(self.videos_path, f))
                ]
            )
            for idx, file in enumerate(videos, 1):
                self.video_listbox.insert(tk.END, f"{idx}. {file}")

    def on_file_click(self, event, list_type):
        """Open the selected file when double-clicked."""
        listbox = self.music_listbox if list_type == "music" else self.video_listbox
        folder = self.musics_path if list_type == "music" else self.videos_path

        selection = listbox.curselection()
        if not selection:
            return

        # Extract filename and open it
        item_text = listbox.get(selection[0])
        filename = item_text.split(". ", 1)[1]
        file_path = os.path.join(folder, filename)

        try:
            if platform.system() == "Windows":
                os.startfile(file_path)
            elif platform.system() == "Darwin":
                subprocess.run(["open", file_path])
            else:
                subprocess.run(["xdg-open", file_path])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file: {e}")

    def clear_url(self):
        """Clear the URL text entry box."""
        self.url_entry.delete("1.0", tk.END)


# Entry point
if __name__ == "__main__":
    ensure_ffmpeg() # Ensure FFmpeg is available
    root = tk.Tk()
    app = YouTubeDownloaderApp(root)
    root.mainloop()
