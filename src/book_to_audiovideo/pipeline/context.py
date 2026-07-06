from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from book_to_audiovideo.config import Settings
from book_to_audiovideo.models.state import PipelineState


@dataclass(slots=True)
class PipelineContext:
    settings: Settings
    state: PipelineState

    @property
    def artifact_dir(self) -> Path:
        return Path(self.state.artifact_dir)
