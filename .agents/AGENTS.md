# agents

This folder contains one file per pipeline stage.

## Contract
- Each agent inherits from `BaseAgent`.
- Each agent defines `stage_name`.
- Each agent implements `async execute(context: PipelineContext) -> None`.
- Each agent is idempotent and returns early if its output already exists.
- Each agent persists its stage output with `write_stage_json(...)`.

## Rules
- Keep one responsibility per agent.
- Do not move orchestration logic into agents.
- Use Pydantic models for structured input/output.
- Keep agent-specific prompt logic in `../prompts/`.
- Preserve stage numbering and file names.

## Project-specific rules
- `DialogueSegmentationAgent` is deterministic and should not call the LLM for normal `«...»` splitting.
- `SpeakerAttributionAgent` must not silently assign unresolved dialogue to the narrator.
- Narration should resolve to the narrator speaker id.
- If dialogue cannot be safely attributed, keep `resolved_speaker_id = None` and append a warning.

## When editing here
Also check:
- `../pipeline/AGENTS.md`
- `../models/AGENTS.md`
- `../prompts/AGENTS.md` if the agent uses LLMs