from pathlib import Path

import anyio

from book_to_audiovideo.agents.voice_assignment_agent import VoiceAssignmentAgent
from book_to_audiovideo.config import Settings
from book_to_audiovideo.models.domain import Speaker, VoiceAssignment
from book_to_audiovideo.models.state import PipelineState
from book_to_audiovideo.pipeline.context import PipelineContext


def test_voice_assignment_keeps_anchor() -> None:
    assignment = VoiceAssignment(
        speaker_id="hero",
        voice_id="voice-1",
        voice_name="Hero Voice",
        delivery_style="dramatic",
        continuity_anchor="hero",
    )
    assert assignment.continuity_anchor == "hero"


class _FakeLLMProvider:
    def __init__(self, assignments: list[dict]) -> None:
        self.assignments = assignments
        self.payloads: list[dict] = []

    async def cleanup_text(self, text: str) -> dict:
        raise NotImplementedError

    async def analyze_text(self, chunk_text: str) -> dict:
        raise NotImplementedError

    async def extract_segments(self, chunk_text: str) -> dict:
        raise NotImplementedError

    async def resolve_speaker(self, payload: dict) -> dict:
        raise NotImplementedError

    async def assign_voice(self, payload: dict) -> dict:
        self.payloads.append(payload)
        return {"assignments": self.assignments}

    async def extract_pronunciation_hints(self, payload: dict) -> dict:
        raise NotImplementedError

    async def add_tone_tags(self, payload: dict) -> dict:
        raise NotImplementedError

    async def plan_media_keywords(self, payload: dict) -> dict:
        raise NotImplementedError


class _FakeTTSProvider:
    def __init__(self, account_voices: list[dict], shared_voices: list[dict] | None = None) -> None:
        self.account_voices = account_voices
        self.shared_voices = shared_voices or []
        self.list_shared_calls = 0
        self.selected_payloads: list[dict] = []

    async def list_voices(self) -> list[dict]:
        return self.account_voices

    async def list_shared_voices(self) -> list[dict]:
        self.list_shared_calls += 1
        return self.shared_voices

    async def ensure_public_voice_available(self, descriptor: dict) -> str:
        if descriptor.get("voice_source") == "shared":
            return f"saved-{descriptor['voice_id']}"
        return descriptor["voice_id"]

    async def select_voice(self, payload: dict) -> VoiceAssignment:
        self.selected_payloads.append(payload)
        voice_id = await self.ensure_public_voice_available(payload)
        return VoiceAssignment(
            speaker_id=payload["speaker_id"],
            voice_id=voice_id,
            voice_name=payload["voice_name"],
            delivery_style=payload.get("delivery_style", "natural"),
            continuity_anchor=payload.get("continuity_anchor", payload["speaker_id"]),
            tts_prompt_tags=payload.get("tts_prompt_tags", []),
        )


def _make_state(tmp_path: Path) -> PipelineState:
    return PipelineState(
        job_id="job-1",
        book_id="book-1",
        source_path=str(tmp_path / "source.txt"),
        source_name="source.txt",
        source_type=".txt",
        artifact_dir=str(tmp_path / "job"),
        speakers=[
            Speaker(
                speaker_id="narrator",
                name="Narrator",
                role="narrator",
                gender="neutral",
                continuity_key="narrator",
                preferred_voice_constraints=["clear"],
            ),
            Speaker(
                speaker_id="heroine",
                name="Giulia",
                role="character",
                gender="female",
                continuity_key="giulia",
                preferred_voice_constraints=["young"],
            ),
            Speaker(
                speaker_id="villain",
                name="Mysterious Man",
                role="character",
                gender="male",
                continuity_key="villain",
                preferred_voice_constraints=["mysterious"],
            ),
        ],
    )


def test_voice_assignment_uses_account_voices_without_shared_lookup(tmp_path: Path) -> None:
    settings = Settings(OUTPUT_DIR=tmp_path, CACHE_DIR=tmp_path / "cache")
    state = _make_state(tmp_path)
    context = PipelineContext(settings=settings, state=state)
    account_voices = [
        {"voice_id": "acc-narr", "name": "Account Narrator", "labels": {"gender": "neutral", "use_case": "informative_educational"}},
        {"voice_id": "acc-f", "name": "Account Female", "labels": {"gender": "female", "use_case": "social_media", "age": "young"}},
        {"voice_id": "acc-m", "name": "Account Male", "labels": {"gender": "male", "use_case": "conversational", "descriptive": "mysterious"}},
    ]
    llm = _FakeLLMProvider(
        [
            {"speaker_id": "narrator", "voice_id": "acc-narr", "voice_name": "Account Narrator", "delivery_style": "narrative_story", "continuity_anchor": "narrator"},
            {"speaker_id": "heroine", "voice_id": "acc-f", "voice_name": "Account Female", "delivery_style": "conversational", "continuity_anchor": "giulia"},
            {"speaker_id": "villain", "voice_id": "acc-m", "voice_name": "Account Male", "delivery_style": "dramatic", "continuity_anchor": "villain"},
        ]
    )
    tts = _FakeTTSProvider(account_voices=account_voices)

    anyio.run(VoiceAssignmentAgent(llm, tts).execute, context)

    assert tts.list_shared_calls == 0
    assert {item.voice_id for item in context.state.voice_assignments} == {"acc-narr", "acc-f", "acc-m"}


def test_voice_assignment_fetches_shared_only_when_account_pool_is_insufficient(tmp_path: Path) -> None:
    settings = Settings(OUTPUT_DIR=tmp_path, CACHE_DIR=tmp_path / "cache")
    state = _make_state(tmp_path)
    context = PipelineContext(settings=settings, state=state)
    account_voices = [
        {"voice_id": "acc-narr", "name": "Account Narrator", "labels": {"gender": "neutral", "use_case": "informative_educational"}}
    ]
    shared_voices = [
        {"voice_id": "pub-f", "name": "Public Female", "labels": {"gender": "female", "use_case": "social_media", "age": "young"}, "public_owner_id": "owner-f"},
        {"voice_id": "pub-m", "name": "Public Male", "labels": {"gender": "male", "use_case": "conversational", "descriptive": "mysterious"}, "public_owner_id": "owner-m"},
    ]
    llm = _FakeLLMProvider(
        [
            {"speaker_id": "narrator", "voice_id": "acc-narr", "voice_name": "Account Narrator", "delivery_style": "narrative_story", "continuity_anchor": "narrator"},
            {"speaker_id": "heroine", "voice_id": "pub-f", "voice_name": "Public Female", "delivery_style": "conversational", "continuity_anchor": "giulia"},
            {"speaker_id": "villain", "voice_id": "pub-m", "voice_name": "Public Male", "delivery_style": "dramatic", "continuity_anchor": "villain"},
        ]
    )
    tts = _FakeTTSProvider(account_voices=account_voices, shared_voices=shared_voices)

    anyio.run(VoiceAssignmentAgent(llm, tts).execute, context)

    assert tts.list_shared_calls == 1
    assert {item.voice_id for item in context.state.voice_assignments} == {"acc-narr", "saved-pub-f", "saved-pub-m"}
    assert any(payload.get("voice_source") == "shared" for payload in tts.selected_payloads)
