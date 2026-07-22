"""
ffmpeg_utils.py
Backend module for handling FFmpeg binary paths, command building,
duration probing, deadlock-free progress tracking, and optional cancellation.
"""

import os
import re
import subprocess
import sys


def get_ffmpeg_bin_path() -> str:
    """
    Returns the absolute path to the FFmpeg executable.
    Checks inside the bundled application directory first, then falls back to system PATH.
    """
    if getattr(sys, "frozen", False):
        base_path = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    bundled_ffmpeg = os.path.join(base_path, "ffmpeg.exe")
    if os.path.exists(bundled_ffmpeg):
        return bundled_ffmpeg
    return "ffmpeg"


def get_media_duration(input_path: str) -> float | None:
    """Probes media file duration using FFmpeg to calculate progress percentage."""
    if not os.path.exists(input_path):
        return None

    ffmpeg_bin = get_ffmpeg_bin_path()
    cmd = [ffmpeg_bin, "-i", input_path]
    creation_flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=creation_flags,
        )
        _, stderr = process.communicate()

        match = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", stderr)
        if match:
            hours, minutes, seconds = match.groups()
            return float(hours) * 3600 + float(minutes) * 60 + float(seconds)
    except Exception as exc:
        print(f"[DEBUG] Duration Probe Error: {exc}")

    return None


def build_ffmpeg_command(
    input_file: str,
    output_file: str,
    vcodec: str,
    preset: str,
    crf: int,
    acodec: str,
    abitrate: str,
) -> list[str]:
    """Constructs the CLI command list based on GUI choices."""
    ffmpeg_bin = get_ffmpeg_bin_path()
    cmd = [ffmpeg_bin, "-y", "-i", input_file, "-progress", "pipe:1", "-nostats"]

    # Video Settings
    if vcodec == "none":
        cmd.append("-vn")
    else:
        cmd.extend(["-c:v", vcodec])
        if vcodec != "copy":
            cmd.extend(["-crf", str(crf)])
            cmd.extend(["-preset", preset])

    # Audio Settings
    if acodec == "an (disable audio)":
        cmd.append("-an")
    else:
        cmd.extend(["-c:a", acodec])
        if acodec != "copy":
            cmd.extend(["-b:a", abitrate])

    cmd.append(output_file)
    return cmd


def execute_ffmpeg_process(
    cmd: list[str],
    total_duration: float | None,
    progress_callback,
    success_callback,
    error_callback,
    cancelled_callback=None,
    process_holder: dict | None = None,
):
    """
    Executes FFmpeg with unbuffered pipe reading and deadlock prevention.
    Supports process handle storage and cancellation without affecting progress logic.
    """
    try:
        # Fallback: calculate duration if not already available
        if (total_duration is None or total_duration <= 0) and "-i" in cmd:
            input_idx = cmd.index("-i") + 1
            if input_idx < len(cmd):
                total_duration = get_media_duration(cmd[input_idx])

        creation_flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0

        # Discard stderr to DEVNULL to avoid OS buffer deadlock on Windows
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            bufsize=1,
            universal_newlines=True,
            creationflags=creation_flags,
        )

        # Store process handle if dictionary was provided
        if process_holder is not None:
            process_holder["process"] = process

        while True:
            # Check for cancellation signal before reading next line
            if process_holder and process_holder.get("is_cancelled"):
                process.terminate()
                if cancelled_callback:
                    cancelled_callback()
                return

            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break

            line = line.strip()

            # 1. Primary check: Microseconds
            if line.startswith("out_time_us="):
                val = line.split("=")[1].strip()
                if val.isdigit():
                    elapsed = int(val) / 1_000_000.0
                    if total_duration and total_duration > 0:
                        progress_callback(min((elapsed / total_duration) * 100.0, 100.0))

            # 2. Secondary check: Milliseconds
            elif line.startswith("out_time_ms="):
                val = line.split("=")[1].strip()
                if val.isdigit():
                    elapsed = int(val) / 1_000.0
                    if total_duration and total_duration > 0:
                        progress_callback(min((elapsed / total_duration) * 100.0, 100.0))

            # 3. Fallback check: Formatted Timestamp (HH:MM:SS.ms)
            elif line.startswith("out_time="):
                val = line.split("=")[1].strip()
                match = re.search(r"(\d+):(\d+):(\d+(?:\.\d+)?)", val)
                if match:
                    h, m, s = match.groups()
                    elapsed = float(h) * 3600 + float(m) * 60 + float(s)
                    if total_duration and total_duration > 0:
                        progress_callback(min((elapsed / total_duration) * 100.0, 100.0))

        process.wait()

        # Final state check
        if process_holder and process_holder.get("is_cancelled"):
            if cancelled_callback:
                cancelled_callback()
        elif process.returncode == 0:
            success_callback()
        else:
            error_callback("FFmpeg processing failed with non-zero exit code.")

    except Exception as exc:
        if process_holder and process_holder.get("is_cancelled"):
            if cancelled_callback:
                cancelled_callback()
        else:
            error_callback(str(exc))