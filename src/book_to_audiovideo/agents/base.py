from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from book_to_audiovideo.models.manifest import build_manifest
from book_to_audiovideo.pipeline.context import PipelineContext
from book_to_audiovideo.utils.json_utils import write_json


class BaseAgent(ABC):
    stage_name: str

    async def run(self, context: PipelineContext) -> None:
        context.state.current_stage = self.stage_name
        await self.execute(context)
        self.write_stage_manifest(context)

    @abstractmethod
    async def execute(self, context: PipelineContext) -> None:
        raise NotImplementedError

    def write_stage_json(self, context: PipelineContext, file_name: str, payload: dict) -> None:
        write_json(Path(context.state.artifact_dir) / file_name, payload)

    def write_stage_manifest(self, context: PipelineContext) -> None:
        path = Path(context.state.artifact_dir) / "manifests" / f"{self.stage_name}.json"
        write_json(path, build_manifest(context.state).model_dump(mode="json"))
