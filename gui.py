"""
gui.py
Frontend module for VidCraft Media Converter.
Provides a clean, user-friendly UI that translates plain-English settings
into exact FFmpeg parameters without losing any technical options.
"""

import os
import sys
import ctypes
import threading
import tkinter as tk
from tkinter import PhotoImage, filedialog, messagebox, ttk

import ffmpeg_utils

# ==============================================================================
# TRANSLATION DICTIONARIES
# Maps user-friendly dropdown descriptions to exact FFmpeg backend strings.
# ==============================================================================

VCODEC_MAP = {
    "H.265 / HEVC (High Efficiency)": "libx265",
    "H.264 / AVC (Universal MP4)": "libx264",
    "VP9 (Web Video / WebM)": "libvpx-vp9",
    "Copy Original (No Re-encoding)": "copy",
    "Disable Video Track": "none",
}

PRESET_MAP = {
    "Ultrafast (Fastest Export / Larger File)": "ultrafast",
    "Superfast": "superfast",
    "Veryfast": "veryfast",
    "Faster": "faster",
    "Fast": "fast",
    "Medium (Balanced)": "medium",
    "Slow (Better Quality & Compression)": "slow",
    "Slower": "slower",
    "Veryslow (Smallest File / Longest Time)": "veryslow",
}

ACODEC_MAP = {
    "AAC Audio (Standard MP4)": "aac",
    "MP3 Audio": "libmp3lame",
    "Opus Audio (Web Audio)": "libopus",
    "Copy Original (No Re-encoding)": "copy",
    "Disable Audio (Mute)": "an",
}

ABITRATE_MAP = {
    "96 kbps (Low Quality)": "96k",
    "128 kbps (Standard)": "128k",
    "160 kbps (Good Quality)": "160k",
    "192 kbps (High Quality)": "192k",
    "256 kbps (Very High Quality)": "256k",
    "320 kbps (Maximum Quality)": "320k",
}

# 1. Tell Windows to group this under a custom process ID (Fixes Taskbar icon)
try:
    myappid = "vidcraft.mediaconverter.app.1.0"
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except Exception:
    pass

# --- RESOURCE PATH HELPER ---
def get_resource_path(relative_path: str) -> str:
    if getattr(sys, "frozen", False):
        base_path = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, relative_path)


