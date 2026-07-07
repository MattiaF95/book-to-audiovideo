from pathlib import Path

import anyio

from book_to_audiovideo.agents.base import BaseAgent
from book_to_audiovideo.agents.dialogue_segmentation_agent import DialogueSegmentationAgent
from book_to_audiovideo.agents.manifest_agent import ManifestAgent
from book_to_audiovideo.agents.narrative_context_agent import NarrativeContextAgent
from book_to_audiovideo.agents.speaker_attribution_agent import SpeakerAttributionAgent
from book_to_audiovideo.agents.speaker_registry_agent import SpeakerRegistryAgent
from book_to_audiovideo.agents.text_cleanup_agent import TextCleanupAgent
from book_to_audiovideo.agents.audio_planning_agent import AudioPlanningAgent
from book_to_audiovideo.agents.story_structure_agent import StoryStructureAgent
from book_to_audiovideo.agents.text_preparation_agent import TextPreparationAgent
from book_to_audiovideo.config import Settings
from book_to_audiovideo.models.domain import MediaPlanItem, PronunciationHint, Segment, SegmentType, Speaker, ToneTag, VoiceAssignment
from book_to_audiovideo.models.state import PipelineState
from book_to_audiovideo.pipeline.context import PipelineContext


class _FakeLLMProvider:
    def __init__(self, prepare_response: dict | None = None, structure_response: dict | None = None, plan_response: dict | None = None) -> None:
        self.prepare_response = prepare_response or {}
        self.structure_response = structure_response or {}
        self.plan_response = plan_response or {}
        self.task_responses: dict[str, dict] = {}
        self.calls: list[tuple[str, dict]] = []

    async def run_task(self, prompt_name: str, payload: dict) -> dict:
        self.calls.append((prompt_name, payload))
        return self.task_responses.get(prompt_name, {})

    async def prepare_text(self, payload: dict) -> dict:
        self.calls.append(("prepare_text", payload))
        return self.prepare_response

    async def structure_story(self, payload: dict) -> dict:
        self.calls.append(("structure_story", payload))
        return self.structure_response

    async def plan_audio(self, payload: dict) -> dict:
        self.calls.append(("plan_audio", payload))
        return self.plan_response


class _FakeTTSProvider:
    def __init__(self, account_voices: list[dict]) -> None:
        self.account_voices = account_voices
        self.shared_voices: list[dict] = []
        self.selected_payloads: list[dict] = []

    async def list_voices(self) -> list[dict]:
        return self.account_voices

    async def list_shared_voices(self) -> list[dict]:
        return self.shared_voices

    async def ensure_public_voice_available(self, descriptor: dict) -> str:
        return descriptor["voice_id"]

    async def select_voice(self, payload: dict) -> VoiceAssignment:
        self.selected_payloads.append(payload)
        return VoiceAssignment(
            speaker_id=payload["speaker_id"],
            voice_id=payload["voice_id"],
            voice_name=payload["voice_name"],
            delivery_style=payload.get("delivery_style", "natural"),
            continuity_anchor=payload.get("continuity_anchor", payload["speaker_id"]),
            tts_prompt_tags=payload.get("tts_prompt_tags", []),
        )


class _NoopAgent(BaseAgent):
    stage_name = "ingestion"

    async def execute(self, context: PipelineContext) -> None:
        context.state.raw_text = "test"


def test_text_preparation_agent_writes_context(tmp_path: Path) -> None:
    settings = Settings(OUTPUT_DIR=tmp_path, CACHE_DIR=tmp_path / "cache")
    state = PipelineState(
        job_id="job-1",
        book_id="book-1",
        source_path=str(tmp_path / "source.txt"),
        source_name="source.txt",
        source_type=".txt",
        artifact_dir=str(tmp_path / "job"),
        raw_text="testo con errore",
    )
    context = PipelineContext(settings=settings, state=state)
    provider = _FakeLLMProvider(
        prepare_response={
            "corrected_text": "testo con errore corretto",
            "corrections": [],
            "context": {"scene": "tensione", "emotions": ["ansia"], "tone": "drammatico"},
            "warnings": [],
        }
    )

    anyio.run(TextPreparationAgent(provider).execute, context)

    assert provider.calls[0][0] == "prepare_text"
    assert context.state.cleaned_text == "testo con errore corretto"
    assert context.state.text_context["scene"] == "tensione"


