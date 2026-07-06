from __future__ import annotations

import re

from book_to_audiovideo.models.domain import Chunk
from book_to_audiovideo.utils.hashing import stable_hash


class TextService:
    def normalize_text(self, text: str) -> str:
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def split_into_chunks(self, text: str, max_words: int = 120) -> list[Chunk]:
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        chunks: list[Chunk] = []
        current_paragraphs: list[str] = []
        current_words = 0
        paragraph_start = 0
        paragraph_index = 0
        for paragraph in paragraphs:
            words = len(paragraph.split())
            if current_paragraphs and current_words + words > max_words:
                chunk_text = "\n\n".join(current_paragraphs)
                chunk_id = stable_hash(f"{paragraph_start}:{chunk_text[:120]}")
                chunks.append(
                    Chunk(
                        chunk_id=chunk_id,
                        text=chunk_text,
                        order_index=len(chunks),
                        paragraph_start=paragraph_start,
                        paragraph_end=paragraph_index - 1,
                        estimated_duration_seconds=max(3.0, len(chunk_text.split()) / 2.7),
                    )
                )
                current_paragraphs = []
                current_words = 0
                paragraph_start = paragraph_index
            current_paragraphs.append(paragraph)
            current_words += words
            paragraph_index += 1
        if current_paragraphs:
            chunk_text = "\n\n".join(current_paragraphs)
            chunk_id = stable_hash(f"{paragraph_start}:{chunk_text[:120]}")
            chunks.append(
                Chunk(
                    chunk_id=chunk_id,
                    text=chunk_text,
                    order_index=len(chunks),
                    paragraph_start=paragraph_start,
                    paragraph_end=paragraph_index - 1,
                    estimated_duration_seconds=max(3.0, len(chunk_text.split()) / 2.7),
                )
            )
        return chunks
