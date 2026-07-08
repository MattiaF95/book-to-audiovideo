from __future__ import annotations

from book_to_audiovideo.agents.base import BaseAgent
from book_to_audiovideo.pipeline.context import PipelineContext
from book_to_audiovideo.providers.provider_base import LLMProvider


class SpeakerAttributionAgent(BaseAgent):
    stage_name = "speaker_attribution"

    def __init__(self, llm: LLMProvider) -> None:
        self.llm = llm

    async def execute(self, context: PipelineContext) -> None:
        if context.state.segments and all(segment.resolved_speaker_id for segment in context.state.segments):
            return
        response = await self.llm.run_task(
            "speaker_attribution.md",
            {
                "corrected_text": context.state.cleaned_text,
                "context": context.state.text_context,
                "speakers": [speaker.model_dump(mode="json") for speaker in context.state.speakers],
                "segments": [segment.model_dump(mode="json") for segment in context.state.segments],
            },
        )
        by_segment = {item.get("segment_id"): item for item in response.get("assignments", [])}
        for segment in context.state.segments:
            item = by_segment.get(segment.segment_id, {})
            if item.get("speaker_hint") is not None:
                segment.speaker_hint = item.get("speaker_hint")
            resolved = item.get("resolved_speaker_id")
            if resolved:
                segment.resolved_speaker_id = resolved
            elif segment.segment_type.value == "narration":
                segment.resolved_speaker_id = next(
                    (s.speaker_id for s in context.state.speakers if s.role == "narrator"),
                    "narrator",
                )
            else:
                segment.resolved_speaker_id = None
                context.state.warnings.append(
                    f"speaker_attribution: segmento {segment.segment_id} non attribuito"
                )
        self.write_stage_json(
            context,
            "06_speaker_attribution.json",
            {"segments": [segment.model_dump(mode="json") for segment in context.state.segments]},
        )