from __future__ import annotations

from book_to_audiovideo.agents.base import BaseAgent
from book_to_audiovideo.models.domain import VoiceAssignment
from book_to_audiovideo.pipeline.context import PipelineContext
from book_to_audiovideo.providers.provider_base import LLMProvider, TTSProvider


class VoiceAssignmentAgent(BaseAgent):
    stage_name = "voice_assignment"

    def __init__(self, llm: LLMProvider, tts: TTSProvider) -> None:
        self.llm = llm
        self.tts = tts

    async def execute(self, context: PipelineContext) -> None:
        if context.state.voice_assignments:
            return
        available_voices = await self.tts.list_voices()
        response = await self.llm.assign_voice(
            {
                "speakers": [self._speaker_payload(speaker) for speaker in context.state.speakers],
                "available_voices": [
                    {
                        "voice_id": voice.get("voice_id"),
                        "name": voice.get("name"),
                        "labels": self._compact_labels(voice.get("labels", {})),
                    }
                    for voice in available_voices
                ],
            }
        )
        assignments: list[VoiceAssignment] = []
        for item in response.get("assignments", []):
            assignment = await self.tts.select_voice(item)
            assignments.append(assignment)
        context.state.voice_assignments = assignments
        self.write_stage_json(
            context,
            "06_voice_assignments.json",
            {"assignments": [assignment.model_dump(mode="json") for assignment in assignments]},
        )

    @staticmethod
    def _speaker_payload(speaker) -> dict[str, object]:
        return {
            "speaker_id": speaker.speaker_id,
            "name": speaker.name,
            "role": speaker.role,
            "gender": speaker.gender,
            "continuity_key": speaker.continuity_key,
            "preferred_voice_constraints": speaker.preferred_voice_constraints[:4],
        }

    @staticmethod
    def _compact_labels(labels: dict[str, object]) -> dict[str, object]:
        compact: dict[str, object] = {}
        for key, value in labels.items():
            if isinstance(value, str):
                compact[key] = value[:80]
            else:
                compact[key] = value
        return compact
