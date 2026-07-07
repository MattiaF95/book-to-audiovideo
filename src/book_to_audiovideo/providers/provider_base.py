from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from book_to_audiovideo.models.domain import MediaAsset, TTSOutput, VoiceAssignment


class LLMProvider(ABC):
    @abstractmethod
    async def cleanup_text(self, text: str) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def analyze_text(self, chunk_text: str) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def extract_segments(self, chunk_text: str) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def resolve_speaker(self, payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def assign_voice(self, payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def extract_pronunciation_hints(self, payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def add_tone_tags(self, payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def plan_media_keywords(self, payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError


class TTSProvider(ABC):
    @abstractmethod
    async def list_voices(self) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    async def list_shared_voices(self) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    async def ensure_public_voice_available(self, descriptor: dict[str, Any]) -> str:
        raise NotImplementedError

    @abstractmethod
    async def select_voice(self, payload: dict[str, Any]) -> VoiceAssignment:
        raise NotImplementedError

    @abstractmethod
    async def synthesize(self, payload: dict[str, Any]) -> TTSOutput:
        raise NotImplementedError


class StockMediaProvider(ABC):
    @abstractmethod
    async def search_videos(self, query: str) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    async def download_media(self, asset: dict[str, Any], target_dir: str, media_type: str, query: str) -> MediaAsset:
        raise NotImplementedError