class FFmpegAppGUI:

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("VidCraft Media Converter")
        self.root.geometry("640x750")
        self.root.resizable(False, False)
        
        icon_path = get_resource_path("app_icon.ico")
        if os.path.exists(icon_path):
            try:
                # Use iconphoto with a PhotoImage for guaranteed rendering
                self.app_icon = tk.PhotoImage(file=get_resource_path("logo.png"))
                self.root.iconphoto(True, self.app_icon)
            except Exception:
                # Fallback to bitmap
                try:
                    self.root.iconbitmap(icon_path)
                except Exception:
                    pass

        logo_path = get_resource_path("logo.png")
        if os.path.exists(logo_path):
            try:
                self.logo_img = tk.PhotoImage(file=logo_path)
                logo_label = tk.Label(self.root, image=self.logo_img)
                logo_label.pack(pady=(10, 0))
            except Exception as e:
                print(f"[DEBUG] Could not load logo image: {e}")

        # Window Icon
        if os.path.exists("app_icon.ico"):
            try:
                self.root.iconbitmap("app_icon.ico")
            except Exception:
                pass

        self.input_file = tk.StringVar()
        self.output_file = tk.StringVar()
        self.total_duration = None
        self.process_holder = {}

        self._build_ui()

    def _build_ui(self):
        # App Title
        tk.Label(
            self.root,
            text="VidCraft Media Converter",
            font=("Segoe UI", 18, "bold"),
        ).pack(pady=(0, 10))

        # --- Section 1: File Selection ---
        file_frame = tk.LabelFrame(
            self.root, text=" File Selection ", font=("Helvetica", 10, "bold")
        )
        file_frame.pack(fill="x", padx=15, pady=5)

        tk.Label(file_frame, text="Select Source Video:").grid(
            row=0, column=0, sticky="w", padx=5, pady=5
        )
        tk.Entry(
            file_frame, textvariable=self.input_file, width=42, state="readonly"
        ).grid(row=0, column=1, padx=5, pady=5)
        tk.Button(
            file_frame, text="Browse...", command=self.browse_input
        ).grid(row=0, column=2, padx=5, pady=5)

        tk.Label(file_frame, text="Save Output Video To:").grid(
            row=1, column=0, sticky="w", padx=5, pady=5
        )
        tk.Entry(file_frame, textvariable=self.output_file, width=42).grid(
            row=1, column=1, padx=5, pady=5
        )
        tk.Button(
            file_frame, text="Save As...", command=self.browse_output
        ).grid(row=1, column=2, padx=5, pady=5)

        # --- Section 2: Video Options ---
        video_frame = tk.LabelFrame(
            self.root,
            text=" Video Quality & Format Settings ",
            font=("Helvetica", 10, "bold"),
        )
        video_frame.pack(fill="x", padx=15, pady=5)

        # Video Codec Dropdown
        tk.Label(video_frame, text="Video Format (Codec):").grid(
            row=0, column=0, sticky="w", padx=5, pady=5
        )
        self.vcodec_var = tk.StringVar(value="H.265 / HEVC (High Efficiency)")
        vcodec_cb = ttk.Combobox(
            video_frame,
            textvariable=self.vcodec_var,
            values=list(VCODEC_MAP.keys()),
            state="readonly",
            width=36,
        )
        vcodec_cb.grid(row=0, column=1, columnspan=2, sticky="w", padx=5, pady=5)

        # Encoding Speed Dropdown
        tk.Label(video_frame, text="Encoding Speed:").grid(
            row=1, column=0, sticky="w", padx=5, pady=5
        )
        self.preset_var = tk.StringVar(value="Slow (Better Quality & Compression)")
        preset_cb = ttk.Combobox(
            video_frame,
            textvariable=self.preset_var,
            values=list(PRESET_MAP.keys()),
            state="readonly",
            width=36,
        )
        preset_cb.grid(row=1, column=1, columnspan=2, sticky="w", padx=5, pady=5)

        # Visual Quality Slider
        tk.Label(video_frame, text="Visual Quality Level:").grid(
            row=2, column=0, sticky="w", padx=5, pady=5
        )
        self.crf_var = tk.IntVar(value=24)
        crf_scale = tk.Scale(
            video_frame,
            from_=0,
            to=51,
            orient="horizontal",
            variable=self.crf_var,
        )
        crf_scale.grid(row=2, column=1, sticky="we", padx=5, pady=5)
        tk.Label(
            video_frame,
            text="(0 = Best Quality, 51 = Smallest Size)",
            fg="gray",
            font=("Helvetica", 8),
        ).grid(row=2, column=2, sticky="w")

        # --- Section 3: Audio Options ---
        audio_frame = tk.LabelFrame(
            self.root,
            text=" Audio Format & Bitrate ",
            font=("Helvetica", 10, "bold"),
        )
        audio_frame.pack(fill="x", padx=15, pady=5)

        # Audio Format Dropdown
        tk.Label(audio_frame, text="Audio Format:").grid(
            row=0, column=0, sticky="w", padx=5, pady=5
        )
        self.acodec_var = tk.StringVar(value="AAC Audio (Standard MP4)")
        acodec_cb = ttk.Combobox(
            audio_frame,
            textvariable=self.acodec_var,
            values=list(ACODEC_MAP.keys()),
            state="readonly",
            width=36,
        )
        acodec_cb.grid(row=0, column=1, columnspan=2, sticky="w", padx=5, pady=5)

        # Audio Bitrate Dropdown
        tk.Label(audio_frame, text="Audio Quality (Bitrate):").grid(
            row=1, column=0, sticky="w", padx=5, pady=5
        )
        self.abitrate_var = tk.StringVar(value="160 kbps (Good Quality)")
        abitrate_cb = ttk.Combobox(
            audio_frame,
            textvariable=self.abitrate_var,
            values=list(ABITRATE_MAP.keys()),
            state="readonly",
            width=36,
        )
        abitrate_cb.grid(row=1, column=1, columnspan=2, sticky="w", padx=5, pady=5)

        # --- Section 4: Progress Frame ---
        progress_frame = tk.LabelFrame(
            self.root, text=" Conversion Progress ", font=("Helvetica", 10, "bold")
        )
        progress_frame.pack(fill="x", padx=15, pady=5)

        self.progress_bar = ttk.Progressbar(
            progress_frame, orient="horizontal", mode="determinate"
        )
        self.progress_bar.pack(fill="x", padx=10, pady=5)

        self.lbl_progress_pct = tk.Label(
            progress_frame, text="0.0%", font=("Helvetica", 9, "bold")
        )
        self.lbl_progress_pct.pack()

        # Action Buttons
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)

        self.btn_convert = tk.Button(
            btn_frame,
            text="Start Encoding",
            bg="#4CAF50",
            fg="white",
            font=("Helvetica", 11, "bold"),
            width=15,
            command=self.start_encoding,
        )
        self.btn_convert.grid(row=0, column=0, padx=10)

        self.btn_cancel = tk.Button(
            btn_frame,
            text="Cancel Encoding",
            bg="#f44336",
            fg="white",
            font=("Helvetica", 11, "bold"),
            width=15,
            state="disabled",
            command=self.cancel_encoding,
        )
        self.btn_cancel.grid(row=0, column=1, padx=10)

        self.lbl_status = tk.Label(
            self.root, text="Status: Ready", font=("Helvetica", 10)
        )
        self.lbl_status.pack()

    def browse_input(self):
        file_path = filedialog.askopenfilename(
            filetypes=[
                ("Video Files", "*.mp4 *.mkv *.avi *.mov *.webm"),
                ("All Files", "*.*"),
            ]
        )
        if file_path:
            self.input_file.set(file_path)
            if not self.output_file.get():
                base, _ = os.path.splitext(file_path)
                self.output_file.set(f"{base}_encoded.mp4")

            self.lbl_status.config(
                text="Status: Reading video duration...", fg="orange"
            )
            self.root.update_idletasks()

            self.total_duration = ffmpeg_utils.get_media_duration(file_path)
            self.lbl_status.config(text="Status: Ready", fg="gray")

    def browse_output(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".mp4",
            filetypes=[
                ("MP4 Video", "*.mp4"),
                ("MKV Video", "*.mkv"),
                ("All Files", "*.*"),
            ],
        )
        if file_path:
            self.output_file.set(file_path)

    def get_command_args(self):
        """
        Translates user-friendly UI selection strings back to standard FFmpeg parameters.
        """
        vcodec = VCODEC_MAP.get(self.vcodec_var.get(), "libx265")
        preset = PRESET_MAP.get(self.preset_var.get(), "slow")
        crf = self.crf_var.get()
        acodec = ACODEC_MAP.get(self.acodec_var.get(), "aac")
        abitrate = ABITRATE_MAP.get(self.abitrate_var.get(), "160k")

        return ffmpeg_utils.build_ffmpeg_command(
            input_file=self.input_file.get() or "input.mp4",
            output_file=self.output_file.get() or "output.mp4",
            vcodec=vcodec,
            preset=preset,
            crf=crf,
            acodec=acodec,
            abitrate=abitrate,
        )

    def update_progress_ui(self, percentage: float):
        self.root.after(0, lambda: self._apply_progress(percentage))

    def _apply_progress(self, percentage: float):
        self.progress_bar["value"] = percentage
        self.lbl_progress_pct.config(text=f"{percentage:.1f}%")

    def start_encoding(self):
        if not self.input_file.get():
            messagebox.showwarning(
                "Missing Input", "Please select a source video file first."
            )
            return

        self.btn_convert.config(state="disabled")
        self.btn_cancel.config(state="normal")
        self.lbl_status.config(text="Status: Encoding...", fg="blue")
        self.progress_bar["value"] = 0
        self.lbl_progress_pct.config(text="0.0%")

        self.process_holder = {"is_cancelled": False, "process": None}
        cmd = self.get_command_args()

        thread = threading.Thread(
            target=ffmpeg_utils.execute_ffmpeg_process,
            args=(
                cmd,
                self.total_duration,
                self.update_progress_ui,
                lambda: self.root.after(0, self.on_success),
                lambda err: self.root.after(0, lambda: self.on_error(err)),
                lambda: self.root.after(0, self.on_cancelled),
                self.process_holder,
            ),
            daemon=True,
        )
        thread.start()

    def cancel_encoding(self):
        """Triggers conversion cancellation."""
        if messagebox.askyesno(
            "Cancel Encoding",
            "Are you sure you want to stop the current conversion?",
        ):
            self.process_holder["is_cancelled"] = True
            proc = self.process_holder.get("process")
            if proc:
                try:
                    proc.terminate()
                except Exception:
                    pass
            self.lbl_status.config(text="Status: Cancelling...", fg="orange")

    def on_success(self):
        self.progress_bar["value"] = 100
        self.lbl_progress_pct.config(text="100.0%")
        self.lbl_status.config(text="Status: Complete!", fg="green")
        self.btn_convert.config(state="normal")
        self.btn_cancel.config(state="disabled")
        messagebox.showinfo(
            "Success", "Video encoding completed successfully!"
        )

    def on_cancelled(self):
        self.lbl_status.config(
            text="Status: Conversion Cancelled", fg="orange"
        )
        self.btn_convert.config(state="normal")
        self.btn_cancel.config(state="disabled")
        messagebox.showwarning(
            "Cancelled", "Video conversion was cancelled by user."
        )

    def on_error(self, err_msg: str):
        self.lbl_status.config(text="Status: Encoding Failed!", fg="red")
        self.btn_convert.config(state="normal")
        self.btn_cancel.config(state="disabled")
        messagebox.showerror(
            "FFmpeg Error", f"An error occurred during encoding:\n\n{err_msg}"
        )