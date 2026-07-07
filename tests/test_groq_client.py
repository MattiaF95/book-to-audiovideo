from pathlib import Path

import anyio

from book_to_audiovideo.config import Settings
from book_to_audiovideo.providers import groq_client as groq_client_module
from book_to_audiovideo.providers.groq_client import GroqClient


class _FakeDelta:
    def __init__(self, content: str | None) -> None:
        self.content = content


class _FakeChoice:
    def __init__(self, content: str | None) -> None:
        self.delta = _FakeDelta(content)


class _FakeChunk:
    def __init__(self, content: str | None) -> None:
        self.choices = [_FakeChoice(content)]


class _FakeStream:
    def __init__(self, chunks: list[_FakeChunk]) -> None:
        self._chunks = chunks

    def __iter__(self):
        return iter(self._chunks)


class _FakeCompletions:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        assert kwargs["model"] == "qwen/qwen3.6-27b"
        assert kwargs["temperature"] == 0.6
        assert kwargs["max_completion_tokens"] == 900
        assert kwargs["top_p"] == 0.95
        assert kwargs["reasoning_effort"] == "default"
        assert kwargs["stream"] is True
        assert kwargs["response_format"] == {"type": "json_object"}
        assert kwargs["messages"][0]["content"].startswith("prompt\nINPUT_JSON:\n")
        return _FakeStream(
            [
                _FakeChunk('{"corrected_text":"'),
                _FakeChunk("ok"),
                _FakeChunk('","corrections":[],"warnings":[]}'),
            ]
        )


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
