from __future__ import annotations

from pathlib import Path

from book_to_audiovideo.agents.base import BaseAgent
from book_to_audiovideo.pipeline.context import PipelineContext
from book_to_audiovideo.services.ffmpeg_service import FFmpegService


class QAAgent(BaseAgent):
    stage_name = "qa"

    def __init__(self, ffmpeg_service: FFmpegService) -> None:
        self.ffmpeg_service = ffmpeg_service

    async def execute(self, context: PipelineContext) -> None:
        video_path = Path(context.state.final_video_path)
        loudness = self.ffmpeg_service.measure_loudness(video_path)
        duration = self.ffmpeg_service.verify_duration(video_path)

        warnings = []

        if loudness is None:
            warnings.append("Loudness unavailable.")
        elif isinstance(loudness, dict):
            if loudness.get("warning"):
                warnings.append(str(loudness["warning"]))
        elif isinstance(loudness, (int, float)):
            if loudness < -30 or loudness > -8:
                warnings.append(f"Loudness out of expected range: {loudness}")

        if duration is None or duration <= 0:
            warnings.append("Duration unavailable or invalid.")

        status = "pass" if not warnings else "warning"
        for warning in warnings:
            if warning not in context.state.warnings:
                context.state.warnings.append(warning)

        self.write_stage_json(
            context,
            "14_qa.json",
            {
                "loudness": loudness,
                "duration_seconds": duration,
                "status": status,
                "warnings": warnings,
            },
        )
