from book_to_audiovideo.models.domain import PronunciationHint


def test_pronunciation_hint_defaults() -> None:
    hint = PronunciationHint(segment_id="seg-1", confidence=0.7)
    assert hint.problem_terms == []
