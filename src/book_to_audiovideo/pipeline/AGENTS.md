# pipeline

This folder controls execution flow and shared pipeline state.

## Responsibilities
- `orchestrator.py` runs stages in order and handles persistence/resume.
- `context.py` defines the shared execution context.
- `errors.py` defines pipeline-specific exceptions.

## Rules
- Keep the stage order stable unless the whole pipeline is being changed intentionally.
- Do not put stage business logic in the orchestrator.
- Prefer explicit failures or warnings over silent fallback behavior.
- Keep resume behavior safe and predictable.
- If a stage output changes shape, verify downstream assumptions immediately.