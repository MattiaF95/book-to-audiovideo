from pathlib import Path

import anyio

from book_to_audiovideo.config import Settings
from book_to_audiovideo.providers import groq_client as groq_client_module
from book_to_audiovideo.providers.groq_client import GroqClient


class _FakeCompletions:
    def __init__(self, content: str) -> None:
        self.calls: list[dict] = []
        self.content = content

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return _FakeCompletion(self.content)


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
    def __init__(self, content: str) -> None:
        self.completions = _FakeCompletions(content)


class _FakeGroq:
    last_instance: "_FakeGroq | None" = None

    def __init__(self, api_key: str | None = None, content: str = '{"corrected_text":"ok","corrections":[],"warnings":[]}') -> None:
        self.api_key = api_key
        self.chat = _FakeChat(content)
        type(self).last_instance = self


class _NarrativeGroq(_FakeGroq):
    def __init__(self, api_key: str | None = None) -> None:
        super().__init__(
            api_key=api_key,
            content='{"context":{"scene":"dialogo","tone":"calmo","setting":"interno","time_period":null}}',
        )


class _DialogueGroq(_FakeGroq):
    def __init__(self, api_key: str | None = None) -> None:
        super().__init__(
            api_key=api_key,
            content='<think>ragionamento interno</think>```json\n{"segments":[{"segment_id":"seg-1","order_index":1,"raw_text":"Ciao","segment_type":"dialogue","start_offset":0,"end_offset":4}]}\n```',
        )


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
    call = _FakeGroq.last_instance.chat.completions.calls[0]  # type: ignore[union-attr]
    assert call["response_format"] == {"type": "json_object"}
    assert call["reasoning_effort"] == "none"


def test_groq_client_enables_parsed_reasoning_only_for_narrative_context(monkeypatch, tmp_path: Path) -> None:
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()
    (prompts_dir / "narrative_context.md").write_text("prompt", encoding="utf-8")
    settings = Settings(
        GROQ_API_KEY="test-key",
        DEFAULT_LLM_MODEL="qwen/qwen3.6-27b",
        MAX_LLM_RETRIES=1,
        LLM_MIN_INTERVAL_SECONDS=0,
    )
    client = GroqClient(settings, prompts_dir)

    monkeypatch.setattr(groq_client_module, "Groq", _NarrativeGroq)

    result = anyio.run(client.run_task, "narrative_context.md", {"corrected_text": "ciao"})
    assert result["context"]["scene"] == "dialogo"

    call = _NarrativeGroq.last_instance.chat.completions.calls[0]  # type: ignore[union-attr]
    assert call["model"] == "qwen/qwen3.6-27b"
    assert call["reasoning_effort"] == "default"
    assert call["reasoning_format"] == "parsed"
    assert call["response_format"] == {"type": "json_object"}
    assert call["max_completion_tokens"] == 2200


def test_groq_client_disables_reasoning_and_strips_wrappers(monkeypatch, tmp_path: Path) -> None:
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()
    (prompts_dir / "dialogue_segmentation.md").write_text("prompt", encoding="utf-8")
    settings = Settings(
        GROQ_API_KEY="test-key",
        DEFAULT_LLM_MODEL="qwen/qwen3.6-27b",
        MAX_LLM_RETRIES=1,
        LLM_MIN_INTERVAL_SECONDS=0,
    )
    client = GroqClient(settings, prompts_dir)

    monkeypatch.setattr(groq_client_module, "Groq", _DialogueGroq)

    result = anyio.run(
        client.run_task,
        "dialogue_segmentation.md",
        {"corrected_text": "Ciao", "context": {"scene": "dialogo"}},
    )
    assert result["segments"][0]["segment_id"] == "seg-1"

    call = _DialogueGroq.last_instance.chat.completions.calls[0]  # type: ignore[union-attr]
    assert call["reasoning_effort"] == "none"
    assert "reasoning_format" not in call
    assert call["response_format"] == {"type": "json_object"}


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
