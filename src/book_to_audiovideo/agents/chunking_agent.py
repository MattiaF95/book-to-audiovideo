from __future__ import annotations

from book_to_audiovideo.agents.base import BaseAgent
from book_to_audiovideo.pipeline.context import PipelineContext
from book_to_audiovideo.services.text_service import TextService


class ChunkingAgent(BaseAgent):
    stage_name = "chunking"

    def __init__(self, text_service: TextService) -> None:
        self.text_service = text_service

    async def execute(self, context: PipelineContext) -> None:
        if self._has_valid_cached_chunks(context):
            return
        context.state.chunks = self.text_service.split_into_chunks(context.state.cleaned_text)
        self.write_stage_json(
            context,
            "03_chunks.json",
            {"chunks": [chunk.model_dump(mode="json") for chunk in context.state.chunks]},
        )

    @staticmethod
    def _has_valid_cached_chunks(context: PipelineContext) -> bool:
        if not context.state.chunks:
            return False
        reconstructed = "\n\n".join(chunk.text.strip() for chunk in context.state.chunks if chunk.text.strip())
        return reconstructed == context.state.cleaned_text.strip()
