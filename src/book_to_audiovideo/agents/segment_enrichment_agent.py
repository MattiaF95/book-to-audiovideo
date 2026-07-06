from __future__ import annotations

from book_to_audiovideo.agents.base import BaseAgent
from book_to_audiovideo.models.domain import MediaPlanItem, PronunciationHint, ToneTag
from book_to_audiovideo.pipeline.context import PipelineContext
from book_to_audiovideo.providers.provider_base import LLMProvider


class SegmentEnrichmentAgent(BaseAgent):
    stage_name = "segment_enrichment"

    def __init__(self, llm: LLMProvider) -> None:
        self.llm = llm

    async def execute(self, context: PipelineContext) -> None:
        if context.state.pronunciation_overrides and context.state.tone_tags and context.state.media_plan:
            return
        hints: list[PronunciationHint] = []
        tags: list[ToneTag] = []
        media_plan: list[MediaPlanItem] = []
        for segment in context.state.segments:
            response = await self.llm.analyze_text(
                {
                    "mode": "segment_enrichment",
                    "segment": self._segment_payload(segment),
                }
            )
            pronunciation_payload = response.get("pronunciation", {})
            pronunciation_payload["segment_id"] = segment.segment_id
            tone_payload = response.get("tone", {})
            tone_payload["segment_id"] = segment.segment_id
            media_payload = response.get("media", {})
            media_payload["segment_id"] = segment.segment_id
            hints.append(PronunciationHint.model_validate(pronunciation_payload))
            tags.append(ToneTag.model_validate(tone_payload))
            media_plan.append(MediaPlanItem.model_validate(media_payload))
        context.state.pronunciation_overrides = hints
        context.state.tone_tags = tags
        context.state.media_plan = media_plan
        self.write_stage_json(
            context,
            "07_segment_enrichment.json",
            {
                "pronunciation": [hint.model_dump(mode="json") for hint in hints],
                "tone_tags": [tag.model_dump(mode="json") for tag in tags],
                "media_plan": [item.model_dump(mode="json") for item in media_plan],
            },
        )

    @staticmethod
    def _segment_payload(segment) -> dict[str, object]:
        return {
            "segment_id": segment.segment_id,
            "segment_type": segment.segment_type.value,
            "speaker_hint": segment.speaker_hint,
            "resolved_speaker_id": segment.resolved_speaker_id,
            "raw_text": segment.raw_text[:240],
        }
