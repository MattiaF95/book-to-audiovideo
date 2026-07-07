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
        if self._has_valid_cached_enrichment(context):
            return
        hints: list[PronunciationHint] = []
        tags: list[ToneTag] = []
        media_plan: list[MediaPlanItem] = []
        for segment in context.state.segments:
            payload = {"segment": self._segment_payload(segment)}
            pronunciation_payload = await self.llm.extract_pronunciation_hints(payload)
            pronunciation_payload["segment_id"] = segment.segment_id
            tone_payload = await self.llm.add_tone_tags(payload)
            tone_payload["segment_id"] = segment.segment_id
            media_payload = await self.llm.plan_media_keywords(payload)
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

    @staticmethod
    def _has_valid_cached_enrichment(context: PipelineContext) -> bool:
        state = context.state
        if not (state.pronunciation_overrides and state.tone_tags and state.media_plan):
            return False
        segment_ids = [segment.segment_id for segment in state.segments]
        if (
            len(state.pronunciation_overrides) != len(segment_ids)
            or len(state.tone_tags) != len(segment_ids)
            or len(state.media_plan) != len(segment_ids)
        ):
            return False
        expected_ids = set(segment_ids)
        if {item.segment_id for item in state.pronunciation_overrides} != expected_ids:
            return False
        if {item.segment_id for item in state.tone_tags} != expected_ids:
            return False
        if {item.segment_id for item in state.media_plan} != expected_ids:
            return False
        return all(SegmentEnrichmentAgent._is_valid_tone_tag(item) for item in state.tone_tags)

    @staticmethod
    def _is_valid_tone_tag(item: ToneTag) -> bool:
        text = item.tagged_text.strip()
        return bool(text) and text.lower() != "string"
