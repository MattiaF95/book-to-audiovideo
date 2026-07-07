from __future__ import annotations

from collections import defaultdict

from book_to_audiovideo.agents.base import BaseAgent
from book_to_audiovideo.models.domain import MediaPlanItem, PronunciationHint, ToneTag, VoiceAssignment
from book_to_audiovideo.pipeline.context import PipelineContext
from book_to_audiovideo.providers.provider_base import LLMProvider, TTSProvider


class AudioPlanningAgent(BaseAgent):
    stage_name = "audio_planning"

    def __init__(self, llm: LLMProvider, tts: TTSProvider) -> None:
        self.llm = llm
        self.tts = tts

    async def execute(self, context: PipelineContext) -> None:
        if context.state.voice_assignments and context.state.tone_tags and context.state.media_plan:
            return
        available_voices = await self.tts.list_voices()
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

        response = await self.llm.plan_audio(
            {
                "corrected_text": context.state.cleaned_text,
                "context": context.state.text_context,
                "speakers": [self._speaker_payload(speaker) for speaker in context.state.speakers],
                "segments": [self._segment_payload(segment) for segment in context.state.segments],
                "available_voices": [
                    {
                        "voice_id": voice.get("voice_id"),
                        "name": voice.get("name"),
                        "labels": self._compact_labels(voice.get("labels", {})),
                        "source": voice.get("voice_source"),
                    }
                    for voice in candidate_pool
                ],
            }
        )

        candidate_by_id = {voice.get("voice_id"): voice for voice in candidate_pool if voice.get("voice_id")}
        candidate_by_name = {voice.get("name"): voice for voice in candidate_pool if voice.get("name")}

        assignments: list[VoiceAssignment] = []
        for item in response.get("voice_assignments", []):
            enriched_item = dict(item)
            selected = None
            if enriched_item.get("voice_id"):
                selected = candidate_by_id.get(enriched_item["voice_id"])
            if not selected and enriched_item.get("voice_name"):
                selected = candidate_by_name.get(enriched_item["voice_name"])
            if not selected and candidate_pool:
                selected = candidate_pool[0]
            if selected:
                enriched_item["voice_name"] = selected.get("name", enriched_item.get("voice_name"))
                enriched_item["voice_id"] = selected.get("voice_id", enriched_item.get("voice_id"))
                enriched_item["voice_source"] = selected.get("voice_source")
                if selected.get("public_owner_id"):
                    enriched_item["public_owner_id"] = selected.get("public_owner_id")
            assignment = await self.tts.select_voice(enriched_item)
            assignments.append(assignment)

        pronunciation = self._normalize_pronunciation(
            context,
            [PronunciationHint.model_validate(item) for item in response.get("pronunciation", [])],
        )
        tone_tags = self._normalize_tone_tags(
            context,
            [ToneTag.model_validate(item) for item in response.get("tone_tags", [])],
        )
        media_plan = self._normalize_media_plan(
            context,
            [MediaPlanItem.model_validate(item) for item in response.get("media_plan", [])],
        )

        context.state.voice_assignments = assignments
        context.state.pronunciation_overrides = pronunciation
        context.state.tone_tags = tone_tags
        context.state.media_plan = media_plan
        self.write_stage_json(
            context,
            "04_audio_planning.json",
            {
                "voice_assignments": [assignment.model_dump(mode="json") for assignment in assignments],
                "pronunciation": [item.model_dump(mode="json") for item in pronunciation],
                "tone_tags": [item.model_dump(mode="json") for item in tone_tags],
                "media_plan": [item.model_dump(mode="json") for item in media_plan],
            },
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
    def _segment_payload(segment) -> dict[str, object]:
        return {
            "segment_id": segment.segment_id,
            "order_index": segment.order_index,
            "raw_text": segment.raw_text[:240],
            "segment_type": segment.segment_type.value,
            "speaker_hint": segment.speaker_hint,
            "resolved_speaker_id": segment.resolved_speaker_id,
            "emotion_hint": segment.emotion_hint,
        }

    @staticmethod
    def _compact_labels(labels: dict[str, object]) -> dict[str, object]:
        compact: dict[str, object] = {}
        for key, value in labels.items():
            if isinstance(value, str):
                compact[key] = value[:80]
            else:
                compact[key] = value
        return compact

    @staticmethod
    def _build_voice_pool(
        speakers,
        voices: list[dict],
        source: str,
        exclude_voice_ids: set[str] | None = None,
    ) -> list[dict]:
        exclude_voice_ids = exclude_voice_ids or set()
        ranked_voice_ids: list[str] = []
        voice_index = {str(voice.get("voice_id")): voice for voice in voices if voice.get("voice_id")}
        for speaker in speakers:
            matches = sorted(
                (
                    (AudioPlanningAgent._voice_match_score(speaker, voice), str(voice.get("voice_id")))
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
            ranked_voice_ids = [
                str(voice.get("voice_id"))
                for voice in voices
                if voice.get("voice_id") and str(voice.get("voice_id")) not in exclude_voice_ids
            ][:6]
        pool = []
        for voice_id in ranked_voice_ids:
            voice = dict(voice_index[voice_id])
            voice["voice_source"] = source
            voice["public_owner_id"] = voice.get("public_owner_id") or voice.get("user_id")
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
            bucket = AudioPlanningAgent._speaker_bucket(speaker)
            if any(AudioPlanningAgent._voice_match_score(speaker, voice) > 0 for voice in voices):
                bucket_candidates[bucket] += 1
        required_buckets = {AudioPlanningAgent._speaker_bucket(speaker) for speaker in speakers}
        return required_buckets.issubset(bucket_candidates.keys()) and len(voices) >= len(required_buckets)

    @staticmethod
    def _voice_match_score(speaker, voice: dict) -> int:
        labels = voice.get("labels", {}) or {}
        score = 1
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
        if str(speaker.role) == "narrator":
            return "narrator"
        gender = (speaker.gender or "unknown").lower()
        return f"character:{gender}"

    @staticmethod
    def _normalize_pronunciation(context: PipelineContext, items: list[PronunciationHint]) -> list[PronunciationHint]:
        by_segment = {item.segment_id: item for item in items}
        normalized: list[PronunciationHint] = []
        for segment in context.state.segments:
            normalized.append(
                by_segment.get(
                    segment.segment_id,
                    PronunciationHint(
                        segment_id=segment.segment_id,
                        pronunciation_overrides={},
                        phonetic_hints={},
                        problem_terms=[],
                        confidence=0.0,
                    ),
                )
            )
        return normalized

    @staticmethod
    def _normalize_tone_tags(context: PipelineContext, items: list[ToneTag]) -> list[ToneTag]:
        by_segment = {item.segment_id: item for item in items}
        normalized: list[ToneTag] = []
        for segment in context.state.segments:
            normalized.append(
                by_segment.get(
                    segment.segment_id,
                    ToneTag(
                        segment_id=segment.segment_id,
                        tagged_text=segment.raw_text,
                        tags_used=[],
                        tag_confidence=0.0,
                    ),
                )
            )
        return normalized

    @staticmethod
    def _normalize_media_plan(context: PipelineContext, items: list[MediaPlanItem]) -> list[MediaPlanItem]:
        by_segment = {item.segment_id: item for item in items}
        normalized: list[MediaPlanItem] = []
        fallback_keywords = context.state.text_context.get("scene")
        default_query = [str(fallback_keywords).strip()] if fallback_keywords else ["cinematic background"]
        for segment in context.state.segments:
            normalized.append(
                by_segment.get(
                    segment.segment_id,
                    MediaPlanItem(
                        segment_id=segment.segment_id,
                        video_keywords=default_query,
                        sfx_keywords=[],
                        mood=segment.emotion_hint or str(context.state.text_context.get("tone") or "neutral"),
                        scene_type="generic",
                        media_intensity="low",
                        needs_sfx=False,
                        sfx_timeline_hint=None,
                    ),
                )
            )
        return normalized
