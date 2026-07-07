from __future__ import annotations

from book_to_audiovideo.agents.base import BaseAgent
from book_to_audiovideo.models.domain import MediaPlanItem
from book_to_audiovideo.pipeline.context import PipelineContext
from book_to_audiovideo.providers.provider_base import LLMProvider


class MediaPlanningAgent(BaseAgent):
    stage_name = "media_planning"

    def __init__(self, llm: LLMProvider) -> None:
        self.llm = llm

    async def execute(self, context: PipelineContext) -> None:
        if context.state.media_plan:
            return
        response = await self.llm.run_task(
            "media_planning.md",
            {
                "context": context.state.text_context,
                "segments": [segment.model_dump(mode="json") for segment in context.state.segments],
            },
        )
        by_segment = {item.segment_id: item for item in [MediaPlanItem.model_validate(item) for item in response.get("media_plan", [])]}
        fallback_keywords = context.state.text_context.get("scene")
        default_query = [str(fallback_keywords).strip()] if fallback_keywords else ["cinematic background"]
        context.state.media_plan = [
            by_segment.get(
                segment.segment_id,
                MediaPlanItem(
                    segment_id=segment.segment_id,
                    video_keywords=default_query,
                    sfx_keywords=[],
                    mood=segment.emotion_hint or str(context.state.text_context.get("tone") or "neutral"),
                    scene_type="generic",
                    media_intensity="low",
                    needs_sfx=False,
                    sfx_timeline_hint=None,
                ),
            )
            for segment in context.state.segments
        ]
        self.write_stage_json(
            context,
            "11_media_planning.json",
            {"media_plan": [item.model_dump(mode="json") for item in context.state.media_plan]},
        )
