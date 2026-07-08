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
        segment_text_by_id = {segment.segment_id: segment.raw_text for segment in context.state.segments}
        by_segment = {}
        for item in response.get("tone_tags", []):
            normalized = dict(item)
            segment_id = str(normalized.get("segment_id", "")).strip()
            normalized.setdefault("tagged_text", segment_text_by_id.get(segment_id, ""))
            normalized.setdefault("tags_used", [])
            normalized.setdefault("tag_confidence", 0.0)
            tone_tag = ToneTag.model_validate(normalized)
            by_segment[tone_tag.segment_id] = tone_tag
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