def test_story_structure_agent_keeps_single_speaker_turns(tmp_path: Path) -> None:
    settings = Settings(OUTPUT_DIR=tmp_path, CACHE_DIR=tmp_path / "cache")
    state = PipelineState(
        job_id="job-1",
        book_id="book-1",
        source_path=str(tmp_path / "source.txt"),
        source_name="source.txt",
        source_type=".txt",
        artifact_dir=str(tmp_path / "job"),
        cleaned_text="«Ciao» disse Marco. Poi il narratore continua.",
        text_context={"scene": "dialogo"},
    )
    context = PipelineContext(settings=settings, state=state)
    provider = _FakeLLMProvider(
        structure_response={
            "speakers": [
                {
                    "speaker_id": "narrator",
                    "name": "Narrator",
                    "role": "narrator",
                    "gender": "neutral",
                    "continuity_key": "narrator",
                    "preferred_voice_constraints": ["clear"],
                },
                {
                    "speaker_id": "marco",
                    "name": "Marco",
                    "role": "character",
                    "gender": "male",
                    "continuity_key": "marco",
                    "preferred_voice_constraints": ["warm"],
                },
            ],
            "segments": [
                {
                    "segment_id": "seg-1",
                    "order_index": 1,
                    "raw_text": "«Ciao» disse Marco.",
                    "segment_type": "dialogue",
                    "speaker_hint": "Marco",
                    "resolved_speaker_id": "marco",
                    "start_offset": 0,
                    "end_offset": 20,
                    "emotion_hint": "calmo",
                    "importance_score": 0.8,
                },
                {
                    "segment_id": "seg-2",
                    "order_index": 2,
                    "raw_text": "Poi il narratore continua.",
                    "segment_type": "narration",
                    "speaker_hint": "narratore",
                    "resolved_speaker_id": "narrator",
                    "start_offset": 21,
                    "end_offset": 50,
                    "emotion_hint": "neutro",
                    "importance_score": 0.6,
                },
            ],
        }
    )

    anyio.run(StoryStructureAgent(provider).execute, context)

    assert [speaker.speaker_id for speaker in context.state.speakers] == ["narrator", "marco"]
    assert [segment.order_index for segment in context.state.segments] == [1, 2]
    assert all(segment.chunk_id == "book-1" for segment in context.state.segments)


def test_audio_planning_agent_assigns_voice_and_media(tmp_path: Path) -> None:
    settings = Settings(OUTPUT_DIR=tmp_path, CACHE_DIR=tmp_path / "cache")
    state = PipelineState(
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
                speaker_id="marco",
                name="Marco",
                role="character",
                gender="male",
                continuity_key="marco",
                preferred_voice_constraints=["warm"],
            ),
        ],
        segments=[
            Segment(
                segment_id="seg-1",
                chunk_id="book-1",
                order_index=1,
                raw_text="«Ciao» disse Marco.",
                segment_type=SegmentType.dialogue,
                speaker_hint="Marco",
                resolved_speaker_id="marco",
                start_offset=0,
                end_offset=20,
                emotion_hint="calmo",
                importance_score=0.8,
            )
        ],
        cleaned_text="«Ciao» disse Marco.",
        text_context={"scene": "dialogo"},
    )
    context = PipelineContext(settings=settings, state=state)
    llm = _FakeLLMProvider(
        plan_response={
            "voice_assignments": [
                {
                    "speaker_id": "narrator",
                    "voice_id": "v-narr",
                    "voice_name": "Narrator Voice",
                    "delivery_style": "narrative",
                    "tts_prompt_tags": ["clear"],
                    "continuity_anchor": "narrator",
                },
                {
                    "speaker_id": "marco",
                    "voice_id": "v-marco",
                    "voice_name": "Marco Voice",
                    "delivery_style": "warm",
                    "tts_prompt_tags": ["warm"],
                    "continuity_anchor": "marco",
                },
            ],
            "pronunciation": [
                {"segment_id": "seg-1", "pronunciation_overrides": {}, "phonetic_hints": {}, "problem_terms": [], "confidence": 0.9}
            ],
            "tone_tags": [
                {"segment_id": "seg-1", "tagged_text": "«Ciao» disse Marco.", "tags_used": [], "tag_confidence": 0.8}
            ],
            "media_plan": [
                {
                    "segment_id": "seg-1",
                    "video_keywords": ["room"],
                    "sfx_keywords": [],
                    "mood": "calmo",
                    "scene_type": "interior",
                    "media_intensity": "low",
                    "needs_sfx": False,
                    "sfx_timeline_hint": None,
                }
            ],
        }
    )
    tts = _FakeTTSProvider(
        [
            {"voice_id": "v-narr", "name": "Narrator Voice", "labels": {"gender": "neutral", "use_case": "narrative_story"}},
            {"voice_id": "v-marco", "name": "Marco Voice", "labels": {"gender": "male", "use_case": "conversational"}},
        ]
    )

    anyio.run(AudioPlanningAgent(llm, tts).execute, context)

    assert [item.speaker_id for item in context.state.voice_assignments] == ["narrator", "marco"]
    assert context.state.media_plan[0].segment_id == "seg-1"
    assert context.state.tone_tags[0].segment_id == "seg-1"
    assert context.state.pronunciation_overrides[0].segment_id == "seg-1"


