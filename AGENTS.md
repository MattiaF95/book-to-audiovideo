# Book to Audiovideo

> Python pipeline that turns a book into a narrated video using Groq for LLM tasks, ElevenLabs for TTS, Pixabay for background media, and FFmpeg for final composition.

## Start here
Read `README.md` first for product overview, pipeline order, environment variables, and run commands.

## Project map
- `src/book_to_audiovideo/agents/` — pipeline agents
- `src/book_to_audiovideo/pipeline/` — orchestration and state flow
- `src/book_to_audiovideo/models/` — Pydantic domain and state models
- `src/book_to_audiovideo/prompts/` — LLM prompt files
- `src/book_to_audiovideo/providers/` — external API adapters
- `src/book_to_audiovideo/services/` — local technical helpers
- `src/book_to_audiovideo/web/` — local dashboard

## Global rules
- Make the smallest safe change.
- Preserve stage order and idempotency.
- Keep prompt text in Markdown files, not inline in Python.
- Update models, prompts, and downstream consumers together when a schema changes.
- Before editing a subfolder, read its local `AGENTS.md` if present.

## Commands
```bash
python -m book_to_audiovideo.main run path/al/libro.txt
python -m book_to_audiovideo.main serve
pytest tests/
```

## Do not
- Do not bypass the pipeline to write to output artifacts directly.
- Do not change generated files by hand if a stage regenerates them.
- Do not remove guards that prevent reruns from duplicating work.