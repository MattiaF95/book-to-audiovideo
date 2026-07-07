from __future__ import annotations

import asyncio
import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from book_to_audiovideo.agents.audio_mix_agent import AudioMixAgent
from book_to_audiovideo.agents.audio_planning_agent import AudioPlanningAgent
from book_to_audiovideo.agents.ingestion_agent import IngestionAgent
from book_to_audiovideo.agents.manifest_agent import ManifestAgent
from book_to_audiovideo.agents.media_fetch_agent import MediaFetchAgent
from book_to_audiovideo.agents.qa_agent import QAAgent
from book_to_audiovideo.agents.story_structure_agent import StoryStructureAgent
from book_to_audiovideo.agents.text_preparation_agent import TextPreparationAgent
from book_to_audiovideo.agents.tts_agent import TTSAgent
from book_to_audiovideo.agents.video_compose_agent import VideoComposeAgent
from book_to_audiovideo.config import Settings
from book_to_audiovideo.models.domain import AttentionRequest, JobEvent, JobStatus
from book_to_audiovideo.models.state import PipelineState
from book_to_audiovideo.pipeline.context import PipelineContext
from book_to_audiovideo.pipeline.errors import ApprovalRequiredError, PipelineError
from book_to_audiovideo.providers.elevenlabs_client import ElevenLabsClient
from book_to_audiovideo.providers.groq_client import GroqClient
from book_to_audiovideo.providers.pixabay_client import PixabayClient
from book_to_audiovideo.services.duration_service import DurationService
from book_to_audiovideo.services.ffmpeg_service import FFmpegService
from book_to_audiovideo.services.file_service import FileService
from book_to_audiovideo.services.media_service import MediaService
from book_to_audiovideo.utils.json_utils import read_json, write_json

LOGGER = logging.getLogger(__name__)


class JobStore:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def create_state(self, source_file: Path, source_name: str | None = None) -> PipelineState:
        job_id = uuid4().hex
        display_name = source_name or source_file.name
        book_id = Path(display_name).stem
        artifact_dir = self.settings.output_dir / job_id
        artifact_dir.mkdir(parents=True, exist_ok=True)
        state = PipelineState(
            job_id=job_id,
            book_id=book_id,
            source_path=str(source_file),
            source_name=display_name,
            source_type=Path(display_name).suffix.lower(),
            artifact_dir=str(artifact_dir),
            source_uploaded=True,
        )
        self.save(state)
        return state

    def save(self, state: PipelineState) -> None:
        state.metrics.last_updated_at = datetime.now(timezone.utc).isoformat()
        write_json(Path(state.artifact_dir) / "state.json", state.model_dump(mode="json"))

    def load(self, job_id: str) -> PipelineState:
        return PipelineState.model_validate(read_json(self.settings.output_dir / job_id / "state.json"))

    def list_jobs(self) -> list[PipelineState]:
        jobs: list[PipelineState] = []
        for path in sorted(self.settings.output_dir.glob("*/state.json")):
            jobs.append(PipelineState.model_validate(read_json(path)))
        return sorted(jobs, key=lambda item: item.metrics.started_at, reverse=True)


