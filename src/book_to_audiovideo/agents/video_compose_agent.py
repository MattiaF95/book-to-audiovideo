from __future__ import annotations

from pathlib import Path

from book_to_audiovideo.agents.base import BaseAgent
from book_to_audiovideo.pipeline.context import PipelineContext
from book_to_audiovideo.pipeline.errors import PipelineError
from book_to_audiovideo.services.ffmpeg_service import FFmpegService


class VideoComposeAgent(BaseAgent):
    stage_name = "video_compose"

    def __init__(self, ffmpeg_service: FFmpegService) -> None:
        self.ffmpeg_service = ffmpeg_service

    async def execute(self, context: PipelineContext) -> None:
        if context.state.final_video_path:
            return
        video_assets = [asset for asset in context.state.downloaded_media if asset.media_type == "video"]
        if not video_assets:
            raise PipelineError("Nessun video disponibile per la composizione finale")
        concat_dir = Path(context.state.artifact_dir) / "final"
        concat_dir.mkdir(parents=True, exist_ok=True)
        final_audio = concat_dir / "full_mix.mp3"
        manifest_list = concat_dir / "mix_list.txt"
        manifest_list.write_text(
            "\n".join(f"file '{Path(item.mixed_audio_path).resolve()}'" for item in context.state.mixed_audio_paths),
            encoding="utf-8",
        )
        self.ffmpeg_service._run(
            [
                context.settings.ffmpeg_bin,
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(manifest_list),
                "-c",
                "copy",
                str(final_audio),
            ]
        )
        output_video = concat_dir / f"{context.state.book_id}.mp4"
        self.ffmpeg_service.compose_video(Path(video_assets[0].local_path), final_audio, output_video)
        context.state.final_video_path = str(output_video)
        self.write_stage_json(
            context,
            "13_final_video.json",
            {"final_audio": str(final_audio), "final_video_path": context.state.final_video_path},
        )
