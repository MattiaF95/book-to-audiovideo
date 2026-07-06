from book_to_audiovideo.models.domain import ToneTag


def test_tone_tag_model() -> None:
    tone = ToneTag(segment_id="seg-1", tagged_text="Hello", tag_confidence=0.2)
    assert tone.tags_used == []
