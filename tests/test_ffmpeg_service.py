from pathlib import Path

from book_to_audiovideo.config import Settings
from book_to_audiovideo.services.ffmpeg_service import FFmpegService


def test_mix_audio_tracks_uses_ducked_sfx(monkeypatch, tmp_path: Path) -> None:
    commands: list[list[str]] = []

    def fake_run(command: list[str]) -> list[str]:
        commands.append(command)
        return command

    service = FFmpegService(Settings())
    monkeypatch.setattr(service, "_run", fake_run)
    service.mix_audio_tracks(tmp_path / "voice.mp3", tmp_path / "sfx.mp3", tmp_path / "out.mp3", 12.0)
    assert "volume=0.18" in commands[0][7]
