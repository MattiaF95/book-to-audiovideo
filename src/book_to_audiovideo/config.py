from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_host: str = Field(default="127.0.0.1", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    groq_api_key: str = Field(default="", alias="GROQ_API_KEY")
    elevenlabs_api_key: str = Field(default="", alias="ELEVENLABS_API_KEY")
    pixabay_api_key: str = Field(default="", alias="PIXABAY_API_KEY")
    output_dir: Path = Field(default=Path("data/output"), alias="OUTPUT_DIR")
    cache_dir: Path = Field(default=Path("data/cache"), alias="CACHE_DIR")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    default_tts_model: str = Field(default="eleven_v3", alias="DEFAULT_TTS_MODEL")
    default_llm_model: str = Field(default="llama-3.3-70b-versatile", alias="DEFAULT_LLM_MODEL")
    ffmpeg_bin: str = Field(default="ffmpeg", alias="FFMPEG_BIN")
    ffprobe_bin: str = Field(default="ffprobe", alias="FFPROBE_BIN")
    approval_timeout_seconds: int = Field(default=0, alias="APPROVAL_TIMEOUT_SECONDS")
    max_llm_retries: int = Field(default=3, alias="MAX_LLM_RETRIES")
    llm_min_interval_seconds: float = Field(default=3.0, alias="LLM_MIN_INTERVAL_SECONDS")
    groq_requests_per_minute: int = Field(default=30, alias="GROQ_REQUESTS_PER_MINUTE")
    groq_tokens_per_minute: int = Field(default=6000, alias="GROQ_TOKENS_PER_MINUTE")
    cleanup_chunk_words: int = Field(default=120, alias="CLEANUP_CHUNK_WORDS")
    groq_cleanup_token_budget: int = Field(default=900, alias="GROQ_CLEANUP_TOKEN_BUDGET")
    groq_segment_token_budget: int = Field(default=700, alias="GROQ_SEGMENT_TOKEN_BUDGET")
    groq_speaker_token_budget: int = Field(default=650, alias="GROQ_SPEAKER_TOKEN_BUDGET")
    groq_voice_token_budget: int = Field(default=450, alias="GROQ_VOICE_TOKEN_BUDGET")
    groq_enrichment_token_budget: int = Field(default=550, alias="GROQ_ENRICHMENT_TOKEN_BUDGET")
    groq_pronunciation_token_budget: int = Field(default=280, alias="GROQ_PRONUNCIATION_TOKEN_BUDGET")
    groq_tone_token_budget: int = Field(default=280, alias="GROQ_TONE_TOKEN_BUDGET")
    groq_media_token_budget: int = Field(default=280, alias="GROQ_MEDIA_TOKEN_BUDGET")
    max_media_retries: int = Field(default=3, alias="MAX_MEDIA_RETRIES")
    max_tts_retries: int = Field(default=2, alias="MAX_TTS_RETRIES")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", populate_by_name=True, extra="ignore")


def get_settings() -> Settings:
    settings = Settings()
    settings.output_dir.mkdir(parents=True, exist_ok=True)
    settings.cache_dir.mkdir(parents=True, exist_ok=True)
    return settings
