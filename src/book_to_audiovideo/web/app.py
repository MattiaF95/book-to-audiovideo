from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from book_to_audiovideo.config import get_settings
from book_to_audiovideo.models.domain import ReviewAction
from book_to_audiovideo.pipeline.errors import PipelineError
from book_to_audiovideo.web.dependencies import get_orchestrator


def create_app() -> FastAPI:
    settings = get_settings()
    base_dir = Path(__file__).resolve().parent
    templates = Jinja2Templates(directory=str(base_dir / "templates"))
    app = FastAPI(title="Book to Audiovideo")
    app.mount("/static", StaticFiles(directory=str(base_dir / "static")), name="static")
    app.mount("/artifacts", StaticFiles(directory=str(settings.output_dir)), name="artifacts")

    @app.get("/", response_class=HTMLResponse)
    async def dashboard(request: Request) -> HTMLResponse:
        orchestrator = get_orchestrator()
        jobs = orchestrator.job_store.list_jobs()
        return templates.TemplateResponse(
            request=request,
            name="dashboard.html",
            context={"jobs": jobs},
        )

    @app.post("/api/jobs")
    async def create_job(file: UploadFile = File(...)) -> dict:
        file_name = (file.filename or "").strip()
        if not file_name:
            raise HTTPException(status_code=400, detail="Nessun file selezionato")
        suffix = Path(file_name).suffix.lower()
        if suffix not in {".txt", ".md", ".pdf", ".docx"}:
            raise HTTPException(status_code=400, detail="Formato non supportato")
        file_bytes = await file.read()
        if not file_bytes:
            raise HTTPException(status_code=400, detail="File vuoto")
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(file_bytes)
            temp_path = Path(temp_file.name)
        orchestrator = get_orchestrator()
        state = orchestrator.create_job(temp_path, source_name=file_name)
        temp_path.unlink(missing_ok=True)
        orchestrator.start_job(state.job_id)
        return {"job_id": state.job_id}

    @app.get("/api/jobs")
    async def list_jobs() -> list[dict]:
        orchestrator = get_orchestrator()
        return [job.model_dump(mode="json") for job in orchestrator.job_store.list_jobs()]

    @app.get("/api/jobs/{job_id}")
    async def get_job(job_id: str) -> dict:
        orchestrator = get_orchestrator()
        try:
            state = orchestrator.job_store.load(job_id)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Job non trovato") from exc
        return state.model_dump(mode="json")

    @app.post("/api/jobs/{job_id}/review")
    async def review_job(job_id: str, action: ReviewAction = Form(...)) -> dict:
        orchestrator = get_orchestrator()
        try:
            state = orchestrator.resolve_attention(job_id, approved=action == ReviewAction.approve)
        except PipelineError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return state.model_dump(mode="json")

    @app.post("/api/jobs/{job_id}/stop")
    async def stop_job(job_id: str) -> dict:
        orchestrator = get_orchestrator()
        try:
            state = orchestrator.stop_job(job_id)
        except PipelineError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return state.model_dump(mode="json")

    @app.get("/jobs/{job_id}")
    async def open_job(job_id: str) -> RedirectResponse:
        return RedirectResponse(url=f"/?job={job_id}")

    return app
