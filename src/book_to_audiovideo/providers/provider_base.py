from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from book_to_audiovideo.models.domain import MediaAsset, TTSOutput, VoiceAssignment


class LLMProvider(ABC):
    @abstractmethod
    async def prepare_text(self, payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def structure_story(self, payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def plan_audio(self, payload: dict[str, Any]) -> dict[str, Any]:
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
