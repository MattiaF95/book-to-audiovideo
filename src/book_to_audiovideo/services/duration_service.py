from __future__ import annotations

import json
import subprocess
from pathlib import Path

from book_to_audiovideo.config import Settings
from book_to_audiovideo.pipeline.errors import PipelineError


class DurationService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def get_duration(self, path: Path) -> float:
        command = [
            self.settings.ffprobe_bin,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            str(path),
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            raise PipelineError(f"ffprobe fallito su {path}: {result.stderr}")
        payload = json.loads(result.stdout)
        return float(payload["format"]["duration"])
