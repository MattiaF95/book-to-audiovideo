# models

This folder defines the typed contract for the pipeline.

## Rules
- Put schema changes here first.
- Use Pydantic validation instead of scattered ad hoc checks.
- Keep enums and constrained fields strict.
- If you add or rename a field, update:
  1. the model
  2. the producing agent
  3. the consuming agents
  4. the related prompts
  5. the stage JSON serialization

## Notes
- `Segment` is the core unit passed across many stages.
- Be careful with `segment_type`, `speaker_hint`, `resolved_speaker_id`, offsets, and planning fields.