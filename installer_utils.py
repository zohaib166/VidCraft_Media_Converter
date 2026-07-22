"""
installer_utils.py
Utility script to verify and auto-install FFmpeg via winget if absent.
"""

import shutil
import subprocess


def is_ffmpeg_available() -> bool:
    """Checks if ffmpeg is accessible either bundled or in system PATH."""
    import ffmpeg_utils
    import os
    bin_path = ffmpeg_utils.get_ffmpeg_bin_path()
    if os.path.exists(bin_path):
        return True
    return shutil.which("ffmpeg") is not None


def ensure_ffmpeg_installed() -> bool:
    """Automates winget installation if FFmpeg is missing from host PC."""
    if is_ffmpeg_available():
        return True

    print("[INFO] FFmpeg not found. Attempting auto-installation via winget...")
    cmd = [
        "winget", "install",
        "--id", "Gyan.FFmpeg",
        "-e",
        "--accept-source-agreements",
        "--accept-package-agreements"
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False