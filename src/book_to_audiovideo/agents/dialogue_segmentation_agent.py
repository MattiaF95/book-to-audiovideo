from __future__ import annotations

from book_to_audiovideo.agents.base import BaseAgent
from book_to_audiovideo.models.domain import Segment
from book_to_audiovideo.pipeline.context import PipelineContext
from book_to_audiovideo.providers.provider_base import LLMProvider


class DialogueSegmentationAgent(BaseAgent):
    stage_name = "dialogue_segmentation"

    def __init__(self, llm: LLMProvider) -> None:
        self.llm = llm

    async def execute(self, context: PipelineContext) -> None:
        if context.state.segments:
            return
        segments: list[Segment] = []
        for chunk in context.state.chunks:
            response = await self.llm.extract_segments(chunk.text)
            for item in response.get("segments", []):
                item["chunk_id"] = chunk.chunk_id
                segments.append(Segment.model_validate(item))
        context.state.segments = segments
        self.write_stage_json(
            context,
            "04_segments.json",
            {"segments": [segment.model_dump(mode="json") for segment in context.state.segments]},
        )
