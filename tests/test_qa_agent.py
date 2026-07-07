from pathlib import Path

import anyio

from book_to_audiovideo.agents.qa_agent import QAAgent
from book_to_audiovideo.config import Settings
from book_to_audiovideo.models.state import PipelineState
from book_to_audiovideo.pipeline.context import PipelineContext


class _FakeFFmpegService:
    def measure_loudness(self, media_path: Path) -> float:
        return -35.0

    def verify_duration(self, media_path: Path) -> float:
        return 12.0


def test_qa_agent_propagates_warnings_to_pipeline_state(tmp_path: Path) -> None:
    settings = Settings(OUTPUT_DIR=tmp_path, CACHE_DIR=tmp_path / "cache")
    state = PipelineState(
        job_id="job-1",
        book_id="book-1",
        source_path=str(tmp_path / "source.txt"),
        source_name="source.txt",
        source_type=".txt",
        artifact_dir=str(tmp_path / "job"),
        final_video_path=str(tmp_path / "job" / "final.mp4"),
    )
    context = PipelineContext(settings=settings, state=state)
    agent = QAAgent(_FakeFFmpegService())

    anyio.run(agent.execute, context)

    assert "Loudness out of expected range: -35.0" in context.state.warnings
