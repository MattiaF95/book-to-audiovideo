from pathlib import Path

import anyio

import book_to_audiovideo.agents.media_fetch_agent as media_fetch_agent_module
from book_to_audiovideo.agents.media_fetch_agent import MediaFetchAgent
from book_to_audiovideo.config import Settings
from book_to_audiovideo.models.domain import MediaAsset, MediaPlanItem
from book_to_audiovideo.models.state import PipelineState
from book_to_audiovideo.pipeline.context import PipelineContext


class _FakeMediaProvider:
    async def search_videos(self, query: str) -> list[dict]:
        return [
            {"id": 1, "videos": {"medium": {"url": "https://example.com/video-1.mp4"}}},
            {"id": 2, "videos": {"medium": {"url": "https://example.com/video-2.mp4"}}},
        ]

    async def download_media(self, asset: dict, target_dir: str, media_type: str, query: str) -> MediaAsset:
        path = Path(target_dir)
        path.mkdir(parents=True, exist_ok=True)
        local_path = path / f"{media_type}_{asset['id']}.mp4"
        local_path.write_bytes(b"data")
        return MediaAsset(
            provider="pixabay",
            query=query,
            asset_id=str(asset["id"]),
            media_type="video" if media_type == "video" else "audio",
            source_url="https://example.com/video.mp4",
            local_path=str(local_path),
        )


class _FakeMediaService:
    def build_fallback_queries(self, item: MediaPlanItem) -> list[str]:
        return ["forest night mist"]


def test_media_fetch_agent_downloads_only_video(tmp_path: Path) -> None:
    settings = Settings(OUTPUT_DIR=tmp_path, CACHE_DIR=tmp_path / "cache", PIXABAY_API_KEY="test")
    artifact_dir = tmp_path / "job"
    artifact_dir.mkdir()
    state = PipelineState(
        job_id="job-1",
        book_id="book-1",
        source_path=str(tmp_path / "source.txt"),
        source_name="source.txt",
        source_type=".txt",
        artifact_dir=str(artifact_dir),
        media_plan=[
            MediaPlanItem(
                segment_id="seg-1",
                video_keywords=["forest", "night", "mist"],
                sfx_keywords=["wind"],
                mood="tense",
                scene_type="forest",
                media_intensity="medium",
                needs_sfx=True,
            )
        ],
    )
    context = PipelineContext(settings=settings, state=state)
    agent = MediaFetchAgent(_FakeMediaProvider(), _FakeMediaService())

    anyio.run(agent.execute, context)

    assert len(context.state.downloaded_media) == 1
    assert context.state.downloaded_media[0].media_type == "video"


def test_media_fetch_agent_uses_random_hit(tmp_path: Path, monkeypatch) -> None:
    settings = Settings(OUTPUT_DIR=tmp_path, CACHE_DIR=tmp_path / "cache", PIXABAY_API_KEY="test")
    artifact_dir = tmp_path / "job"
    artifact_dir.mkdir()
    state = PipelineState(
        job_id="job-1",
        book_id="book-1",
        source_path=str(tmp_path / "source.txt"),
        source_name="source.txt",
        source_type=".txt",
        artifact_dir=str(artifact_dir),
        media_plan=[
            MediaPlanItem(
                segment_id="seg-1",
                video_keywords=["forest", "night", "mist"],
                sfx_keywords=["wind"],
                mood="tense",
                scene_type="forest",
                media_intensity="medium",
                needs_sfx=True,
            )
        ],
    )
    context = PipelineContext(settings=settings, state=state)
    agent = MediaFetchAgent(_FakeMediaProvider(), _FakeMediaService())

    monkeypatch.setattr(media_fetch_agent_module.random, "choice", lambda items: items[1])

    anyio.run(agent.execute, context)

    assert context.state.downloaded_media[0].asset_id == "2"
