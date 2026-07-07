from __future__ import annotations

import random
from pathlib import Path

from book_to_audiovideo.agents.base import BaseAgent
from book_to_audiovideo.models.domain import AttentionRequest, MediaAsset, MediaPlanItem
from book_to_audiovideo.pipeline.context import PipelineContext
from book_to_audiovideo.pipeline.errors import ApprovalRequiredError, ProviderError
from book_to_audiovideo.providers.provider_base import StockMediaProvider
from book_to_audiovideo.services.media_service import MediaService


class MediaFetchAgent(BaseAgent):
    stage_name = "media_fetch"

    def __init__(self, media_provider: StockMediaProvider, media_service: MediaService) -> None:
        self.media_provider = media_provider
        self.media_service = media_service

    async def execute(self, context: PipelineContext) -> None:
        if self._has_valid_cached_media(context):
            return
        media_dir = Path(context.state.artifact_dir) / "media"
        first_item = self._select_media_plan_item(context)
        video_error: str | None = None
        for query in self.media_service.build_fallback_queries(first_item):
            try:
                hits = await self.media_provider.search_videos(query)
                if not hits:
                    continue
                video_asset = await self.media_provider.download_media(random.choice(hits), str(media_dir / "video"), "video", query)
                context.state.downloaded_media = [video_asset]
                self.write_stage_json(
                    context,
                    "10_downloaded_media.json",
                    {"assets": [video_asset.model_dump(mode="json")]},
                )
                break
            except ProviderError as exc:
                video_error = str(exc)
        if not context.state.downloaded_media:
            context.state.attention_request = AttentionRequest(
                stage=self.stage_name,
                reason="Impossibile recuperare il video di sfondo da Pixabay",
                details={"error": video_error or "nessun risultato"},
            )
            raise ApprovalRequiredError(context.state.attention_request.reason)

    @staticmethod
    def _has_valid_cached_media(context: PipelineContext) -> bool:
        if not context.state.downloaded_media:
            return False
        return any(asset.media_type == "video" for asset in context.state.downloaded_media)

    @staticmethod
    def _select_media_plan_item(context: PipelineContext) -> MediaPlanItem:
        if context.state.media_plan:
            return context.state.media_plan[0]
        scene = str(context.state.text_context.get("scene") or "").strip()
        tone = str(context.state.text_context.get("tone") or "").strip()
        setting = str(context.state.text_context.get("setting") or "").strip()
        fallback_keywords = [value for value in [scene, setting, tone] if value]
        if not fallback_keywords:
            fallback_keywords = ["cinematic background"]
        return MediaPlanItem(
            segment_id=context.state.book_id or context.state.job_id,
            video_keywords=fallback_keywords[:3],
            sfx_keywords=[],
            mood=tone or "neutral",
            scene_type=scene or "generic",
            media_intensity="low",
            needs_sfx=False,
            sfx_timeline_hint=None,
        )
