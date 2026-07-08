from __future__ import annotations

from collections import defaultdict

from book_to_audiovideo.agents.base import BaseAgent
from book_to_audiovideo.models.domain import VoiceAssignment
from book_to_audiovideo.pipeline.context import PipelineContext
from book_to_audiovideo.providers.provider_base import LLMProvider, TTSProvider


class VoiceCastingAgent(BaseAgent):
    stage_name = "voice_casting"

    def __init__(self, llm: LLMProvider, tts: TTSProvider) -> None:
        self.llm = llm
        self.tts = tts

    async def execute(self, context: PipelineContext) -> None:
        if context.state.voice_assignments:
            return
        available_voices = await self.tts.list_voices()
        # Preferisce prima le voci dell'account, poi amplia alle shared se serve copertura.
        account_pool = self._build_voice_pool(context.state.speakers, available_voices, source="account")
        candidate_pool = account_pool
        if not self._pool_is_sufficient(context.state.speakers, account_pool):
            shared_voices = await self.tts.list_shared_voices()
            shared_pool = self._build_voice_pool(
                context.state.speakers,
                shared_voices,
                source="shared",
                exclude_voice_ids={voice.get("voice_id") for voice in account_pool},
            )
            candidate_pool = self._merge_voice_pools(account_pool, shared_pool)

        response = await self.llm.run_task(
            "voice_casting.md",
            {
                "context": context.state.text_context,
                "speakers": [self._speaker_payload(speaker) for speaker in context.state.speakers],
                "available_voices": [
                    {
                        "voice_id": voice.get("voice_id"),
                        "name": voice.get("name"),
                        "labels": self._compact_labels(voice.get("labels", {})),
                        "source": voice.get("voice_source"),
                    }
                    for voice in candidate_pool
                ],
            },
        )

        candidate_by_id = {voice.get("voice_id"): voice for voice in candidate_pool if voice.get("voice_id")}
        candidate_by_name = {voice.get("name"): voice for voice in candidate_pool if voice.get("name")}
        by_speaker_id = {str(item.get("speaker_id")): item for item in response.get("voice_assignments", []) if item.get("speaker_id")}
        assignments: list[VoiceAssignment] = []
        for speaker in context.state.speakers:
            item = dict(by_speaker_id.get(speaker.speaker_id, {}))
            if not item:
                item = {
                    "speaker_id": speaker.speaker_id,
                    "voice_name": speaker.name,
                }
            item.setdefault("speaker_id", speaker.speaker_id)
            item.setdefault("voice_name", speaker.name)
            selected = None
            if item.get("voice_id"):
                selected = candidate_by_id.get(item["voice_id"])
            if not selected and item.get("voice_name"):
                selected = candidate_by_name.get(item["voice_name"])
            if not selected and candidate_pool:
                selected = max(
                    candidate_pool,
                    key=lambda voice: self._voice_match_score(speaker, voice),
                )
            if selected:
                item["voice_name"] = selected.get("name", item.get("voice_name"))
                item["voice_id"] = selected.get("voice_id", item.get("voice_id"))
            assignments.append(await self.tts.select_voice(item))
        context.state.voice_assignments = assignments
        self.write_stage_json(
            context,
            "08_voice_casting.json",
            {"voice_assignments": [assignment.model_dump(mode="json") for assignment in assignments]},
        )

    @staticmethod
    def _speaker_payload(speaker) -> dict[str, object]:
        return {
            "speaker_id": speaker.speaker_id,
            "name": speaker.name,
            "role": speaker.role,
            "gender": speaker.gender,
            "continuity_key": speaker.continuity_key,
            "preferred_voice_constraints": speaker.preferred_voice_constraints[:4],
        }

    @staticmethod
    def _compact_labels(labels: dict[str, object]) -> dict[str, object]:
        compact: dict[str, object] = {}
        for key, value in labels.items():
            compact[key] = value[:80] if isinstance(value, str) else value
        return compact

    @staticmethod
    def _build_voice_pool(speakers, voices: list[dict], source: str, exclude_voice_ids: set[str] | None = None) -> list[dict]:
        exclude_voice_ids = exclude_voice_ids or set()
        ranked_voice_ids: list[str] = []
        voice_index = {str(voice.get("voice_id")): voice for voice in voices if voice.get("voice_id")}
        for speaker in speakers:
            matches = sorted(
                (
                    (VoiceCastingAgent._voice_match_score(speaker, voice), str(voice.get("voice_id")))
                    for voice in voices
                    if voice.get("voice_id") and str(voice.get("voice_id")) not in exclude_voice_ids
                ),
                reverse=True,
            )
            kept = 0
            for score, voice_id in matches:
                if score <= 0:
                    continue
                if voice_id not in ranked_voice_ids:
                    ranked_voice_ids.append(voice_id)
                kept += 1
                if kept >= 3:
                    break
        if not ranked_voice_ids:
            # Fallback finale: tieni un piccolo pool anche senza match forti.
            ranked_voice_ids = [
                str(voice.get("voice_id"))
                for voice in voices
                if voice.get("voice_id") and str(voice.get("voice_id")) not in exclude_voice_ids
            ][:6]
        pool = []
        for voice_id in ranked_voice_ids:
            voice = dict(voice_index[voice_id])
            voice["voice_source"] = source
            pool.append(voice)
        return pool

    @staticmethod
    def _merge_voice_pools(account_pool: list[dict], shared_pool: list[dict]) -> list[dict]:
        merged = []
        seen_voice_ids: set[str] = set()
        for voice in [*account_pool, *shared_pool]:
            voice_id = str(voice.get("voice_id"))
            if not voice_id or voice_id in seen_voice_ids:
                continue
            seen_voice_ids.add(voice_id)
            merged.append(voice)
        return merged

    @staticmethod
    def _pool_is_sufficient(speakers, voices: list[dict]) -> bool:
        if not voices:
            return False
        bucket_candidates: dict[str, int] = defaultdict(int)
        for speaker in speakers:
            bucket = VoiceCastingAgent._speaker_bucket(speaker)
            if any(VoiceCastingAgent._voice_match_score(speaker, voice) > 0 for voice in voices):
                bucket_candidates[bucket] += 1
        required_buckets = {VoiceCastingAgent._speaker_bucket(speaker) for speaker in speakers}
        return required_buckets.issubset(bucket_candidates.keys()) and len(voices) >= len(required_buckets)

    @staticmethod
    def _voice_match_score(speaker, voice: dict) -> int:
        labels = voice.get("labels", {}) or {}
        score = 1
        # Il punteggio combina ruolo, genere e vincoli testuali del parlante.
        speaker_gender = (speaker.gender or "").lower()
        voice_gender = str(labels.get("gender", "")).lower()
        if speaker_gender and voice_gender:
            score += 4 if speaker_gender == voice_gender else -3
        role = str(speaker.role)
        use_case = str(labels.get("use_case", "")).lower()
        if role == "narrator" and use_case in {"narrative_story", "informative_educational", "advertisement", "conversational"}:
            score += 3
        if role == "character" and use_case in {"conversational", "social_media", "entertainment_tv"}:
            score += 3
        constraints = [str(item).lower() for item in speaker.preferred_voice_constraints]
        haystack = " ".join(
            [
                str(voice.get("name", "")).lower(),
                str(voice.get("description", "")).lower(),
                " ".join(f"{key}:{value}".lower() for key, value in labels.items()),
            ]
        )
        for constraint in constraints:
            if constraint and constraint in haystack:
                score += 2
        return score

    @staticmethod
    def _speaker_bucket(speaker) -> str:
        role = str(speaker.role)
        gender = (speaker.gender or "neutral").lower()
        return f"{role}:{gender}"
