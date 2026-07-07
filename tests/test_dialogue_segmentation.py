from book_to_audiovideo.models.domain import Segment, SegmentType


def test_segment_model_supports_dialogue_and_narration() -> None:
    segment = Segment(
        segment_id="s1",
        chunk_id="c1",
        order_index=1,
        raw_text='"Ciao", disse Luca.',
        segment_type=SegmentType.dialogue,
        speaker_hint="Luca",
        start_offset=0,
        end_offset=20,
        emotion_hint="calm",
        importance_score=0.8,
    )
    assert segment.segment_type is SegmentType.dialogue
