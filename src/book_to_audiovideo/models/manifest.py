from datetime import datetime, timezone

from pydantic import BaseModel, Field

from book_to_audiovideo.models.domain import MediaAsset, MixResult, Speaker, TTSOutput, VoiceAssignment
from book_to_audiovideo.models.state import PipelineState


class SegmentDecision(BaseModel):
    segment_id: str
    speaker_id: str | None = None
    voice_id: str | None = None
    mood: str | None = None
    needs_sfx: bool = False
    video_query: list[str] = Field(default_factory=list)
    sfx_query: list[str] = Field(default_factory=list)


class Manifest(BaseModel):
    book_id: str
    source_name: str
    final_video_path: str
    generated_at: str
    speakers: list[Speaker] = Field(default_factory=list)
    voice_assignments: list[VoiceAssignment] = Field(default_factory=list)
    media_assets: list[MediaAsset] = Field(default_factory=list)
    tts_outputs: list[TTSOutput] = Field(default_factory=list)
    mixed_audio: list[MixResult] = Field(default_factory=list)
    decisions: list[SegmentDecision] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


def build_manifest(state: PipelineState) -> Manifest:
    decisions = []
    media_map = {item.segment_id: item for item in state.media_plan}
    voice_map = {item.speaker_id: item for item in state.voice_assignments}
    for segment in state.segments:
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
    return Manifest(
        book_id=state.book_id,
        source_name=state.source_name,
        final_video_path=state.final_video_path or "",
        generated_at=datetime.now(timezone.utc).isoformat(),
        speakers=state.speakers,
        voice_assignments=state.voice_assignments,
        media_assets=state.downloaded_media,
        tts_outputs=state.tts_outputs,
        mixed_audio=state.mixed_audio_paths,
        decisions=decisions,
        warnings=state.warnings,
        errors=state.errors,
    )
