from __future__ import annotations

from book_to_audiovideo.agents.base import BaseAgent
from book_to_audiovideo.models.domain import PronunciationHint
from book_to_audiovideo.pipeline.context import PipelineContext
from book_to_audiovideo.providers.provider_base import LLMProvider


class PronunciationPlanningAgent(BaseAgent):
    stage_name = "pronunciation_planning"

    def __init__(self, llm: LLMProvider) -> None:
        self.llm = llm

    async def execute(self, context: PipelineContext) -> None:
        if context.state.pronunciation_overrides:
            return
        response = await self.llm.run_task(
            "pronunciation_planning.md",
            {
                "segments": [segment.model_dump(mode="json") for segment in context.state.segments],
                "speakers": [speaker.model_dump(mode="json") for speaker in context.state.speakers],
            },
        )
        by_segment = {
            item.segment_id: item
            for item in [PronunciationHint.model_validate(item) for item in response.get("pronunciation", [])]
        }
        context.state.pronunciation_overrides = [
            by_segment.get(
                segment.segment_id,
                PronunciationHint(
                    segment_id=segment.segment_id,
                    pronunciation_overrides={},
                    phonetic_hints={},
                    problem_terms=[],
                    confidence=0.0,
                ),
            )
            for segment in context.state.segments
        ]
        self.write_stage_json(
            context,
            "09_pronunciation_planning.json",
            {"pronunciation": [item.model_dump(mode="json") for item in context.state.pronunciation_overrides]},
        )
