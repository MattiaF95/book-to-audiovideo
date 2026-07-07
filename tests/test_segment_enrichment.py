from pathlib import Path

import anyio

from book_to_audiovideo.agents.segment_enrichment_agent import SegmentEnrichmentAgent
from book_to_audiovideo.config import Settings
from book_to_audiovideo.models.domain import MediaPlanItem, PronunciationHint, Segment, SegmentType, ToneTag
from book_to_audiovideo.models.state import PipelineState
from book_to_audiovideo.pipeline.context import PipelineContext


def test_segment_enrichment_models_are_compatible() -> None:
    hint = PronunciationHint(segment_id="seg-1", confidence=0.8)
    tone = ToneTag(segment_id="seg-1", tagged_text="Hello", tag_confidence=0.6)
    media = MediaPlanItem(
        segment_id="seg-1",
        video_keywords=["library", "moonlight"],
        sfx_keywords=["wind"],
        mood="tense",
        scene_type="library",
        media_intensity="medium",
        needs_sfx=True,
        sfx_timeline_hint="soft wind",
    )
    assert hint.segment_id == tone.segment_id == media.segment_id


class _FakeLLMProvider:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []

    async def cleanup_text(self, text: str) -> dict:
        raise NotImplementedError

    async def analyze_text(self, chunk_text: str) -> dict:
        raise NotImplementedError

    async def extract_segments(self, chunk_text: str) -> dict:
        raise NotImplementedError

    async def resolve_speaker(self, payload: dict) -> dict:
        raise NotImplementedError

    async def assign_voice(self, payload: dict) -> dict:
        raise NotImplementedError

    async def extract_pronunciation_hints(self, payload: dict) -> dict:
        self.calls.append(("pronunciation", payload))
        return {"pronunciation_overrides": {}, "phonetic_hints": {}, "problem_terms": [], "confidence": 0.2}

    async def add_tone_tags(self, payload: dict) -> dict:
        self.calls.append(("tone", payload))
        return {"tagged_text": payload["segment"]["raw_text"], "tags_used": [], "tag_confidence": 0.3}

    async def plan_media_keywords(self, payload: dict) -> dict:
        self.calls.append(("media", payload))
        return {
            "video_keywords": ["library"],
            "sfx_keywords": [],
            "mood": "tense",
            "scene_type": "interior",
            "media_intensity": "low",
            "needs_sfx": False,
            "sfx_timeline_hint": None,
        }


def test_segment_enrichment_agent_uses_dedicated_methods(tmp_path: Path) -> None:
    settings = Settings(OUTPUT_DIR=tmp_path, CACHE_DIR=tmp_path / "cache")
    state = PipelineState(
        job_id="job-1",
        book_id="book-1",
        source_path=str(tmp_path / "source.txt"),
        source_name="source.txt",
        source_type=".txt",
        artifact_dir=str(tmp_path / "job"),
        segments=[
            Segment(
                segment_id="seg-1",
                chunk_id="chunk-1",
                raw_text="Ciao dal segmento",
                segment_type=SegmentType.narration,
                start_offset=0,
                end_offset=16,
                importance_score=0.5,
            )
        ],
    )
    context = PipelineContext(settings=settings, state=state)
    provider = _FakeLLMProvider()

    anyio.run(SegmentEnrichmentAgent(provider).execute, context)

    assert [name for name, _ in provider.calls] == ["pronunciation", "tone", "media"]
    assert context.state.tone_tags[0].tagged_text == "Ciao dal segmento"


def test_segment_enrichment_agent_rebuilds_invalid_cached_tone_tags(tmp_path: Path) -> None:
    settings = Settings(OUTPUT_DIR=tmp_path, CACHE_DIR=tmp_path / "cache")
    state = PipelineState(
        job_id="job-1",
        book_id="book-1",
        source_path=str(tmp_path / "source.txt"),
        source_name="source.txt",
        source_type=".txt",
        artifact_dir=str(tmp_path / "job"),
        segments=[
            Segment(
                segment_id="seg-1",
                chunk_id="chunk-1",
                raw_text="Ciao dal segmento",
                segment_type=SegmentType.narration,
                start_offset=0,
                end_offset=16,
                importance_score=0.5,
            )
        ],
        pronunciation_overrides=[PronunciationHint(segment_id="seg-1", confidence=0.1)],
        tone_tags=[ToneTag(segment_id="seg-1", tagged_text="string", tag_confidence=0.0)],
        media_plan=[
            MediaPlanItem(
                segment_id="seg-1",
                video_keywords=["old"],
                sfx_keywords=[],
                mood="flat",
                scene_type="unknown",
                media_intensity="low",
                needs_sfx=False,
                sfx_timeline_hint=None,
            )
        ],
    )
    context = PipelineContext(settings=settings, state=state)
    provider = _FakeLLMProvider()

    anyio.run(SegmentEnrichmentAgent(provider).execute, context)

    assert provider.calls
    assert context.state.tone_tags[0].tagged_text == "Ciao dal segmento"
