from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class SegmentType(str, Enum):
    narration = "narration"
    dialogue = "dialogue"


class JobStatus(str, Enum):
    queued = "queued"
    running = "running"
    needs_attention = "needs_attention"
    completed = "completed"
    failed = "failed"
    rejected = "rejected"
    cancelled = "cancelled"


class ReviewAction(str, Enum):
    approve = "approve"
    reject = "reject"


class CleanupChange(BaseModel):
    original: str
    cleaned: str
    reason: str
    confidence: float = Field(ge=0.0, le=1.0)
    start_offset: int
    end_offset: int
    needs_review: bool = False


class Chunk(BaseModel):
    chunk_id: str
    text: str
    order_index: int
    paragraph_start: int
    paragraph_end: int
    estimated_duration_seconds: float


class Segment(BaseModel):
    segment_id: str
    chunk_id: str
    order_index: int = 0
    raw_text: str
    segment_type: SegmentType
    speaker_hint: str | None = None
    resolved_speaker_id: str | None = None
    start_offset: int
    end_offset: int
    emotion_hint: str | None = None
    importance_score: float = Field(ge=0.0, le=1.0)


class Speaker(BaseModel):
    speaker_id: str
    name: str
    role: Literal["narrator", "character"]
    gender: str | None = None
    continuity_key: str
    preferred_voice_constraints: list[str] = Field(default_factory=list)


class VoiceAssignment(BaseModel):
    speaker_id: str
    voice_id: str
    voice_name: str
    delivery_style: str
    tts_prompt_tags: list[str] = Field(default_factory=list)
    continuity_anchor: str


class PronunciationHint(BaseModel):
    segment_id: str
    pronunciation_overrides: dict[str, str] = Field(default_factory=dict)
    phonetic_hints: dict[str, str] = Field(default_factory=dict)
    problem_terms: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)


class ToneTag(BaseModel):
    segment_id: str
    tagged_text: str
    tags_used: list[str] = Field(default_factory=list)
    tag_confidence: float = Field(ge=0.0, le=1.0)


class MediaPlanItem(BaseModel):
    segment_id: str
    video_keywords: list[str] = Field(default_factory=list)
    sfx_keywords: list[str] = Field(default_factory=list)
    mood: str
    scene_type: str
    media_intensity: str
    needs_sfx: bool
    sfx_timeline_hint: str | None = None


class MediaAsset(BaseModel):
    provider: str
    query: str
    asset_id: str
    media_type: Literal["video", "audio"]
    source_url: str
    local_path: str
    duration_seconds: float | None = None
    metadata: dict[str, str | int | float | bool] = Field(default_factory=dict)


class TTSOutput(BaseModel):
    segment_id: str
    speaker_id: str
    voice_id: str
    audio_path: str
    duration_seconds: float
    request_id: str | None = None
    history_item_id: str | None = None
    previous_text: str | None = None
    next_text: str | None = None
    provider_metadata: dict[str, str | int | float | bool] = Field(default_factory=dict)


class TTSStitchHistory(BaseModel):
    previous_request_ids: list[str] = Field(default_factory=list)
    previous_history_item_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _limit_history(self) -> "TTSStitchHistory":
        self.previous_request_ids = self.previous_request_ids[-3:]
        self.previous_history_item_ids = self.previous_history_item_ids[-3:]
        return self

    def append(self, request_id: str | None, history_item_id: str | None) -> None:
        if request_id:
            self.previous_request_ids.append(request_id)
        if history_item_id:
            self.previous_history_item_ids.append(history_item_id)
        self._limit_history()


class MixResult(BaseModel):
    segment_id: str
    mixed_audio_path: str
    normalized_levels: dict[str, float] = Field(default_factory=dict)
    duration_seconds: float
    metadata: dict[str, str | int | float | bool] = Field(default_factory=dict)


class JobEvent(BaseModel):
    timestamp: str
    stage: str
    status: str
    message: str


class AttentionRequest(BaseModel):
    stage: str
    reason: str
    details: dict[str, str | int | float | bool | list[str]] = Field(default_factory=dict)
