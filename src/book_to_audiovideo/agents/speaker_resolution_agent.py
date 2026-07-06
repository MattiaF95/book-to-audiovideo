from __future__ import annotations

from collections import OrderedDict

from book_to_audiovideo.agents.base import BaseAgent
from book_to_audiovideo.models.domain import Segment, Speaker
from book_to_audiovideo.pipeline.context import PipelineContext
from book_to_audiovideo.providers.provider_base import LLMProvider


class SpeakerResolutionAgent(BaseAgent):
    stage_name = "speaker_resolution"

    def __init__(self, llm: LLMProvider) -> None:
        self.llm = llm

    async def execute(self, context: PipelineContext) -> None:
        if context.state.speakers and all(segment.resolved_speaker_id for segment in context.state.segments):
            return
        response = await self.llm.resolve_speaker(
            {
                "segments": [self._segment_payload(segment) for segment in context.state.segments],
                "existing_speakers": [self._speaker_payload(speaker) for speaker in context.state.speakers],
            }
        )
        speaker_map = OrderedDict()
        for item in response.get("speakers", []):
            speaker = Speaker.model_validate(item)
            speaker_map[speaker.speaker_id] = speaker
        segment_speakers = response.get("segment_speaker_map", {})
        for segment in context.state.segments:
            if segment.segment_id in segment_speakers:
                segment.resolved_speaker_id = segment_speakers[segment.segment_id]
            elif segment.segment_type.value == "narration":
                segment.resolved_speaker_id = "narrator"
        context.state.speakers = list(speaker_map.values())
        if not any(speaker.speaker_id == "narrator" for speaker in context.state.speakers):
            context.state.speakers.insert(
                0,
                Speaker(
                    speaker_id="narrator",
                    name="Narrator",
                    role="narrator",
                    gender="neutral",
                    continuity_key="narrator",
                    preferred_voice_constraints=["clear", "neutral"],
                ),
            )
        self.write_stage_json(
            context,
            "05_speakers.json",
            {
                "speakers": [speaker.model_dump(mode="json") for speaker in context.state.speakers],
                "segments": [segment.model_dump(mode="json") for segment in context.state.segments],
            },
        )

    @staticmethod
    def _segment_payload(segment: Segment) -> dict[str, object]:
        return {
            "segment_id": segment.segment_id,
            "segment_type": segment.segment_type.value,
            "speaker_hint": segment.speaker_hint,
            "raw_text": segment.raw_text[:220],
        }

    @staticmethod
    def _speaker_payload(speaker: Speaker) -> dict[str, object]:
        return {
            "speaker_id": speaker.speaker_id,
            "name": speaker.name,
            "role": speaker.role,
            "gender": speaker.gender,
            "continuity_key": speaker.continuity_key,
            "preferred_voice_constraints": speaker.preferred_voice_constraints[:4],
        }
