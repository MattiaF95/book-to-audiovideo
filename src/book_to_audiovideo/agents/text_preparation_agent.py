from __future__ import annotations

from book_to_audiovideo.agents.base import BaseAgent
from book_to_audiovideo.pipeline.context import PipelineContext
from book_to_audiovideo.providers.provider_base import LLMProvider


class TextPreparationAgent(BaseAgent):
    stage_name = "text_preparation"

    def __init__(self, llm: LLMProvider) -> None:
        self.llm = llm

    async def execute(self, context: PipelineContext) -> None:
        if context.state.cleaned_text and context.state.text_context:
            return
        response = await self.llm.prepare_text({"text": context.state.raw_text})
        context.state.cleaned_text = (response.get("corrected_text") or context.state.raw_text).strip()
        context.state.text_corrections = list(response.get("corrections", []))
        context.state.text_context = dict(response.get("context", {}))
        context.state.text_warnings = list(response.get("warnings", []))
        self.write_stage_json(
            context,
            "02_text_preparation.json",
            {
                "corrected_text": context.state.cleaned_text,
                "corrections": context.state.text_corrections,
                "context": context.state.text_context,
                "warnings": context.state.text_warnings,
            },
        )
