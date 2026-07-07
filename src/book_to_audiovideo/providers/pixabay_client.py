from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx

from book_to_audiovideo.config import Settings
from book_to_audiovideo.models.domain import MediaAsset
from book_to_audiovideo.pipeline.errors import ProviderError
from book_to_audiovideo.providers.provider_base import StockMediaProvider
from book_to_audiovideo.utils.retry import retryable


class PixabayClient(StockMediaProvider):
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @retryable()
    async def search_videos(self, query: str) -> list[dict[str, Any]]:
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.get(
                    "https://pixabay.com/api/videos/",
                    params={"key": self.settings.pixabay_api_key, "q": query, "per_page": 10},
                )
        except httpx.HTTPError as exc:
            raise ProviderError(f"Pixabay rete/DNS non raggiungibile: {exc}") from exc
        if response.status_code >= 400:
            raise ProviderError(f"Pixabay video errore {response.status_code}: {response.text}")
        return response.json().get("hits", [])

    @retryable()
    async def download_media(self, asset: dict[str, Any], target_dir: str, media_type: str, query: str) -> MediaAsset:
        if media_type != "video":
            raise ProviderError(f"Pixabay supporta solo video di sfondo, richiesto media_type={media_type!r}")
        target_path = Path(target_dir)
        target_path.mkdir(parents=True, exist_ok=True)
        source_url = self._preferred_video_url(asset)
        extension = ".mp4"
        asset_id = str(asset["id"])
        if not source_url:
            raise ProviderError(f"Asset Pixabay privo di url scaricabile: {asset}")
        local_path = target_path / f"{media_type}_{asset_id}{extension}"
        try:
            async with httpx.AsyncClient(timeout=180) as client:
                response = await client.get(source_url)
        except httpx.HTTPError as exc:
            raise ProviderError(f"Download Pixabay fallito per rete/DNS: {exc}") from exc
        if response.status_code >= 400:
            raise ProviderError(f"Download asset fallito {response.status_code}: {source_url}")
        local_path.write_bytes(response.content)
        return MediaAsset(
            provider="pixabay",
            query=query,
            asset_id=asset_id,
            media_type="video",
            source_url=source_url,
            local_path=str(local_path),
            duration_seconds=None,
            metadata={"tags": asset.get("tags", ""), "user": asset.get("user", "")},
        )

    @staticmethod
    def _preferred_video_url(asset: dict[str, Any]) -> str | None:
        variants = asset.get("videos", {})
        for preferred_key in ("medium", "large", "small"):
            item = variants.get(preferred_key)
            if isinstance(item, dict) and item.get("url"):
                return str(item["url"])
        for item in variants.values():
            if isinstance(item, dict) and item.get("url"):
                return str(item["url"])
        return None
