from book_to_audiovideo.services.text_service import TextService


def test_split_into_chunks_keeps_order_and_duration() -> None:
    service = TextService()
    text = "\n\n".join(
        [
            "Paragrafo uno con abbastanza testo per partire.",
            "Paragrafo due con altro contenuto.",
            "Paragrafo tre con ancora testo utile.",
        ]
    )
    chunks = service.split_into_chunks(text, max_words=8)
    assert len(chunks) >= 2
    assert chunks[0].order_index == 0
    assert all(chunk.estimated_duration_seconds > 0 for chunk in chunks)
