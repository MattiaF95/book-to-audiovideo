Task: identify the stable set of recurring speakers in the cleaned text.
Return only JSON:
Do not produce reasoning, analysis, or thinking text. Return only the requested JSON object.
Use real names and stable IDs. Replace every placeholder with actual speakers from the text.
{
  "speakers": [
    {
      "speaker_id": "<stable speaker id>",
      "name": "<speaker name>",
      "role": "narrator or character",
      "gender": "male, female, or null",
      "continuity_key": "<stable continuity key>",
      "preferred_voice_constraints": ["<short constraint>"]
    }
  ]
}
Rules:
- There must be exactly one narrator speaker for the entire text.
- Reuse one stable speaker_id for each recurring character.
- Infer gender from explicit names, pronouns, kinship roles, and context.
- Use `male`, `female`, or `null` only when gender is genuinely ambiguous.
- If gender is unclear, use `null` rather than `neutral` or other labels.
- If a character repeats, keep the same `speaker_id` and `continuity_key` every time.
- Keep preferred_voice_constraints short and sparse.
- Do not emit placeholder literals like `string` or angle-bracketed examples.
- Do not segment text or assign segments here.
