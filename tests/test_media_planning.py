from book_to_audiovideo.models.domain import MediaPlanItem
from book_to_audiovideo.services.media_service import MediaService


def test_media_service_builds_queries() -> None:
    item = MediaPlanItem(
        segment_id="seg-1",
        video_keywords=["forest", "night", "mist"],
        sfx_keywords=["wind", "branches"],
        mood="tense",
        scene_type="forest",
        media_intensity="medium",
        needs_sfx=True,
        sfx_timeline_hint="light wind",
    )
    service = MediaService()
    assert service.build_fallback_queries(item)[0] == "forest night mist"
    assert service.build_sfx_queries(item)[0] == "wind branches"
