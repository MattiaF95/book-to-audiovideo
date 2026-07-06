from pathlib import Path

import anyio

from book_to_audiovideo.config import Settings
from book_to_audiovideo.providers.elevenlabs_client import ElevenLabsClient


class _FakeResponse:
    def __init__(self, status_code: int, payload: dict | None = None, content: bytes = b"audio") -> None:
        self.status_code = status_code
        self._payload = payload or {}
        self.content = content
        self.text = ""
        self.headers = {"request-id": "req-1", "history-item-id": "hist-1"}

    def json(self) -> dict:
        return self._payload


class _FakeClient:
    def __init__(self, captured_bodies: list[dict]) -> None:
        self.captured_bodies = captured_bodies

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url: str, headers: dict, json: dict) -> _FakeResponse:
        self.captured_bodies.append(json)
        return _FakeResponse(200)


def test_synthesize_avoids_stitching_for_eleven_v3(monkeypatch, tmp_path: Path) -> None:
    captured_bodies: list[dict] = []
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()
    settings = Settings(
        ELEVENLABS_API_KEY="test-key",
        DEFAULT_TTS_MODEL="eleven_v3",
        OUTPUT_DIR=tmp_path,
        CACHE_DIR=tmp_path / "cache",
    )
    client = ElevenLabsClient(settings)
    monkeypatch.setattr(
        "book_to_audiovideo.providers.elevenlabs_client.httpx.AsyncClient",
        lambda timeout: _FakeClient(captured_bodies),
    )

    result = anyio.run(
        client.synthesize,
        {
            "segment_id": "seg-1",
            "speaker_id": "speaker-1",
            "voice_id": "voice-1",
            "text": "ciao",
            "audio_path": str(tmp_path / "out.mp3"),
            "previous_request_ids": ["r1", "r2", "r3", "r4"],
            "previous_history_item_ids": ["h1", "h2", "h3", "h4"],
            "previous_text": "prima",
            "next_text": "dopo",
        },
    )

    assert captured_bodies[0]["model_id"] == "eleven_v3"
    assert "previous_request_ids" not in captured_bodies[0]
    assert "previous_history_item_ids" not in captured_bodies[0]
    assert captured_bodies[0]["previous_text"] == "prima"
    assert captured_bodies[0]["next_text"] == "dopo"
    assert result.request_id == "req-1"
    assert result.history_item_id == "hist-1"


def test_synthesize_limits_stitching_history_to_three_items(monkeypatch, tmp_path: Path) -> None:
    captured_bodies: list[dict] = []
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()
    settings = Settings(
        ELEVENLABS_API_KEY="test-key",
        DEFAULT_LLM_MODEL="ignored",
        DEFAULT_TTS_MODEL="eleven_multilingual_v2",
        OUTPUT_DIR=tmp_path,
        CACHE_DIR=tmp_path / "cache",
    )
    client = ElevenLabsClient(settings)
    monkeypatch.setattr(
        "book_to_audiovideo.providers.elevenlabs_client.httpx.AsyncClient",
        lambda timeout: _FakeClient(captured_bodies),
    )

    anyio.run(
        client.synthesize,
        {
            "segment_id": "seg-1",
            "speaker_id": "speaker-1",
            "voice_id": "voice-1",
            "text": "ciao",
            "audio_path": str(tmp_path / "out.mp3"),
            "previous_request_ids": ["r1", "r2", "r3", "r4"],
            "previous_history_item_ids": ["h1", "h2", "h3", "h4"],
            "previous_text": "prima",
            "next_text": "dopo",
        },
    )

    assert captured_bodies[0]["model_id"] == "eleven_multilingual_v2"
    assert captured_bodies[0]["previous_request_ids"] == ["r2", "r3", "r4"]
    assert captured_bodies[0]["previous_history_item_ids"] == ["h2", "h3", "h4"]
    assert "previous_text" not in captured_bodies[0]
    assert "next_text" not in captured_bodies[0]
