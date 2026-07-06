from __future__ import annotations

from pathlib import Path

from book_to_audiovideo.agents.base import BaseAgent
from book_to_audiovideo.models.domain import MixResult
from book_to_audiovideo.pipeline.context import PipelineContext
from book_to_audiovideo.services.ffmpeg_service import FFmpegService


class AudioMixAgent(BaseAgent):
    stage_name = "audio_mix"

    def __init__(self, ffmpeg_service: FFmpegService) -> None:
        self.ffmpeg_service = ffmpeg_service

    async def execute(self, context: PipelineContext) -> None:
        if context.state.mixed_audio_paths:
            return
        asset_by_segment = {asset.metadata.get("segment_id"): asset for asset in context.state.downloaded_media if asset.media_type == "audio"}
        results: list[MixResult] = []
        mix_dir = Path(context.state.artifact_dir) / "mix"
        for tts_output in context.state.tts_outputs:
            sfx = asset_by_segment.get(tts_output.segment_id)
            mixed_path = mix_dir / f"{tts_output.segment_id}.mp3"
            metadata = self.ffmpeg_service.mix_audio_tracks(
                Path(tts_output.audio_path),
                Path(sfx.local_path) if sfx else None,
                mixed_path,
                tts_output.duration_seconds,
            )
            results.append(
                MixResult(
                    segment_id=tts_output.segment_id,
                    mixed_audio_path=str(mixed_path),
                    normalized_levels={"voice_priority": 1.0, "sfx_gain": 0.18 if sfx else 0.0},
                    duration_seconds=tts_output.duration_seconds,
                    metadata={"ffmpeg_command": " ".join(metadata["command"])},
                )
            )
        context.state.mixed_audio_paths = results
        self.write_stage_json(
            context,
            "12_mixed_audio.json",
            {"mixed_audio": [item.model_dump(mode="json") for item in results]},
        )
