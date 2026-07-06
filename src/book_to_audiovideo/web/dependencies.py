from __future__ import annotations

from functools import lru_cache

from book_to_audiovideo.config import get_settings
from book_to_audiovideo.pipeline.orchestrator import PipelineOrchestrator


@lru_cache(maxsize=1)
def get_orchestrator() -> PipelineOrchestrator:
    return PipelineOrchestrator(get_settings())
