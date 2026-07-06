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


def test_search_sfx_falls_back_to_empty_list_on_404(monkeypatch) -> None:
    settings = Settings(PIXABAY_API_KEY="test", OUTPUT_DIR=Path("/tmp"), CACHE_DIR=Path("/tmp/cache"))
    client = PixabayClient(settings)
    monkeypatch.setattr("book_to_audiovideo.providers.pixabay_client.httpx.AsyncClient", lambda timeout: _FakeClient())

    result = anyio.run(client.search_sfx, "wind")
    assert result == []
    assert client._sfx_available is False
