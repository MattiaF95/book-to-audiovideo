from __future__ import annotations

from book_to_audiovideo.agents.base import BaseAgent
from book_to_audiovideo.pipeline.context import PipelineContext
from book_to_audiovideo.providers.provider_base import LLMProvider


class TextCleanupAgent(BaseAgent):
    stage_name = "text_cleanup"

    def __init__(self, llm: LLMProvider) -> None:
        self.llm = llm

    async def execute(self, context: PipelineContext) -> None:
        if context.state.cleaned_text:
            return
        context.state.cleaned_text = context.state.raw_text.strip()
        context.state.text_corrections = []
        context.state.text_warnings = ["text_cleanup saltato temporaneamente: uso del testo originale"]
        self.write_stage_json(
            context,
            "02_text_cleanup.json",
            {
                "corrected_text": context.state.cleaned_text,
                "corrections": context.state.text_corrections,
                "warnings": context.state.text_warnings,
            },
        )
