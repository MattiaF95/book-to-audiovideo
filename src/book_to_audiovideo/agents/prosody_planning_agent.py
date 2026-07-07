from __future__ import annotations

from book_to_audiovideo.agents.base import BaseAgent
from book_to_audiovideo.models.domain import ToneTag
from book_to_audiovideo.pipeline.context import PipelineContext
from book_to_audiovideo.providers.provider_base import LLMProvider


class ProsodyPlanningAgent(BaseAgent):
    stage_name = "prosody_planning"

    def __init__(self, llm: LLMProvider) -> None:
        self.llm = llm

    async def execute(self, context: PipelineContext) -> None:
        if context.state.tone_tags:
            return
        response = await self.llm.run_task(
            "prosody_planning.md",
            {
                "context": context.state.text_context,
                "segments": [segment.model_dump(mode="json") for segment in context.state.segments],
                "speakers": [speaker.model_dump(mode="json") for speaker in context.state.speakers],
            },
        )
        by_segment = {item.segment_id: item for item in [ToneTag.model_validate(item) for item in response.get("tone_tags", [])]}
        context.state.tone_tags = [
            by_segment.get(
                segment.segment_id,
                ToneTag(
                    segment_id=segment.segment_id,
                    tagged_text=segment.raw_text,
                    tags_used=[],
                    tag_confidence=0.0,
                ),
            )
            for segment in context.state.segments
        ]
        self.write_stage_json(
            context,
            "10_prosody_planning.json",
            {"tone_tags": [item.model_dump(mode="json") for item in context.state.tone_tags]},
        )
