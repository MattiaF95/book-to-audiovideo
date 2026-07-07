from __future__ import annotations

from collections import OrderedDict

from book_to_audiovideo.agents.base import BaseAgent
from book_to_audiovideo.models.domain import Segment, Speaker
from book_to_audiovideo.pipeline.context import PipelineContext
from book_to_audiovideo.providers.provider_base import LLMProvider


class StoryStructureAgent(BaseAgent):
    stage_name = "story_structure"

    def __init__(self, llm: LLMProvider) -> None:
        self.llm = llm

    async def execute(self, context: PipelineContext) -> None:
        if context.state.segments and context.state.speakers and all(segment.resolved_speaker_id for segment in context.state.segments):
            return
        response = await self.llm.structure_story(
            {
                "corrected_text": context.state.cleaned_text,
                "context": context.state.text_context,
            }
        )
        speakers = OrderedDict()
        for item in response.get("speakers", []):
            speaker = Speaker.model_validate(item)
            speakers[speaker.speaker_id] = speaker
        synthetic_chunk_id = context.state.book_id or context.state.job_id
        segments: list[Segment] = []
        for item in response.get("segments", []):
            segment_data = dict(item)
            segment_data["chunk_id"] = synthetic_chunk_id
            segment = Segment.model_validate(segment_data)
            if not segment.resolved_speaker_id:
                segment.resolved_speaker_id = "narrator" if segment.segment_type.value == "narration" else segment.speaker_hint or "narrator"
            segments.append(segment)
        context.state.speakers = list(speakers.values())
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
        context.state.segments = segments
        self.write_stage_json(
            context,
            "03_story_structure.json",
            {
                "speakers": [speaker.model_dump(mode="json") for speaker in context.state.speakers],
                "segments": [segment.model_dump(mode="json") for segment in context.state.segments],
            },
        )