class PipelineOrchestrator:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.job_store = JobStore(settings)
        prompts_dir = Path(__file__).resolve().parents[1] / "prompts"
        self.file_service = FileService()
        self.duration_service = DurationService(settings)
        self.ffmpeg_service = FFmpegService(settings)
        self.media_service = MediaService()
        self.llm = GroqClient(settings, prompts_dir)
        self.tts = ElevenLabsClient(settings)
        self.media = PixabayClient(settings)
        self._running_tasks: dict[str, asyncio.Task[None]] = {}

    def _build_agents(self) -> list[object]:
        return [
            IngestionAgent(self.file_service),
            TextPreparationAgent(self.llm),
            StoryStructureAgent(self.llm),
            AudioPlanningAgent(self.llm, self.tts),
            MediaFetchAgent(self.media, self.media_service),
            TTSAgent(self.tts, self.duration_service),
            AudioMixAgent(self.ffmpeg_service),
            VideoComposeAgent(self.ffmpeg_service),
            QAAgent(self.ffmpeg_service),
            ManifestAgent(),
        ]

    def create_job(self, source_file: Path, source_name: str | None = None) -> PipelineState:
        state = self.job_store.create_state(source_file, source_name=source_name)
        artifact_source = Path(state.artifact_dir) / "source" / state.source_name
        artifact_source.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_file, artifact_source)
        state.source_path = str(artifact_source)
        self._append_event(state, "queued", "queued", f"File caricato: {state.source_name}")
        self.job_store.save(state)
        return state

    def start_job(self, job_id: str) -> None:
        if job_id in self._running_tasks and not self._running_tasks[job_id].done():
            return
        task = asyncio.create_task(self.run_job(job_id))
        self._running_tasks[job_id] = task

    async def run_job(self, job_id: str) -> None:
        state = self.job_store.load(job_id)
        if state.status == JobStatus.cancelled:
            return
        state.status = JobStatus.running
        state.stop_requested = False
        state.attention_request = None
        self._append_event(state, state.current_stage, "running", "Pipeline avviata")
        self.job_store.save(state)
        context = PipelineContext(settings=self.settings, state=state)
        try:
            for agent in self._build_agents():
                if state.stop_requested:
                    raise asyncio.CancelledError
                self._append_event(state, agent.stage_name, "running", f"Stage avviato: {agent.stage_name}")
                self.job_store.save(state)
                await agent.run(context)
                self._append_event(state, agent.stage_name, "completed", f"Stage completato: {agent.stage_name}")
                self.job_store.save(state)
                if state.status == JobStatus.needs_attention:
                    raise ApprovalRequiredError(state.attention_request.reason if state.attention_request else "Approval richiesta")
            state.status = JobStatus.completed
            state.current_stage = "completed"
            state.metrics.finished_at = datetime.now(timezone.utc).isoformat()
            self._append_event(state, "completed", "completed", "Pipeline completata")
        except asyncio.CancelledError:
            state.status = JobStatus.cancelled
            state.stop_requested = True
            state.metrics.finished_at = datetime.now(timezone.utc).isoformat()
            self._append_event(state, state.current_stage, "cancelled", "Job interrotto manualmente")
        except ApprovalRequiredError as exc:
            state.status = JobStatus.needs_attention
            self._append_event(state, state.current_stage, "needs_attention", str(exc))
        except Exception as exc:
            LOGGER.exception("Pipeline fallita job_id=%s", job_id)
            state.status = JobStatus.failed
            state.errors.append(str(exc))
            state.metrics.finished_at = datetime.now(timezone.utc).isoformat()
            self._append_event(state, state.current_stage, "failed", str(exc))
        finally:
            self.job_store.save(state)
            self._running_tasks.pop(job_id, None)

    def _append_event(self, state: PipelineState, stage: str, status: str, message: str) -> None:
        state.events.append(
            JobEvent(
                timestamp=datetime.now(timezone.utc).isoformat(),
                stage=stage,
                status=status,
                message=message,
            )
        )

    def request_attention(self, job_id: str, attention_request: AttentionRequest) -> PipelineState:
        state = self.job_store.load(job_id)
        state.status = JobStatus.needs_attention
        state.attention_request = attention_request
        self._append_event(state, attention_request.stage, "needs_attention", attention_request.reason)
        self.job_store.save(state)
        return state

    def resolve_attention(self, job_id: str, approved: bool) -> PipelineState:
        state = self.job_store.load(job_id)
        if not state.attention_request:
            raise PipelineError("Nessuna approval pendente")
        if not approved:
            state.attention_request = None
            state.status = JobStatus.rejected
            self._append_event(state, state.current_stage, "rejected", "Job rifiutato da dashboard")
            self.job_store.save(state)
            return state
        state.attention_request = None
        state.status = JobStatus.running
        self._append_event(state, state.current_stage, "approved", "Job riattivato da dashboard")
        self.job_store.save(state)
        self.start_job(job_id)
        return state

    def stop_job(self, job_id: str) -> PipelineState:
        state = self.job_store.load(job_id)
        state.stop_requested = True
        state.attention_request = None
        state.status = JobStatus.cancelled
        state.metrics.finished_at = datetime.now(timezone.utc).isoformat()
        self._append_event(state, state.current_stage, "cancelled", "Job annullato dalla dashboard")
        task = self._running_tasks.get(job_id)
        if task and not task.done():
            task.cancel()
        self.job_store.save(state)
        return state
