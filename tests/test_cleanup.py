from book_to_audiovideo.models.domain import CleanupChange


def test_cleanup_change_model_accepts_high_confidence_payload() -> None:
    change = CleanupChange(
        original="teh",
        cleaned="the",
        reason="ocr",
        confidence=0.98,
        start_offset=10,
        end_offset=13,
    )
    assert change.cleaned == "the"
    assert change.needs_review is False
