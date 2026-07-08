# prompts

This folder contains Markdown prompts loaded at runtime by LLM-driven agents.

## Prompt rules
- Return JSON only.
- Do not request reasoning text.
- Include an explicit output schema.
- Use closed vocabularies for categorical fields.
- Add at least one concrete example when the structure is non-trivial.
- Avoid placeholder literals like `"string"` in examples.
- Keep prompts aligned with the current Pydantic models.

## Maintenance rules
- If an output model changes, update the prompt in the same change.
- If an agent becomes deterministic, document that here and keep the prompt as fallback-only.
- Each prompt should describe exactly one stage responsibility.