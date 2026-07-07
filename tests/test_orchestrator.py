from pathlib import Path

from book_to_audiovideo.config import Settings
from book_to_audiovideo.models.domain import AttentionRequest, JobStatus
from book_to_audiovideo.pipeline.orchestrator import JobStore, PipelineOrchestrator


def test_job_store_create_and_load(tmp_path: Path) -> None:
    settings = Settings(OUTPUT_DIR=tmp_path, CACHE_DIR=tmp_path / "cache")
    source = tmp_path / "sample.txt"
    source.write_text("ciao", encoding="utf-8")
    store = JobStore(settings)
    state = store.create_state(source)
    loaded = store.load(state.job_id)
    assert loaded.job_id == state.job_id
    assert loaded.source_name == "sample.txt"


def test_orchestrator_keeps_uploaded_display_name(tmp_path: Path) -> None:
    settings = Settings(OUTPUT_DIR=tmp_path, CACHE_DIR=tmp_path / "cache")
    source = tmp_path / "tmp-upload.bin"
    source.write_text("ciao", encoding="utf-8")
    orchestrator = PipelineOrchestrator(settings)
    state = orchestrator.create_job(source, source_name="romanzo.docx")
    assert state.source_name == "romanzo.docx"
    assert state.book_id == "romanzo"
    assert state.source_uploaded is True


def test_stop_job_marks_job_cancelled(tmp_path: Path) -> None:
    settings = Settings(OUTPUT_DIR=tmp_path, CACHE_DIR=tmp_path / "cache")
    source = tmp_path / "sample.txt"
    source.write_text("ciao", encoding="utf-8")
    orchestrator = PipelineOrchestrator(settings)
    state = orchestrator.create_job(source, source_name="sample.txt")
    stopped = orchestrator.stop_job(state.job_id)
    assert stopped.status == JobStatus.cancelled
    assert stopped.stop_requested is True


def test_resolve_attention_reject_clears_pending_request(tmp_path: Path) -> None:
    settings = Settings(OUTPUT_DIR=tmp_path, CACHE_DIR=tmp_path / "cache")
    source = tmp_path / "sample.txt"
    source.write_text("ciao", encoding="utf-8")
    orchestrator = PipelineOrchestrator(settings)
    state = orchestrator.create_job(source, source_name="sample.txt")
    orchestrator.request_attention(
        state.job_id,
        AttentionRequest(stage="media_fetch", reason="Serve review", details={"error": "x"}),
    )

    rejected = orchestrator.resolve_attention(state.job_id, approved=False)

    assert rejected.status == JobStatus.rejected
    assert rejected.attention_request is None
