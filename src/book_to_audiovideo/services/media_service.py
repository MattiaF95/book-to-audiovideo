from __future__ import annotations

from book_to_audiovideo.models.domain import MediaPlanItem


class MediaService:
    def build_fallback_queries(self, item: MediaPlanItem) -> list[str]:
        candidates: list[str] = []
        if item.video_keywords:
            candidates.append(" ".join(item.video_keywords[:3]))
        if item.scene_type and item.mood:
            candidates.append(f"{item.scene_type} {item.mood}")
        if item.scene_type:
            candidates.append(item.scene_type)
        return [query for query in candidates if query.strip()]

    def build_sfx_queries(self, item: MediaPlanItem) -> list[str]:
        if not item.needs_sfx:
            return []
        candidates: list[str] = []
        if item.sfx_keywords:
            candidates.append(" ".join(item.sfx_keywords[:3]))
        if item.sfx_timeline_hint:
            candidates.append(item.sfx_timeline_hint)
        if item.mood:
            candidates.append(item.mood)
        return [query for query in candidates if query.strip()]
