from pydantic import BaseModel, Field

from book_to_audiovideo.models.domain import MediaAsset, MixResult, Speaker, TTSOutput, VoiceAssignment


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
