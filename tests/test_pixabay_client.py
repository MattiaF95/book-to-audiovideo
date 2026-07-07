from pathlib import Path

import anyio

from book_to_audiovideo.config import Settings
from book_to_audiovideo.providers.pixabay_client import PixabayClient


class _FakeResponse:
    def __init__(self, status_code: int, payload: dict | None = None) -> None:
        self.status_code = status_code
        self._payload = payload or {}
        self.text = "not found"

    def json(self) -> dict:
        return self._payload


class _FakeClient:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url: str, params: dict) -> _FakeResponse:
        return _FakeResponse(404)


def test_preferred_video_url_prefers_medium_variant() -> None:
    asset = {
        "videos": {
            "tiny": {"url": "https://example.com/tiny.mp4", "width": 640, "height": 360, "size": 1000},
            "medium": {"url": "https://example.com/medium.mp4", "width": 1280, "height": 720, "size": 2000},
            "large": {"url": "https://example.com/large.mp4", "width": 1920, "height": 1080, "size": 3000},
        }
    }

    assert PixabayClient._preferred_video_url(asset) == "https://example.com/medium.mp4"
