from pathlib import Path

import anyio

from book_to_audiovideo.agents.tts_agent import TTSAgent
from book_to_audiovideo.config import Settings
from book_to_audiovideo.models.domain import Segment, SegmentType, TTSOutput, TTSStitchHistory, ToneTag, VoiceAssignment
from book_to_audiovideo.models.state import PipelineState
from book_to_audiovideo.pipeline.context import PipelineContext


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
            Segment(segment_id=f"seg-{index}", chunk_id="chunk-1", raw_text=f"Testo {index}", segment_type=SegmentType.narration, start_offset=index, end_offset=index + 1, importance_score=0.5)
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
