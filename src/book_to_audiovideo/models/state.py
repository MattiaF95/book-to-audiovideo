from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel, Field

from book_to_audiovideo.models.domain import (
    AttentionRequest,
    JobEvent,
    JobStatus,
    MediaAsset,
    MediaPlanItem,
    MixResult,
    PronunciationHint,
    Segment,
    Speaker,
    TTSOutput,
    TTSStitchHistory,
    ToneTag,
    VoiceAssignment,
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class PipelineMetrics(BaseModel):
    started_at: str = Field(default_factory=utc_now_iso)
    finished_at: str | None = None
    total_duration_seconds: float | None = None
    last_updated_at: str = Field(default_factory=utc_now_iso)


class PipelineState(BaseModel):
    job_id: str
    book_id: str
    source_path: str
    source_name: str
    source_type: str
    status: JobStatus = JobStatus.queued
    current_stage: str = "queued"
    raw_text: str = ""
    cleaned_text: str = ""
    text_context: dict[str, object] = Field(default_factory=dict)
    text_corrections: list[dict[str, object]] = Field(default_factory=list)
    text_warnings: list[str] = Field(default_factory=list)
    segments: list[Segment] = Field(default_factory=list)
    speakers: list[Speaker] = Field(default_factory=list)
    voice_assignments: list[VoiceAssignment] = Field(default_factory=list)
    pronunciation_overrides: list[PronunciationHint] = Field(default_factory=list)
    tone_tags: list[ToneTag] = Field(default_factory=list)
    media_plan: list[MediaPlanItem] = Field(default_factory=list)
    downloaded_media: list[MediaAsset] = Field(default_factory=list)
    tts_outputs: list[TTSOutput] = Field(default_factory=list)
    mixed_audio_paths: list[MixResult] = Field(default_factory=list)
    final_video_path: str | None = None
    manifest_path: str | None = None
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    metrics: PipelineMetrics = Field(default_factory=PipelineMetrics)
    events: list[JobEvent] = Field(default_factory=list)
    attention_request: AttentionRequest | None = None
    artifact_dir: str = ""
    speaker_tts_history: dict[str, TTSStitchHistory] = Field(default_factory=dict)
    source_uploaded: bool = False
    stop_requested: bool = False

    def artifact_path(self, *parts: str) -> Path:
        return Path(self.artifact_dir, *parts)
