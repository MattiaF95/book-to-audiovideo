from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx

from book_to_audiovideo.config import Settings
from book_to_audiovideo.models.domain import TTSOutput, VoiceAssignment
from book_to_audiovideo.pipeline.errors import ProviderError
from book_to_audiovideo.providers.provider_base import TTSProvider
from book_to_audiovideo.utils.retry import retryable


class ElevenLabsClient(TTSProvider):
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.base_url = "https://api.elevenlabs.io/v1"
        self.model_fallbacks = [settings.default_tts_model, "eleven_turbo_v2_5", "eleven_multilingual_v2"]
        self.stitching_models = {"eleven_turbo_v2_5", "eleven_multilingual_v2"}

    def _headers(self) -> dict[str, str]:
        return {
            "xi-api-key": self.settings.elevenlabs_api_key,
            "Accept": "application/json",
        }

    @staticmethod
    def _limit_history_ids(values: list[str] | None) -> list[str]:
        return (values or [])[-3:]

    def _supports_stitching(self, model_id: str) -> bool:
        return model_id in self.stitching_models and model_id != "eleven_v3"

    @staticmethod
    def _response_history_item_id(response: httpx.Response) -> str | None:
        for header_name in ("history-item-id", "history_item_id", "history-id"):
            value = response.headers.get(header_name)
            if value:
                return value
        return None

    @retryable()
    async def list_voices(self) -> list[dict[str, Any]]:
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.get(f"{self.base_url}/voices", headers=self._headers())
        except httpx.HTTPError as exc:
            raise ProviderError(f"ElevenLabs rete/DNS non raggiungibile: {exc}") from exc
        if response.status_code >= 400:
            raise ProviderError(f"ElevenLabs voices errore {response.status_code}: {response.text}")
        return response.json().get("voices", [])

    @retryable()
    async def list_shared_voices(self) -> list[dict[str, Any]]:
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.get(
                    f"{self.base_url}/shared-voices",
                    headers=self._headers(),
                    params={"page_size": 100},
                )
        except httpx.HTTPError as exc:
            raise ProviderError(f"ElevenLabs rete/DNS non raggiungibile: {exc}") from exc
        if response.status_code >= 400:
            raise ProviderError(f"ElevenLabs shared voices errore {response.status_code}: {response.text}")
        return response.json().get("voices", [])

    async def ensure_public_voice_available(self, descriptor: dict[str, Any]) -> str:
        if descriptor.get("voice_source") == "account" and descriptor.get("voice_id"):
            return descriptor["voice_id"]
        account_voices = await self.list_voices()
        target_name = (descriptor.get("voice_name") or "").strip()
        target_voice_id = descriptor.get("voice_id")
        for voice in account_voices:
            if target_voice_id and voice.get("voice_id") == target_voice_id:
                return target_voice_id
            if target_name and voice.get("name") == target_name:
                return str(voice.get("voice_id"))
        voices = await self.list_shared_voices()
        target = None
        for voice in voices:
            if target_voice_id and voice.get("voice_id") == target_voice_id:
                target = voice
                break
            if target_name and voice.get("name") == target_name:
                target = voice
                break
        if not target:
            raise ProviderError(f"Voce pubblica non trovata: {target_name}")
        public_owner_id = target.get("public_owner_id") or target.get("user_id")
        public_voice_id = target.get("voice_id")
        if not public_owner_id or not public_voice_id:
            raise ProviderError(f"Metadati voce pubblica incompleti per {target_name or public_voice_id}")
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                add_response = await client.post(
                    f"{self.base_url}/voices/add/{public_owner_id}/{public_voice_id}",
                    headers=self._headers(),
                    json={"new_name": target.get("name", target_name or "shared_voice")},
                )
        except httpx.HTTPError as exc:
            raise ProviderError(f"ElevenLabs rete/DNS non raggiungibile: {exc}") from exc
        if add_response.status_code >= 400:
            for voice in await self.list_voices():
                if voice.get("name") == target.get("name"):
                    return str(voice.get("voice_id"))
            raise ProviderError(f"Aggiunta voce pubblica fallita {add_response.status_code}: {add_response.text}")
        payload = add_response.json()
        return payload.get("voice_id") or public_voice_id

    async def select_voice(self, payload: dict[str, Any]) -> VoiceAssignment:
        voice_id = await self.ensure_public_voice_available(payload)
        return VoiceAssignment(
            speaker_id=payload["speaker_id"],
            voice_id=voice_id,
            voice_name=payload["voice_name"],
            delivery_style=payload.get("delivery_style", "natural"),
            tts_prompt_tags=payload.get("tts_prompt_tags", []),
            continuity_anchor=payload.get("continuity_anchor", payload["speaker_id"]),
        )

    @retryable()
    async def synthesize(self, payload: dict[str, Any]) -> TTSOutput:
        errors: list[str] = []
        audio_path = Path(payload["audio_path"])
        audio_path.parent.mkdir(parents=True, exist_ok=True)
        for model_id in self.model_fallbacks:
            stitch_supported = self._supports_stitching(model_id)
            previous_request_ids = self._limit_history_ids(payload.get("previous_request_ids"))
            previous_history_item_ids = self._limit_history_ids(payload.get("previous_history_item_ids"))
            body = {
                "text": payload["text"],
                "model_id": model_id,
                "voice_settings": {"stability": 0.45, "similarity_boost": 0.75},
            }
            if stitch_supported:
                body["previous_request_ids"] = previous_request_ids
                body["previous_history_item_ids"] = previous_history_item_ids
            else:
                body["previous_text"] = payload.get("previous_text")
                body["next_text"] = payload.get("next_text")
            try:
                async with httpx.AsyncClient(timeout=180) as client:
                    response = await client.post(
                        f"{self.base_url}/text-to-speech/{payload['voice_id']}",
                        headers={**self._headers(), "Accept": "audio/mpeg", "Content-Type": "application/json"},
                        json=body,
                    )
            except httpx.HTTPError as exc:
                errors.append(f"{model_id}: network {exc}")
                continue
            if response.status_code < 400:
                audio_path.write_bytes(response.content)
                request_id = response.headers.get("request-id")
                return TTSOutput(
                    segment_id=payload["segment_id"],
                    speaker_id=payload["speaker_id"],
                    voice_id=payload["voice_id"],
                    audio_path=str(audio_path),
                    duration_seconds=0.0,
                    request_id=request_id,
                    history_item_id=self._response_history_item_id(response),
                    previous_text=payload.get("previous_text"),
                    next_text=payload.get("next_text"),
                    provider_metadata={"model_id": model_id},
                )
            errors.append(f"{model_id}: {response.status_code} {response.text}")
        raise ProviderError("TTS fallita su tutti i modelli fallback: " + " | ".join(errors))
