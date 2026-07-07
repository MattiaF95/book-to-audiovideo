from pathlib import Path

import anyio
import pytest

from book_to_audiovideo.agents.tts_agent import TTSAgent
from book_to_audiovideo.config import Settings
from book_to_audiovideo.models.domain import Segment, SegmentType, TTSOutput, TTSStitchHistory, ToneTag, VoiceAssignment
from book_to_audiovideo.models.state import PipelineState
from book_to_audiovideo.pipeline.context import PipelineContext
from book_to_audiovideo.pipeline.errors import PipelineError


class _FakeTTSProvider:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def synthesize(self, payload: dict) -> TTSOutput:
        self.calls.append(payload)
        audio_path = Path(payload["audio_path"])
        audio_path.parent.mkdir(parents=True, exist_ok=True)
        audio_path.write_bytes(b"audio")
        index = len(self.calls)
        return TTSOutput(
            segment_id=payload["segment_id"],
            speaker_id=payload["speaker_id"],
            voice_id=payload["voice_id"],
            audio_path=str(audio_path),
            duration_seconds=0.0,
            request_id=f"req-{index}",
            history_item_id=f"hist-{index}",
        )


class _FakeDurationService:
    def get_duration(self, path: Path) -> float:
        return 1.0


def test_tts_agent_keeps_three_item_history_queue(tmp_path: Path) -> None:
    settings = Settings(OUTPUT_DIR=tmp_path, CACHE_DIR=tmp_path / "cache")
    state = PipelineState(
        job_id="job-1",
        book_id="book-1",
        source_path=str(tmp_path / "source.txt"),
        source_name="source.txt",
        source_type=".txt",
        artifact_dir=str(tmp_path / "job"),
        segments=[
            Segment(segment_id=f"seg-{index}", chunk_id="chunk-1", order_index=index + 1, raw_text=f"Testo {index}", segment_type=SegmentType.narration, start_offset=index, end_offset=index + 1, importance_score=0.5)
            for index in range(4)
        ],
        tone_tags=[
            ToneTag(segment_id=f"seg-{index}", tagged_text=f"Testo {index}", tag_confidence=0.5)
            for index in range(4)
        ],
        voice_assignments=[
            VoiceAssignment(
                speaker_id="narrator",
                voice_id="voice-1",
                voice_name="Narrator",
                delivery_style="natural",
                continuity_anchor="narrator",
            )
        ],
        speaker_tts_history={"narrator": TTSStitchHistory(previous_request_ids=["r0"], previous_history_item_ids=["h0"])},
    )
    context = PipelineContext(settings=settings, state=state)
    provider = _FakeTTSProvider()
    agent = TTSAgent(provider, _FakeDurationService())

    anyio.run(agent.execute, context)

    assert len(provider.calls) == 4
    assert provider.calls[0]["previous_request_ids"] == ["r0"]
    assert "previous_text" in provider.calls[0]
    assert provider.calls[-1]["previous_request_ids"] == ["req-1", "req-2", "req-3"]
    assert provider.calls[-1]["previous_history_item_ids"] == ["hist-1", "hist-2", "hist-3"]
    assert context.state.speaker_tts_history["narrator"].previous_request_ids == ["req-2", "req-3", "req-4"]
    assert context.state.speaker_tts_history["narrator"].previous_history_item_ids == ["hist-2", "hist-3", "hist-4"]


def test_tts_agent_falls_back_to_raw_text_when_tone_tag_is_placeholder(tmp_path: Path) -> None:
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
                order_index=1,
                raw_text="Testo reale",
                segment_type=SegmentType.narration,
                start_offset=0,
                end_offset=10,
                importance_score=0.5,
            )
        ],
        tone_tags=[ToneTag(segment_id="seg-1", tagged_text="string", tag_confidence=0.0)],
        voice_assignments=[
            VoiceAssignment(
                speaker_id="narrator",
                voice_id="voice-1",
                voice_name="Narrator",
                delivery_style="natural",
                continuity_anchor="narrator",
            )
        ],
    )
    context = PipelineContext(settings=settings, state=state)
    provider = _FakeTTSProvider()
    agent = TTSAgent(provider, _FakeDurationService())

    anyio.run(agent.execute, context)

    assert provider.calls[0]["text"] == "Testo reale"


def test_tts_agent_raises_clear_error_when_voice_assignment_is_missing(tmp_path: Path) -> None:
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
                order_index=1,
                raw_text="Testo reale",
                segment_type=SegmentType.dialogue,
                resolved_speaker_id="hero",
                start_offset=0,
                end_offset=10,
                importance_score=0.5,
            )
        ],
        tone_tags=[ToneTag(segment_id="seg-1", tagged_text="Testo reale", tag_confidence=0.5)],
        voice_assignments=[],
    )
    context = PipelineContext(settings=settings, state=state)
    agent = TTSAgent(_FakeTTSProvider(), _FakeDurationService())

    with pytest.raises(PipelineError, match="Voice assignment mancante"):
        anyio.run(agent.execute, context)
