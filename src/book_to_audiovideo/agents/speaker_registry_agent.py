from __future__ import annotations

from collections import OrderedDict

from book_to_audiovideo.agents.base import BaseAgent
from book_to_audiovideo.models.domain import Speaker
from book_to_audiovideo.pipeline.context import PipelineContext
from book_to_audiovideo.providers.provider_base import LLMProvider


class SpeakerRegistryAgent(BaseAgent):
    stage_name = "speaker_registry"

    def __init__(self, llm: LLMProvider) -> None:
        self.llm = llm

    async def execute(self, context: PipelineContext) -> None:
        if context.state.speakers:
            return
        response = await self.llm.run_task(
            "speaker_registry.md",
            {
                "corrected_text": context.state.cleaned_text,
                "context": context.state.text_context,
            },
        )
        speakers = OrderedDict()
        for item in response.get("speakers", []):
            speaker = Speaker.model_validate(item)
            speakers[speaker.speaker_id] = speaker
        if "narrator" not in speakers:
            speakers["narrator"] = Speaker(
                speaker_id="narrator",
                name="Narrator",
                role="narrator",
                gender=None,
                continuity_key="narrator",
                preferred_voice_constraints=["clear"],
            )
        context.state.speakers = list(speakers.values())
        self.write_stage_json(
            context,
            "05_speaker_registry.json",
            {"speakers": [speaker.model_dump(mode="json") for speaker in context.state.speakers]},
        )
