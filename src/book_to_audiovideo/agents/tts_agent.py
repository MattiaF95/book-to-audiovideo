from __future__ import annotations

from pathlib import Path

from book_to_audiovideo.agents.base import BaseAgent
from book_to_audiovideo.models.domain import TTSStitchHistory
from book_to_audiovideo.pipeline.context import PipelineContext
from book_to_audiovideo.pipeline.errors import PipelineError
from book_to_audiovideo.providers.provider_base import TTSProvider
from book_to_audiovideo.services.duration_service import DurationService


class TTSAgent(BaseAgent):
    stage_name = "tts"

    def __init__(self, tts_provider: TTSProvider, duration_service: DurationService) -> None:
        self.tts_provider = tts_provider
        self.duration_service = duration_service

    async def execute(self, context: PipelineContext) -> None:
        if context.state.tts_outputs:
            return
        tone_by_segment = {item.segment_id: item for item in context.state.tone_tags}
        voice_by_speaker = {item.speaker_id: item for item in context.state.voice_assignments}
        audio_dir = Path(context.state.artifact_dir) / "tts"
        outputs = []
        for index, segment in enumerate(context.state.segments):
            speaker_id = segment.resolved_speaker_id or "narrator"
            if speaker_id not in voice_by_speaker:
                raise PipelineError(f"Voice assignment mancante per speaker {speaker_id}")
            assignment = voice_by_speaker[speaker_id]
            tone = tone_by_segment[segment.segment_id]
            stitch_history = context.state.speaker_tts_history.setdefault(speaker_id, TTSStitchHistory())
            previous_request_ids = stitch_history.previous_request_ids[-3:]
            previous_history_item_ids = stitch_history.previous_history_item_ids[-3:]
            next_text = context.state.segments[index + 1].raw_text if index + 1 < len(context.state.segments) else None
            tts_text = self._resolve_tts_text(segment.raw_text, tone.tagged_text)
            response = await self.tts_provider.synthesize(
                {
                    "segment_id": segment.segment_id,
                    "speaker_id": speaker_id,
                    "voice_id": assignment.voice_id,
                    "text": tts_text,
                    "audio_path": str(audio_dir / f"{segment.segment_id}.mp3"),
                    "previous_text": context.state.segments[index - 1].raw_text if index > 0 else None,
                    "next_text": next_text,
                    "previous_request_ids": previous_request_ids,
                    "previous_history_item_ids": previous_history_item_ids,
                    "next_request_ids": [],
                }
            )
            response.duration_seconds = self.duration_service.get_duration(Path(response.audio_path))
            outputs.append(response)
            stitch_history.append(response.request_id, response.history_item_id)
        context.state.tts_outputs = outputs
        self.write_stage_json(
            context,
            "11_tts_outputs.json",
            {"tts_outputs": [item.model_dump(mode="json") for item in outputs]},
        )

    @staticmethod
    def _resolve_tts_text(raw_text: str, tagged_text: str) -> str:
        candidate = tagged_text.strip()
        if candidate and candidate.lower() != "string":
            return candidate
        return raw_text.strip()
