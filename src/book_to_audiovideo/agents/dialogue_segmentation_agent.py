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
        response = await self.llm.run_task(
            "dialogue_segmentation.md",
            {
                "corrected_text": context.state.cleaned_text,
                "context": context.state.text_context,
            },
        )
        synthetic_chunk_id = context.state.book_id or context.state.job_id
        segments: list[Segment] = []
        for item in response.get("segments", []):
            segment_data = dict(item)
            segment_data["chunk_id"] = synthetic_chunk_id
            segment_data.setdefault("speaker_hint", None)
            segment_data.setdefault("resolved_speaker_id", None)
            segment_data.setdefault("emotion_hint", None)
            segment_data.setdefault("importance_score", 0.5)
            segments.append(Segment.model_validate(segment_data))
        context.state.segments = segments
        self.write_stage_json(
            context,
            "04_dialogue_segmentation.json",
            {"segments": [segment.model_dump(mode="json") for segment in segments]},
        )
