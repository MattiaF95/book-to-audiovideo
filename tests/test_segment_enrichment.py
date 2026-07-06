from book_to_audiovideo.models.domain import MediaPlanItem, PronunciationHint, ToneTag


def test_segment_enrichment_models_are_compatible() -> None:
    hint = PronunciationHint(segment_id="seg-1", confidence=0.8)
    tone = ToneTag(segment_id="seg-1", tagged_text="Hello", tag_confidence=0.6)
    media = MediaPlanItem(
        segment_id="seg-1",
        video_keywords=["library", "moonlight"],
        sfx_keywords=["wind"],
        mood="tense",
        scene_type="library",
        media_intensity="medium",
        needs_sfx=True,
        sfx_timeline_hint="soft wind",
    )
    assert hint.segment_id == tone.segment_id == media.segment_id
