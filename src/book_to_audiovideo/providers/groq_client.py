from __future__ import annotations

import asyncio
import json
import logging
import math
import time
from collections import deque
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any

try:
    from groq import Groq
except ImportError:  # pragma: no cover - dependency is optional in unit tests
    Groq = None  # type: ignore[assignment]

import httpx

from book_to_audiovideo.config import Settings
from book_to_audiovideo.pipeline.errors import ProviderError
from book_to_audiovideo.providers.provider_base import LLMProvider

LOGGER = logging.getLogger(__name__)
GROQ_OPENAI_BASE_URL = "https://api.groq.com/openai/v1"


class GroqClient(LLMProvider):
    _global_rate_lock = asyncio.Lock()
    _request_window: deque[float] = deque()
    _token_window: deque[tuple[float, int]] = deque()
    _token_total = 0
    _last_request_monotonic = 0.0

    def __init__(self, settings: Settings, prompts_dir: Path) -> None:
        self.settings = settings
        self.prompts_dir = prompts_dir
        self.task_token_budgets = {
            "text_cleanup.md": settings.groq_cleanup_token_budget,
            "narrative_context.md": settings.groq_enrichment_token_budget,
            "dialogue_segmentation.md": settings.groq_segment_token_budget,
            "speaker_registry.md": settings.groq_segment_token_budget,
            "speaker_attribution.md": settings.groq_segment_token_budget,
            "narrative_annotation.md": settings.groq_enrichment_token_budget,
            "voice_casting.md": settings.groq_voice_token_budget,
            "pronunciation_planning.md": settings.groq_pronunciation_token_budget,
            "prosody_planning.md": settings.groq_tone_token_budget,
            "media_planning.md": settings.groq_media_token_budget,
        }

    def _load_prompt(self, name: str) -> str:
        return (self.prompts_dir / name).read_text(encoding="utf-8")

    def _estimate_tokens(self, text: str) -> int:
        return max(1, math.ceil(len(text) / 4))

    def _budget_for(self, prompt_name: str) -> int:
        return self.task_token_budgets.get(prompt_name, self.settings.groq_enrichment_token_budget)

    def _request_reservation(self, prompt_name: str, prompt_text: str, payload_text: str) -> int:
        prompt_budget = self._budget_for(prompt_name)
        estimated_tokens = self._estimate_tokens(prompt_text) + self._estimate_tokens(payload_text)
        requested = max(estimated_tokens + 200, prompt_budget)
        return max(1, min(requested, self.settings.groq_tokens_per_minute))

    def _retry_after_seconds(self, exc: Exception) -> float | None:
        response = getattr(exc, "response", None)
        if response is None:
            return None
        value = getattr(response, "headers", {}).get("Retry-After")
        if not value:
            return None
        try:
            return max(0.0, float(value))
        except ValueError:
            try:
                retry_at = parsedate_to_datetime(value)
            except (TypeError, ValueError):
                return None
            if retry_at.tzinfo is None:
                retry_at = retry_at.replace(tzinfo=timezone.utc)
            return max(0.0, (retry_at - datetime.now(timezone.utc)).total_seconds())

    def _compact_payload(self, prompt_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        if prompt_name == "text_cleanup.md":
            return {"text": payload.get("text", "")}
        if prompt_name == "narrative_context.md":
            return {"corrected_text": payload.get("corrected_text", "")}
        if prompt_name == "dialogue_segmentation.md":
            return {
                "corrected_text": payload.get("corrected_text", ""),
                "context": payload.get("context", {}),
            }
        if prompt_name == "speaker_registry.md":
            return {
                "corrected_text": payload.get("corrected_text", ""),
                "context": payload.get("context", {}),
            }
        if prompt_name == "speaker_attribution.md":
            return {
                "corrected_text": payload.get("corrected_text", ""),
                "context": payload.get("context", {}),
                "speakers": [self._compact_speaker(item) for item in payload.get("speakers", [])],
                "segments": [self._compact_segment(item) for item in payload.get("segments", [])],
            }
        if prompt_name == "narrative_annotation.md":
            return {
                "context": payload.get("context", {}),
                "speakers": [self._compact_speaker(item) for item in payload.get("speakers", [])],
                "segments": [self._compact_segment(item) for item in payload.get("segments", [])],
            }
        if prompt_name == "voice_casting.md":
            return {
                "context": payload.get("context", {}),
                "speakers": [self._compact_speaker(item) for item in payload.get("speakers", [])],
                "available_voices": [self._compact_voice(item) for item in payload.get("available_voices", [])],
            }
        if prompt_name == "pronunciation_planning.md":
            return {
                "segments": [self._compact_segment(item) for item in payload.get("segments", [])],
                "speakers": [self._compact_speaker(item) for item in payload.get("speakers", [])],
            }
        if prompt_name == "prosody_planning.md":
            return {
                "context": payload.get("context", {}),
                "segments": [self._compact_segment(item) for item in payload.get("segments", [])],
                "speakers": [self._compact_speaker(item) for item in payload.get("speakers", [])],
            }
        if prompt_name == "media_planning.md":
            return {
                "context": payload.get("context", {}),
                "segments": [self._compact_segment(item) for item in payload.get("segments", [])],
            }
        return payload

    def _compact_segment(self, payload: Any) -> Any:
        if not isinstance(payload, dict):
            return payload
        compact: dict[str, Any] = {}
        for key in ("segment_id", "order_index", "chunk_id", "segment_type", "speaker_hint", "resolved_speaker_id", "emotion_hint", "importance_score"):
            if key in payload:
                compact[key] = payload[key]
        raw_text = payload.get("raw_text")
        if isinstance(raw_text, str):
            compact["raw_text"] = raw_text[:240]
        return compact

    def _compact_speaker(self, payload: Any) -> Any:
        if not isinstance(payload, dict):
            return payload
        compact: dict[str, Any] = {}
        for key in ("speaker_id", "name", "role", "gender", "continuity_key"):
            if key in payload:
                compact[key] = payload[key]
        constraints = payload.get("preferred_voice_constraints")
        if isinstance(constraints, list):
            compact["preferred_voice_constraints"] = constraints[:4]
        return compact

    def _compact_voice(self, payload: Any) -> Any:
        if not isinstance(payload, dict):
            return payload
        compact: dict[str, Any] = {}
        for key in ("voice_id", "name"):
            if key in payload:
                compact[key] = payload[key]
        labels = payload.get("labels")
        if isinstance(labels, dict):
            compact["labels"] = self._truncate_value(labels, max_chars=160)
        return compact

    def _truncate_value(self, value: Any, max_chars: int) -> Any:
        if max_chars <= 0:
            return value
        if isinstance(value, str):
            return value if len(value) <= max_chars else value[:max_chars]
        if isinstance(value, list):
            items: list[Any] = []
            remaining = max_chars
            for item in value:
                if remaining <= 0:
                    break
                truncated = self._truncate_value(item, remaining)
                items.append(truncated)
                remaining -= len(json.dumps(truncated, ensure_ascii=False))
            return items
        if isinstance(value, dict):
            compact: dict[str, Any] = {}
            remaining = max_chars
            for key, item in value.items():
                if remaining <= 0:
                    break
                truncated = self._truncate_value(item, max(32, remaining - len(str(key)) - 4))
                compact[key] = truncated
                remaining -= len(str(key)) + len(json.dumps(truncated, ensure_ascii=False))
            return compact
        return value

    @classmethod
    def _prune_windows(cls, now: float) -> None:
        window_seconds = 60.0
        while cls._request_window and now - cls._request_window[0] >= window_seconds:
            cls._request_window.popleft()
        while cls._token_window and now - cls._token_window[0][0] >= window_seconds:
            _, tokens = cls._token_window.popleft()
            cls._token_total -= tokens
        cls._token_total = max(0, cls._token_total)

    def _wait_time_for_tokens(self, now: float, reserved_tokens: int) -> float:
        limit = self.settings.groq_tokens_per_minute
        if self.__class__._token_total + reserved_tokens <= limit:
            return 0.0
        needed = self.__class__._token_total + reserved_tokens - limit
        freed = 0
        for timestamp, tokens in self.__class__._token_window:
            freed += tokens
            if freed >= needed:
                return max(0.0, 60.0 - (now - timestamp))
        return 60.0

    def _wait_time_for_requests(self, now: float) -> float:
        limit = self.settings.groq_requests_per_minute
        if len(self.__class__._request_window) < limit:
            return 0.0
        oldest = self.__class__._request_window[0]
        return max(0.0, 60.0 - (now - oldest))

    async def _wait_for_global_limits(self, reserved_tokens: int) -> None:
        while True:
            async with self.__class__._global_rate_lock:
                now = time.monotonic()
                self.__class__._prune_windows(now)
                interval_wait = max(0.0, self.settings.llm_min_interval_seconds - (now - self.__class__._last_request_monotonic))
                wait_for = max(interval_wait, self._wait_time_for_requests(now), self._wait_time_for_tokens(now, reserved_tokens))
                if wait_for <= 0:
                    self.__class__._request_window.append(now)
                    self.__class__._token_window.append((now, reserved_tokens))
                    self.__class__._token_total += reserved_tokens
                    self.__class__._last_request_monotonic = now
                    return
            await asyncio.sleep(wait_for)

    def _create_body(self, prompt: str, payload_text: str, prompt_name: str) -> dict[str, Any]:
        max_tokens = min(4096, max(256, self._budget_for(prompt_name)))
        return {
            "model": self.settings.default_llm_model,
            "messages": [
                {
                    "role": "user",
                    "content": f"{prompt}\nINPUT_JSON:\n{payload_text}",
                }
            ],
            "temperature": 0.6,
            "max_completion_tokens": max_tokens,
            "top_p": 0.95,
            "stream": False,
        }

    def _extract_completion_text(self, completion: Any) -> str:
        choices = getattr(completion, "choices", None) or []
        if not choices:
            raise ProviderError("Risposta Groq priva di choices")
        message = getattr(choices[0], "message", None)
        if message is None:
            raise ProviderError("Risposta Groq priva di message")
        content = getattr(message, "content", None)
        if not content:
            raise ProviderError("Risposta Groq priva di content testuale")
        return content

    def _groq_completion_text(self, body: dict[str, Any]) -> str:
        if Groq is None:
            raise ProviderError("Pacchetto groq non disponibile")
        client = Groq(api_key=self.settings.groq_api_key) if self.settings.groq_api_key else Groq()
        completion = client.chat.completions.create(**body)
        return self._extract_completion_text(completion)

    def _extract_json_object(self, text: str) -> dict[str, Any]:
        decoder = json.JSONDecoder()
        stripped = text.lstrip()
        start = stripped.find("{")
        if start < 0:
            raise json.JSONDecodeError("No JSON object found", text, 0)
        candidate = stripped[start:]
        value, _ = decoder.raw_decode(candidate)
        if not isinstance(value, dict):
            raise json.JSONDecodeError("JSON root is not an object", text, 0)
        return value

    def _validate_response(self, prompt_name: str, response: dict[str, Any], payload: dict[str, Any]) -> None:
        def require_non_empty_string(field: str) -> None:
            value = response.get(field)
            if not isinstance(value, str) or not value.strip() or value.strip().lower() == "string":
                raise ProviderError(f"{prompt_name} ha restituito {field} vuoto o non valido")

        def require_list(field: str, expected_len: int | None = None) -> list[Any]:
            value = response.get(field)
            if not isinstance(value, list):
                raise ProviderError(f"{prompt_name} ha restituito {field} non valido")
            if not value:
                raise ProviderError(f"{prompt_name} ha restituito {field} vuoto")
            if expected_len is not None and len(value) != expected_len:
                raise ProviderError(
                    f"{prompt_name} ha restituito {field} con lunghezza {len(value)}, attesa {expected_len}"
                )
            return value

        if prompt_name == "text_cleanup.md":
            return
        if prompt_name == "narrative_context.md":
            context = response.get("context")
            if not isinstance(context, dict) or not context:
                raise ProviderError("narrative_context.md ha restituito context vuoto o non valido")
            return
        if prompt_name == "dialogue_segmentation.md":
            segments = require_list("segments")
            for item in segments:
                if not isinstance(item, dict):
                    raise ProviderError("dialogue_segmentation.md ha restituito un segmento non valido")
                if not isinstance(item.get("segment_id"), str) or not item["segment_id"].strip() or item["segment_id"].strip().lower() == "string":
                    raise ProviderError("dialogue_segmentation.md ha restituito segment_id non valido")
                if not isinstance(item.get("raw_text"), str) or not item["raw_text"].strip() or item["raw_text"].strip().lower() == "string":
                    raise ProviderError("dialogue_segmentation.md ha restituito raw_text non valido")
                if item.get("segment_type") not in {"narration", "dialogue"}:
                    raise ProviderError("dialogue_segmentation.md ha restituito segment_type non valido")
            return
        if prompt_name == "speaker_registry.md":
            speakers = require_list("speakers")
            if not any(isinstance(item, dict) and item.get("role") == "narrator" for item in speakers):
                raise ProviderError("speaker_registry.md non contiene il narratore")
            for item in speakers:
                if not isinstance(item, dict):
                    raise ProviderError("speaker_registry.md ha restituito uno speaker non valido")
                for field in ("speaker_id", "name", "continuity_key"):
                    value = item.get(field)
                    if not isinstance(value, str) or not value.strip() or value.strip().lower() == "string":
                        raise ProviderError(f"speaker_registry.md ha restituito {field} non valido")
                if item.get("role") not in {"narrator", "character"}:
                    raise ProviderError("speaker_registry.md ha restituito role non valido")
                gender = item.get("gender")
                if gender not in {"male", "female", None}:
                    raise ProviderError("speaker_registry.md ha restituito gender non valido")
            return
        if prompt_name == "speaker_attribution.md":
            expected_len = len(payload.get("segments", []))
            require_list("assignments", expected_len=expected_len)
            return
        if prompt_name == "narrative_annotation.md":
            expected_len = len(payload.get("segments", []))
            require_list("annotations", expected_len=expected_len)
            return
        if prompt_name == "voice_casting.md":
            expected_len = len(payload.get("speakers", []))
            require_list("voice_assignments", expected_len=expected_len)
            return
        if prompt_name == "pronunciation_planning.md":
            expected_len = len(payload.get("segments", []))
            require_list("pronunciation", expected_len=expected_len)
            return
        if prompt_name == "prosody_planning.md":
            expected_len = len(payload.get("segments", []))
            require_list("tone_tags", expected_len=expected_len)
            return
        if prompt_name == "media_planning.md":
            expected_len = len(payload.get("segments", []))
            require_list("media_plan", expected_len=expected_len)
            return

    async def _http_completion_text(self, body: dict[str, Any]) -> str:
        if not self.settings.groq_api_key:
            raise ProviderError("GROQ_API_KEY mancante")
        headers = {
            "Authorization": f"Bearer {self.settings.groq_api_key}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(base_url=GROQ_OPENAI_BASE_URL, timeout=120.0) as client:
            response = await client.post("/chat/completions", headers=headers, json=body)
            if response.is_error:
                raise ProviderError(f"Groq HTTP {response.status_code}: {response.text}")
            data = response.json()
        choices = data.get("choices") or []
        if not choices:
            raise ProviderError("Risposta Groq priva di choices")
        message = choices[0].get("message") or {}
        content = message.get("content")
        if not content:
            raise ProviderError("Risposta Groq priva di content testuale")
        return content

    async def _completion_text(self, body: dict[str, Any]) -> str:
        if Groq is not None:
            return await asyncio.to_thread(self._groq_completion_text, body)
        return await self._http_completion_text(body)

    async def _structured_generate(self, prompt_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        prompt = self._load_prompt(prompt_name)
        compact_payload = self._compact_payload(prompt_name, payload)
        payload_text = json.dumps(compact_payload, ensure_ascii=False)
        prompt_budget = self._budget_for(prompt_name)
        estimated_tokens = self._estimate_tokens(prompt) + self._estimate_tokens(payload_text)
        if estimated_tokens > prompt_budget:
            LOGGER.debug(
                "Groq payload over budget for %s: estimated=%s budget=%s",
                prompt_name,
                estimated_tokens,
                prompt_budget,
            )
            compact_payload = self._truncate_value(compact_payload, max_chars=prompt_budget * 4)
            payload_text = json.dumps(compact_payload, ensure_ascii=False)
        body = self._create_body(prompt, payload_text, prompt_name)
        errors: list[str] = []
        backoff_seconds = 1.0
        reserved_tokens = self._request_reservation(prompt_name, prompt, payload_text)
        for attempt in range(1, self.settings.max_llm_retries + 1):
            retry_after: float | None = None
            retryable_error = False
            await self._wait_for_global_limits(reserved_tokens)
            try:
                text = await self._completion_text(body)
            except Exception as exc:  # pragma: no cover - network/provider errors depend on runtime
                errors.append(str(exc))
                retry_after = self._retry_after_seconds(exc)
                retryable_error = True
            else:
                try:
                    response = self._extract_json_object(text)
                    self._validate_response(prompt_name, response, compact_payload)
                    return response
                except json.JSONDecodeError as exc:
                    errors.append(f"risposta non valida: {exc}")
                    retryable_error = True
            if attempt >= self.settings.max_llm_retries or not retryable_error:
                break
            wait_for = retry_after if retry_after is not None else backoff_seconds
            await asyncio.sleep(wait_for)
            backoff_seconds = min(backoff_seconds * 2, 8.0)
        raise ProviderError("Groq fallito su tutti i tentativi: " + " | ".join(errors))

    async def run_task(self, prompt_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        return await self._structured_generate(prompt_name, payload)
