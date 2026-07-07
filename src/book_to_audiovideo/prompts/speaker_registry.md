Task: identify the stable set of recurring speakers in the cleaned text.
Return only JSON:
{
  "speakers": [
    {
      "speaker_id": "string",
      "name": "string",
      "role": "narrator or character",
      "gender": "male, female, or null",
      "continuity_key": "string",
      "preferred_voice_constraints": ["string"]
    }
  ]
}
Rules:
- There must be exactly one narrator speaker for the entire text.
- Reuse one stable speaker_id for each recurring character.
- Infer gender from explicit names, pronouns, kinship roles, and context.
- Use `null` only when gender is genuinely ambiguous.
- Keep preferred_voice_constraints short and sparse.
- Do not segment text or assign segments here.
