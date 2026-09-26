"""FFmpeg Streaming Pipe Manager & Process Safety Handler (Zero-Disk Intermediary)."""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
from typing import Sequence


DEFAULT_FFMPEG_CANDIDATES = [
    Path("C:/Users/AXION/AppData/Local/Programs/Shotcut/ffmpeg.exe"),
    Path("C:/Program Files/Shotcut/ffmpeg.exe"),
    Path("C:/ffmpeg/bin/ffmpeg.exe"),
]


def find_ffmpeg_binary() -> Path:
    """Locate functional ffmpeg executable from PATH or standard locations."""
    system_which = shutil.which("ffmpeg")
    if system_which:
        return Path(system_which)
    for cand in DEFAULT_FFMPEG_CANDIDATES:
        if cand.is_file():
            return cand
    raise FileNotFoundError("FFmpeg executable not found in PATH or standard directories.")


class FFmpegStreamer:
    """
    Spawns and manages an active FFmpeg pipe for zero-disk frame ingestion.
    Writes raw RGB24 frames to pipe:0 while concurrently muxing an audio track.
    """

    def __init__(
        self,
        output_video: str | Path,
        audio_path: str | Path,
        width: int = 1080,
        height: int = 1920,
        fps: int = 30,
        ffmpeg_bin: str | Path | None = None,
        crf: int = 17,
        preset: str = "medium"
    ):
        self.output_video = Path(output_video)
        self.output_video.parent.mkdir(parents=True, exist_ok=True)
        self.audio_path = Path(audio_path)
        self.width = int(width)
        self.height = int(height)
        self.fps = int(fps)
        self.ffmpeg_bin = Path(ffmpeg_bin) if ffmpeg_bin else find_ffmpeg_binary()
        self.proc: subprocess.Popen | None = None

        self.command = [
            str(self.ffmpeg_bin),
            "-hide_banner",
            "-loglevel", "warning",
            "-nostdin",
            "-y",
            "-f", "rawvideo",
            "-pixel_format", "rgb24",
            "-video_size", f"{self.width}x{self.height}",
            "-framerate", str(self.fps),
            "-i", "pipe:0",
            "-i", str(self.audio_path),
            "-vf", "vflip",
            "-c:v", "libx264",
            "-preset", preset,
            "-crf", str(crf),
            "-threads", "3",
            "-pix_fmt", "yuv420p",
            "-color_primaries", "bt709",
            "-color_trc", "bt709",
            "-colorspace", "bt709",
            "-c:a", "aac",
            "-b:a", "192k",
            "-movflags", "+faststart",
            "-shortest",
            str(self.output_video)
        ]

    def __enter__(self) -> FFmpegStreamer:
        flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        self.proc = subprocess.Popen(
            self.command,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            creationflags=flags
        )
        return self

    def write_frame(self, raw_bytes: bytes) -> None:
        """Stream a single raw RGB24 frame directly to FFmpeg stdin."""
        if not self.proc or not self.proc.stdin:
            raise RuntimeError("FFmpeg process is not running or stdin is closed.")
        self.proc.stdin.write(raw_bytes)

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if not self.proc:
            return

        if self.proc.stdin and not self.proc.stdin.closed:
            self.proc.stdin.close()

        try:
            exit_code = self.proc.wait(timeout=120)
            if exit_code != 0 and exc_type is None:
                err_log = self.proc.stderr.read().decode("utf-8", errors="replace") if self.proc.stderr else ""
                raise RuntimeError(f"FFmpeg failed with exit code {exit_code}: {err_log}")
        except subprocess.TimeoutExpired:
            self.proc.terminate()
            self.proc.wait(timeout=10)
            raise
