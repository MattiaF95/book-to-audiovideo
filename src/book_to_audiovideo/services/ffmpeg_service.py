from __future__ import annotations

import json
import subprocess
from pathlib import Path

from book_to_audiovideo.config import Settings
from book_to_audiovideo.pipeline.errors import PipelineError


class FFmpegService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def _run(self, command: list[str]) -> list[str]:
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            raise PipelineError(f"FFmpeg fallito: {' '.join(command)}\n{result.stderr}")
        return command

    def mix_audio_tracks(
        self,
        voice_path: Path,
        sfx_path: Path | None,
        output_path: Path,
        duration_seconds: float,
    ) -> dict[str, object]:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if sfx_path:
            filter_complex = (
                "[1:a]volume=0.18,aloop=loop=-1:size=2e+09,atrim=duration="
                f"{duration_seconds}[sfx];"
                "[0:a][sfx]amix=inputs=2:duration=first,loudnorm=I=-16:LRA=11:TP=-1.5[aout]"
            )
            command = [
                self.settings.ffmpeg_bin,
                "-y",
                "-i",
                str(voice_path),
                "-i",
                str(sfx_path),
                "-filter_complex",
                filter_complex,
                "-map",
                "[aout]",
                str(output_path),
            ]
        else:
            command = [
                self.settings.ffmpeg_bin,
                "-y",
                "-i",
                str(voice_path),
                "-af",
                "loudnorm=I=-16:LRA=11:TP=-1.5",
                str(output_path),
            ]
        return {"command": self._run(command), "duration_seconds": duration_seconds}

    def compose_video(self, video_path: Path, audio_path: Path, output_path: Path) -> dict[str, object]:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        command = [
            self.settings.ffmpeg_bin,
            "-y",
            "-stream_loop",
            "-1",
            "-i",
            str(video_path),
            "-i",
            str(audio_path),
            "-shortest",
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "libx264",
            "-c:a",
            "aac",
            "-pix_fmt",
            "yuv420p",
            str(output_path),
        ]
        return {"command": self._run(command)}

    def verify_duration(self, media_path: Path) -> float:
        command = [
            self.settings.ffprobe_bin,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            str(media_path),
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            raise PipelineError(f"ffprobe fallito: {result.stderr}")
        return float(json.loads(result.stdout)["format"]["duration"])

    def measure_loudness(self, media_path: Path) -> dict[str, float]:
        command = [
            self.settings.ffmpeg_bin,
            "-i",
            str(media_path),
            "-af",
            "loudnorm=print_format=json",
            "-f",
            "null",
            "-",
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            raise PipelineError(f"Misura loudness fallita: {result.stderr}")
        marker = "{\n\t\"input_i\""
        start = result.stderr.find(marker)
        if start == -1:
            return {}
        return json.loads(result.stderr[start:])
