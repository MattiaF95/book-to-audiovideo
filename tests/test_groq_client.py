from pathlib import Path

import anyio

from book_to_audiovideo.config import Settings
from book_to_audiovideo.providers import groq_client as groq_client_module
from book_to_audiovideo.providers.groq_client import GroqClient


class _FakeCompletions:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        assert kwargs["model"] == "qwen/qwen3.6-27b"
        assert kwargs["temperature"] == 0.6
        assert kwargs["max_completion_tokens"] == 900
        assert kwargs["top_p"] == 0.95
        assert kwargs["stream"] is False
        assert kwargs["response_format"] == {"type": "json_object"}
        assert kwargs["messages"][0]["content"].startswith("prompt\nINPUT_JSON:\n")
        return _FakeCompletion('{"corrected_text":"ok","corrections":[],"warnings":[]}')


class _FakeMessage:
    def __init__(self, content: str) -> None:
        self.content = content


class _FakeChoice:
    def __init__(self, content: str) -> None:
        self.message = _FakeMessage(content)


class _FakeCompletion:
    def __init__(self, content: str) -> None:
        self.choices = [_FakeChoice(content)]


class _FakeChat:
    def __init__(self) -> None:
        self.completions = _FakeCompletions()


class _FakeGroq:
    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key
        self.chat = _FakeChat()


def test_groq_client_returns_structured_json(monkeypatch, tmp_path: Path) -> None:
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()
    (prompts_dir / "text_cleanup.md").write_text("prompt", encoding="utf-8")
    settings = Settings(
        GROQ_API_KEY="test-key",
        DEFAULT_LLM_MODEL="qwen/qwen3.6-27b",
        MAX_LLM_RETRIES=1,
        LLM_MIN_INTERVAL_SECONDS=0,
    )
    client = GroqClient(settings, prompts_dir)

    monkeypatch.setattr(groq_client_module, "Groq", _FakeGroq)

    result = anyio.run(client.run_task, "text_cleanup.md", {"text": "ciao"})
    assert result["corrected_text"] == "ok"


class _FakeResponse:
    def __init__(self, status_code: int, payload: dict[str, object]) -> None:
        self.status_code = status_code
        self._payload = payload
        self.text = '{"choices":[{"message":{"content":"{\\"corrected_text\\":\\"ok\\",\\"corrections\\":[],\\"warnings\\":[]}"}}]}'

    @property
    def is_error(self) -> bool:
        return self.status_code >= 400

    def json(self) -> dict[str, object]:
        return self._payload


class _FakeAsyncClient:
    def __init__(self, *args, **kwargs) -> None:
        self.calls: list[dict[str, object]] = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    async def post(self, path: str, headers: dict[str, str], json: dict[str, object]):
        self.calls.append({"path": path, "headers": headers, "json": json})
        return _FakeResponse(
            200,
            {"choices": [{"message": {"content": '{"corrected_text":"ok","corrections":[],"warnings":[]}'}}]},
        )


def test_groq_client_http_fallback(monkeypatch, tmp_path: Path) -> None:
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()
    (prompts_dir / "text_cleanup.md").write_text("prompt", encoding="utf-8")
    settings = Settings(
        GROQ_API_KEY="test-key",
        DEFAULT_LLM_MODEL="qwen/qwen3.6-27b",
        MAX_LLM_RETRIES=1,
        LLM_MIN_INTERVAL_SECONDS=0,
    )
    client = GroqClient(settings, prompts_dir)

    monkeypatch.setattr(groq_client_module, "Groq", None)
    monkeypatch.setattr(groq_client_module.httpx, "AsyncClient", _FakeAsyncClient)

    result = anyio.run(client.run_task, "text_cleanup.md", {"text": "ciao"})
    assert result["corrected_text"] == "ok"
