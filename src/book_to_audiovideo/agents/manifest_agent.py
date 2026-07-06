from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from book_to_audiovideo.agents.base import BaseAgent
from book_to_audiovideo.models.manifest import Manifest, SegmentDecision
from book_to_audiovideo.pipeline.context import PipelineContext
from book_to_audiovideo.utils.json_utils import write_json


class ManifestAgent(BaseAgent):
    stage_name = "manifest"

    async def execute(self, context: PipelineContext) -> None:
        decisions = []
        media_map = {item.segment_id: item for item in context.state.media_plan}
        voice_map = {item.speaker_id: item for item in context.state.voice_assignments}
        for segment in context.state.segments:
            media_item = media_map.get(segment.segment_id)
            voice_item = voice_map.get(segment.resolved_speaker_id or "narrator")
            decisions.append(
                SegmentDecision(
                    segment_id=segment.segment_id,
                    speaker_id=segment.resolved_speaker_id,
                    voice_id=voice_item.voice_id if voice_item else None,
                    mood=media_item.mood if media_item else None,
                    needs_sfx=media_item.needs_sfx if media_item else False,
                    video_query=media_item.video_keywords if media_item else [],
                    sfx_query=media_item.sfx_keywords if media_item else [],
                )
            )
        manifest = Manifest(
            book_id=context.state.book_id,
            source_name=context.state.source_name,
            final_video_path=context.state.final_video_path or "",
            generated_at=datetime.now(timezone.utc).isoformat(),
            speakers=context.state.speakers,
            voice_assignments=context.state.voice_assignments,
            media_assets=context.state.downloaded_media,
            tts_outputs=context.state.tts_outputs,
            mixed_audio=context.state.mixed_audio_paths,
            decisions=decisions,
            warnings=context.state.warnings,
            errors=context.state.errors,
        )
        path = Path(context.state.artifact_dir) / "manifest.json"
        write_json(path, manifest.model_dump(mode="json"))
        context.state.manifest_path = str(path)
