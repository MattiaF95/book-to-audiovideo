from __future__ import annotations

import re

from book_to_audiovideo.agents.base import BaseAgent
from book_to_audiovideo.models.domain import Segment, SegmentType
from book_to_audiovideo.pipeline.context import PipelineContext
from book_to_audiovideo.providers.provider_base import LLMProvider

_QUOTE_OPEN  = "«"
_QUOTE_CLOSE = "»"


def _presegment_text(text: str) -> list[dict]:
    """
    Splits text into atomic narration/dialogue segments using « » as hard boundaries.
    Deterministic, no LLM needed. Strips whitespace from each chunk.
    """
    segments: list[dict] = []
    order = 1
    pos = 0
    n = len(text)

    while pos < n:
        open_pos = text.find(_QUOTE_OPEN, pos)

        if open_pos == -1:
            chunk = text[pos:].strip()
            if chunk:
                real_start = text.index(chunk, pos)
                segments.append({
                    "order_index": order,
                    "raw_text": chunk,
                    "segment_type": "narration",
                    "start_offset": real_start,
                    "end_offset": real_start + len(chunk),
                })
                order += 1
            break

        narration = text[pos:open_pos].strip()
        if narration:
            real_start = text.index(narration, pos)
            segments.append({
                "order_index": order,
                "raw_text": narration,
                "segment_type": "narration",
                "start_offset": real_start,
                "end_offset": real_start + len(narration),
            })
            order += 1

        close_pos = text.find(_QUOTE_CLOSE, open_pos + 1)
        if close_pos == -1:
            chunk = text[open_pos:].strip()
            segments.append({
                "order_index": order,
                "raw_text": chunk,
                "segment_type": "dialogue",
                "start_offset": open_pos,
                "end_offset": open_pos + len(chunk),
            })
            order += 1
            break

        dialogue = text[open_pos : close_pos + 1]
        segments.append({
            "order_index": order,
            "raw_text": dialogue,
            "segment_type": "dialogue",
            "start_offset": open_pos,
            "end_offset": close_pos + 1,
        })
        order += 1
        pos = close_pos + 1

    return segments


class DialogueSegmentationAgent(BaseAgent):
    stage_name = "dialogue_segmentation"

    def __init__(self, llm: LLMProvider) -> None:
        self.llm = llm  # kept for interface compatibility, not used here

    async def execute(self, context: PipelineContext) -> None:
        if context.state.segments:
            return

        raw_items = _presegment_text(context.state.cleaned_text)
        synthetic_chunk_id = context.state.book_id or context.state.job_id
        segments: list[Segment] = []

        for item in raw_items:
            item["segment_id"] = f"seg-{item['order_index']}"
            item["chunk_id"] = synthetic_chunk_id
            item.setdefault("speaker_hint", None)
            item.setdefault("resolved_speaker_id", None)
            item.setdefault("emotion_hint", None)
            item.setdefault("importance_score", 0.5)
            segments.append(Segment.model_validate(item))

        context.state.segments = segments
        self.write_stage_json(
            context,
            "04_dialogue_segmentation.json",
            {"segments": [s.model_dump(mode="json") for s in segments]},
        )