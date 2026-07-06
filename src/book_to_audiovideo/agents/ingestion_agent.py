from __future__ import annotations

from pathlib import Path

from book_to_audiovideo.agents.base import BaseAgent
from book_to_audiovideo.pipeline.context import PipelineContext
from book_to_audiovideo.services.file_service import FileService
from book_to_audiovideo.services.text_service import TextService


class IngestionAgent(BaseAgent):
    stage_name = "ingestion"

    def __init__(self, file_service: FileService, text_service: TextService) -> None:
        self.file_service = file_service
        self.text_service = text_service

    async def execute(self, context: PipelineContext) -> None:
        if context.state.raw_text:
            return
        text = self.file_service.read_text(Path(context.state.source_path))
        context.state.raw_text = self.text_service.normalize_text(text)
        self.write_stage_json(
            context,
            "01_ingestion.json",
            {"source_path": context.state.source_path, "text_preview": context.state.raw_text[:2000]},
        )
