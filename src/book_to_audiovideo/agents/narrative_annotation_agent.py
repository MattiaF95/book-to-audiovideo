from __future__ import annotations

from book_to_audiovideo.agents.base import BaseAgent
from book_to_audiovideo.pipeline.context import PipelineContext
from book_to_audiovideo.providers.provider_base import LLMProvider


class NarrativeAnnotationAgent(BaseAgent):
    stage_name = "narrative_annotation"

    def __init__(self, llm: LLMProvider) -> None:
        self.llm = llm

    async def execute(self, context: PipelineContext) -> None:
        if context.state.segments and all(segment.emotion_hint is not None for segment in context.state.segments):
            return
        response = await self.llm.run_task(
            "narrative_annotation.md",
            {
                "context": context.state.text_context,
                "speakers": [speaker.model_dump(mode="json") for speaker in context.state.speakers],
                "segments": [segment.model_dump(mode="json") for segment in context.state.segments],
            },
        )
        by_segment = {item.get("segment_id"): item for item in response.get("annotations", [])}
        for segment in context.state.segments:
            item = by_segment.get(segment.segment_id, {})
            segment.emotion_hint = item.get("emotion_hint")
            segment.importance_score = float(item.get("importance_score", segment.importance_score or 0.5))
        self.write_stage_json(
            context,
            "07_narrative_annotation.json",
            {"segments": [segment.model_dump(mode="json") for segment in context.state.segments]},
        )
