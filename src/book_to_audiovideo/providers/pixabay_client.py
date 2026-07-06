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
        self._sfx_available = True

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
    async def search_sfx(self, query: str) -> list[dict[str, Any]]:
        if not self._sfx_available:
            return []
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                for endpoint in ("https://pixabay.com/api/sounds/", "https://pixabay.com/api/audio/"):
                    response = await client.get(
                        endpoint,
                        params={"key": self.settings.pixabay_api_key, "q": query, "per_page": 10},
                    )
                    if response.status_code == 404:
                        continue
                    if response.status_code >= 400:
                        raise ProviderError(f"Pixabay audio errore {response.status_code}: {response.text}")
                    return response.json().get("hits", [])
        except httpx.HTTPError as exc:
            raise ProviderError(f"Pixabay rete/DNS non raggiungibile: {exc}") from exc
        self._sfx_available = False
        return []

    @retryable()
    async def download_media(self, asset: dict[str, Any], target_dir: str, media_type: str, query: str) -> MediaAsset:
        target_path = Path(target_dir)
        target_path.mkdir(parents=True, exist_ok=True)
        if media_type == "video":
            source_url = asset["videos"]["medium"]["url"]
            extension = ".mp4"
            asset_id = str(asset["id"])
        else:
            source_url = asset.get("audio") or asset.get("previewURL") or asset.get("url")
            extension = ".mp3"
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
            media_type="video" if media_type == "video" else "audio",
            source_url=source_url,
            local_path=str(local_path),
            duration_seconds=None,
            metadata={"tags": asset.get("tags", ""), "user": asset.get("user", "")},
        )