def test_each_agent_writes_stage_manifest_and_final_manifest(tmp_path: Path) -> None:
    settings = Settings(OUTPUT_DIR=tmp_path, CACHE_DIR=tmp_path / "cache")
    state = PipelineState(
        job_id="job-1",
        book_id="book-1",
        source_path=str(tmp_path / "source.txt"),
        source_name="source.txt",
        source_type=".txt",
        artifact_dir=str(tmp_path / "job"),
    )
    context = PipelineContext(settings=settings, state=state)

    anyio.run(_NoopAgent().run, context)
    anyio.run(ManifestAgent().run, context)

    assert (tmp_path / "job" / "manifests" / "ingestion.json").exists()
    assert (tmp_path / "job" / "manifests" / "manifest.json").exists()
    assert (tmp_path / "job" / "manifest.json").exists()


def test_refactored_narrative_agents_build_stable_segments_and_speakers(tmp_path: Path) -> None:
    settings = Settings(OUTPUT_DIR=tmp_path, CACHE_DIR=tmp_path / "cache")
    state = PipelineState(
        job_id="job-1",
        book_id="book-1",
        source_path=str(tmp_path / "source.txt"),
        source_name="source.txt",
        source_type=".txt",
        artifact_dir=str(tmp_path / "job"),
        raw_text="Testo",
    )
    context = PipelineContext(settings=settings, state=state)
    provider = _FakeLLMProvider()
    provider.task_responses = {
        "text_cleanup.md": {"corrected_text": "«Ciao» disse Marco. Poi il narratore continua.", "corrections": [], "warnings": []},
        "narrative_context.md": {"context": {"scene": "dialogo", "tone": "calmo", "setting": "interno", "time_period": None}},
        "dialogue_segmentation.md": {
            "segments": [
                {
                    "segment_id": "seg-1",
                    "order_index": 1,
                    "raw_text": "«Ciao» disse Marco.",
                    "segment_type": "dialogue",
                    "start_offset": 0,
                    "end_offset": 20,
                },
                {
                    "segment_id": "seg-2",
                    "order_index": 2,
                    "raw_text": "Poi il narratore continua.",
                    "segment_type": "narration",
                    "start_offset": 21,
                    "end_offset": 50,
                },
            ]
        },
        "speaker_registry.md": {
            "speakers": [
                {
                    "speaker_id": "narrator",
                    "name": "Narrator",
                    "role": "narrator",
                    "gender": None,
                    "continuity_key": "narrator",
                    "preferred_voice_constraints": ["clear"],
                },
                {
                    "speaker_id": "marco",
                    "name": "Marco",
                    "role": "character",
                    "gender": "male",
                    "continuity_key": "marco",
                    "preferred_voice_constraints": ["warm"],
                },
            ]
        },
        "speaker_attribution.md": {
            "assignments": [
                {"segment_id": "seg-1", "speaker_hint": "Marco", "resolved_speaker_id": "marco"},
                {"segment_id": "seg-2", "speaker_hint": None, "resolved_speaker_id": "narrator"},
            ]
        },
    }

    anyio.run(TextCleanupAgent(provider).execute, context)
    anyio.run(NarrativeContextAgent(provider).execute, context)
    anyio.run(DialogueSegmentationAgent(provider).execute, context)
    anyio.run(SpeakerRegistryAgent(provider).execute, context)
    anyio.run(SpeakerAttributionAgent(provider).execute, context)

    assert context.state.cleaned_text.startswith("«Ciao»")
    assert context.state.text_context["scene"] == "dialogo"
    assert [segment.resolved_speaker_id for segment in context.state.segments] == ["marco", "narrator"]
    assert [speaker.speaker_id for speaker in context.state.speakers] == ["narrator", "marco"]
