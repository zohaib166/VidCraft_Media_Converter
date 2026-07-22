"""
main.py
Application Entry Point.
"""

import tkinter as tk
from tkinter import messagebox
from gui import FFmpegAppGUI
import installer_utils


def main():
    # Verify FFmpeg presence before launching full UI
    if not installer_utils.ensure_ffmpeg_installed():
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Dependency Error",
            "FFmpeg executable was not found and winget auto-installation failed.\n"
            "Please ensure FFmpeg is installed or bundled with the application."
        )
        return

    root = tk.Tk()
    _app = FFmpegAppGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()