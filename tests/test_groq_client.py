from pathlib import Path

import anyio

from book_to_audiovideo.config import Settings
from book_to_audiovideo.providers.groq_client import GroqClient


class _FakeResponse:
    def __init__(self, status_code: int, payload: dict) -> None:
        self.status_code = status_code
        self._payload = payload
        self.text = ""

    def json(self) -> dict:
        return self._payload


class _FakeClient:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url: str, headers: dict, json: dict) -> _FakeResponse:
        assert url == "https://api.groq.com/openai/v1/chat/completions"
        assert headers["Authorization"].startswith("Bearer ")
        assert json["model"] == "llama-3.1-8b-instant"
        assert json["response_format"] == {"type": "json_object"}
        return _FakeResponse(
            200,
            {
                "choices": [
                    {
                        "message": {
                            "content": '{"cleaned_text":"ok","changes":[],"warnings":[]}'
                        }
                    }
                ]
            },
        )


def test_groq_client_returns_structured_json(monkeypatch, tmp_path: Path) -> None:
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()
    (prompts_dir / "cleanup_text.md").write_text("prompt", encoding="utf-8")
    settings = Settings(
        GROQ_API_KEY="test-key",
        DEFAULT_LLM_MODEL="llama-3.1-8b-instant",
        MAX_LLM_RETRIES=1,
        LLM_MIN_INTERVAL_SECONDS=0,
    )
    client = GroqClient(settings, prompts_dir)

    monkeypatch.setattr(
        "book_to_audiovideo.providers.groq_client.httpx.AsyncClient",
        lambda timeout: _FakeClient({}),
    )

    result = anyio.run(client.cleanup_text, "ciao")
    assert result["cleaned_text"] == "ok"
