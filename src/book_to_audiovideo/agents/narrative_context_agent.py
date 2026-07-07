from __future__ import annotations

from book_to_audiovideo.agents.base import BaseAgent
from book_to_audiovideo.pipeline.context import PipelineContext
from book_to_audiovideo.providers.provider_base import LLMProvider


class NarrativeContextAgent(BaseAgent):
    stage_name = "narrative_context"

    def __init__(self, llm: LLMProvider) -> None:
        self.llm = llm

    async def execute(self, context: PipelineContext) -> None:
        if context.state.text_context:
            return
        response = await self.llm.run_task("narrative_context.md", {"corrected_text": context.state.cleaned_text})
        context.state.text_context = dict(response.get("context", {}))
        self.write_stage_json(
            context,
            "03_narrative_context.json",
            {"context": context.state.text_context},
        )
