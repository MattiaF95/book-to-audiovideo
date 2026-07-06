from __future__ import annotations

from pathlib import Path

from book_to_audiovideo.agents.base import BaseAgent
from book_to_audiovideo.models.domain import AttentionRequest, MediaAsset
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
        if context.state.downloaded_media:
            return
        assets: list[MediaAsset] = []
        media_dir = Path(context.state.artifact_dir) / "media"
        first_item = context.state.media_plan[0]
        video_asset: MediaAsset | None = None
        video_error: str | None = None
        for query in self.media_service.build_fallback_queries(first_item):
            try:
                hits = await self.media_provider.search_videos(query)
                if not hits:
                    continue
                video_asset = await self.media_provider.download_media(hits[0], str(media_dir / "video"), "video", query)
                break
            except ProviderError as exc:
                video_error = str(exc)
        if not video_asset:
            context.state.attention_request = AttentionRequest(
                stage=self.stage_name,
                reason="Impossibile recuperare il video di sfondo da Pixabay",
                details={"error": video_error or "nessun risultato"},
            )
            raise ApprovalRequiredError(context.state.attention_request.reason)
        assets.append(video_asset)
        for item in context.state.media_plan:
            if not item.needs_sfx:
                continue
            fetched = None
            last_error: str | None = None
            for query in self.media_service.build_sfx_queries(item):
                try:
                    hits = await self.media_provider.search_sfx(query)
                    if not hits:
                        continue
                    fetched = await self.media_provider.download_media(hits[0], str(media_dir / "sfx"), "audio", query)
                    break
                except ProviderError as exc:
                    last_error = str(exc)
            if not fetched:
                context.state.warnings.append(
                    f"SFX saltato per segment {item.segment_id}: {last_error or 'nessun risultato da Pixabay'}"
                )
                continue
            fetched.metadata["segment_id"] = item.segment_id
            assets.append(fetched)
        context.state.downloaded_media = assets
        self.write_stage_json(
            context,
            "10_downloaded_media.json",
            {"assets": [asset.model_dump(mode="json") for asset in assets]},
        )
