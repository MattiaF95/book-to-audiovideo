from __future__ import annotations

from pathlib import Path

from book_to_audiovideo.agents.base import BaseAgent
from book_to_audiovideo.models.manifest import build_manifest
from book_to_audiovideo.pipeline.context import PipelineContext
from book_to_audiovideo.utils.json_utils import write_json


class ManifestAgent(BaseAgent):
    stage_name = "manifest"

    async def execute(self, context: PipelineContext) -> None:
        manifest = build_manifest(context.state)
        path = Path(context.state.artifact_dir) / "manifest.json"
        write_json(path, manifest.model_dump(mode="json"))
        context.state.manifest_path = str(path)
