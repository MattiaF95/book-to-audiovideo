from __future__ import annotations

import asyncio
import json
import logging
import math
import time
from datetime import datetime, timezone
from collections import deque
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any

import httpx

from book_to_audiovideo.config import Settings
from book_to_audiovideo.pipeline.errors import ProviderError
from book_to_audiovideo.providers.provider_base import LLMProvider

LOGGER = logging.getLogger(__name__)


class GroqClient(LLMProvider):
    _global_rate_lock = asyncio.Lock()
    _request_window: deque[float] = deque()
    _token_window: deque[tuple[float, int]] = deque()
    _token_total = 0
    _last_request_monotonic = 0.0

    def __init__(self, settings: Settings, prompts_dir: Path) -> None:
        self.settings = settings
        self.prompts_dir = prompts_dir
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model_fallbacks = [settings.default_llm_model]
        self.task_token_budgets = {
            "text_preparation.md": max(settings.groq_cleanup_token_budget, 12000),
            "story_structure.md": max(settings.groq_segment_token_budget, 16000),
            "audio_planning.md": max(settings.groq_media_token_budget, 12000),
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
        if prompt_name in {"text_preparation.md", "story_structure.md", "audio_planning.md"}:
            return max(estimated_tokens + 200, prompt_budget)
        return min(prompt_budget, max(estimated_tokens + 200, 300))

    def _retry_after_seconds(self, response: httpx.Response) -> float | None:
        value = response.headers.get("Retry-After")
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
        if prompt_name == "text_preparation.md":
            return {"text": payload.get("text", "")}
        if prompt_name == "story_structure.md":
            return {
                "corrected_text": payload.get("corrected_text", ""),
                "context": payload.get("context", {}),
            }
        if prompt_name == "audio_planning.md":
            return {
                "corrected_text": payload.get("corrected_text", ""),
                "context": payload.get("context", {}),
                "speakers": [self._compact_speaker(item) for item in payload.get("speakers", [])],
                "segments": [self._compact_segment(item) for item in payload.get("segments", [])],
                "available_voices": [self._compact_voice(item) for item in payload.get("available_voices", [])],
            }
        return self._truncate_value(payload, max_chars=self._budget_for(prompt_name) * 4)

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

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.settings.groq_api_key}",
            "Content-Type": "application/json",
        }

    async def _structured_generate(self, prompt_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        prompt = self._load_prompt(prompt_name)
        compact_payload = self._compact_payload(prompt_name, payload)
        prompt_budget = self._budget_for(prompt_name)
        payload_text = json.dumps(compact_payload, ensure_ascii=False)
        estimated_tokens = self._estimate_tokens(prompt) + self._estimate_tokens(payload_text)
        if estimated_tokens > prompt_budget:
            if prompt_name in {"text_preparation.md", "story_structure.md", "audio_planning.md"}:
                LOGGER.debug("Groq payload over budget for %s but skipping truncation by design", prompt_name)
            else:
                LOGGER.debug(
                    "Groq payload over budget for %s: estimated=%s budget=%s",
                    prompt_name,
                    estimated_tokens,
                    prompt_budget,
                )
                compact_payload = self._truncate_value(compact_payload, max_chars=prompt_budget * 4)
                payload_text = json.dumps(compact_payload, ensure_ascii=False)
        body = {
            "model": self.settings.default_llm_model,
            "messages": [
                {
                    "role": "system",
                    "content": "Return JSON only.",
                },
                {
                    "role": "user",
                    "content": f"{prompt}\nINPUT_JSON:\n{payload_text}",
                },
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.1,
        }
        errors: list[str] = []
        backoff_seconds = 1.0
        reserved_tokens = self._request_reservation(prompt_name, prompt, payload_text)
        for attempt in range(1, self.settings.max_llm_retries + 1):
            retry_after: float | None = None
            retryable_error = False
            await self._wait_for_global_limits(reserved_tokens)
            async with httpx.AsyncClient(timeout=120) as client:
                for model_name in self.model_fallbacks:
                    request_body = {**body, "model": model_name}
                    try:
                        response = await client.post(self.base_url, headers=self._headers(), json=request_body)
                    except httpx.HTTPError as exc:
                        errors.append(f"{model_name}: network {exc}")
                        retryable_error = True
                        continue
                    if response.status_code >= 400:
                        errors.append(f"{model_name}: {response.status_code} {response.text}")
                        if response.status_code == 429:
                            retry_after = self._retry_after_seconds(response)
                            retryable_error = True
                            break
                        if response.status_code in {500, 503}:
                            retryable_error = True
                            continue
                        raise ProviderError(f"Groq errore {response.status_code}: {response.text}")
                    data = response.json()
                    try:
                        text = data["choices"][0]["message"]["content"]
                        return json.loads(text)
                    except (KeyError, IndexError, json.JSONDecodeError) as exc:
                        errors.append(f"{model_name}: risposta non valida")
                        retryable_error = True
                        continue
            if attempt >= self.settings.max_llm_retries or not retryable_error:
                break
            wait_for = retry_after if retry_after is not None else backoff_seconds
            await asyncio.sleep(wait_for)
            backoff_seconds = min(backoff_seconds * 2, 8.0)
        raise ProviderError("Groq fallito su tutti i tentativi: " + " | ".join(errors))

    async def prepare_text(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self._structured_generate("text_preparation.md", payload)

    async def structure_story(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self._structured_generate("story_structure.md", payload)

    async def plan_audio(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self._structured_generate("audio_planning.md", payload)
