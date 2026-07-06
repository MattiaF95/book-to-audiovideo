from book_to_audiovideo.models.domain import VoiceAssignment


def test_voice_assignment_keeps_anchor() -> None:
    assignment = VoiceAssignment(
        speaker_id="hero",
        voice_id="voice-1",
        voice_name="Hero Voice",
        delivery_style="dramatic",
        continuity_anchor="hero",
    )
    assert assignment.continuity_anchor == "hero"
