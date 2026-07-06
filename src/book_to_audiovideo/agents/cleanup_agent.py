from __future__ import annotations

from book_to_audiovideo.agents.base import BaseAgent
from book_to_audiovideo.models.domain import CleanupChange
from book_to_audiovideo.pipeline.context import PipelineContext
from book_to_audiovideo.providers.provider_base import LLMProvider
from book_to_audiovideo.services.text_service import TextService


class CleanupAgent(BaseAgent):
    stage_name = "cleanup"

    def __init__(self, llm: LLMProvider, text_service: TextService) -> None:
        self.llm = llm
        self.text_service = text_service

    async def execute(self, context: PipelineContext) -> None:
        if context.state.cleaned_text:
            return
        chunks = self.text_service.split_into_chunks(
            context.state.raw_text,
            max_words=context.settings.cleanup_chunk_words,
        )
        cleaned_chunks: list[str] = []
        cleanup_diff: list[CleanupChange] = []
        warnings: list[str] = []
        for chunk in chunks:
            response = await self.llm.cleanup_text(chunk.text)
            cleaned_chunks.append(response.get("cleaned_text") or chunk.text)
            cleanup_diff.extend(CleanupChange.model_validate(item) for item in response.get("changes", []))
            warnings.extend(response.get("warnings", []))
        context.state.cleaned_text = "\n\n".join(part.strip() for part in cleaned_chunks if part.strip())
        context.state.cleanup_diff = cleanup_diff
        context.state.cleanup_warnings = warnings
        self.write_stage_json(
            context,
            "02_cleanup.json",
            {
                "chunks_processed": len(chunks),
                "cleaned_text_preview": context.state.cleaned_text[:4000],
                "changes": [item.model_dump(mode="json") for item in cleanup_diff],
                "warnings": warnings,
            },
        )
