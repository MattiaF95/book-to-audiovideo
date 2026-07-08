Task: identify the stable set of recurring speakers in the cleaned text.
Return only JSON.
Do not produce reasoning, analysis, or thinking text. Return only the requested JSON object.
Use real names and stable IDs. Replace every placeholder with actual speakers from the text.

{
  "speakers": [
    {
      "speaker_id": "spk-1",
      "name": "<speaker name or descriptive label>",
      "role": "narrator or character",
      "gender": "male, female, or null",
      "continuity_key": "<lowercase-hyphenated stable key, e.g. marco-rossi or unnamed-man-coat>",
      "preferred_voice_constraints": ["<one short constraint, e.g. deep voice, Italian accent>"]
    }
  ]
}

Example output:
{
  "speakers": [
    {
      "speaker_id": "spk-1",
      "name": "Narratore",
      "role": "narrator",
      "gender": null,
      "continuity_key": "narrator",
      "preferred_voice_constraints": []
    },
    {
      "speaker_id": "spk-2",
      "name": "Marco",
      "role": "character",
      "gender": "male",
      "continuity_key": "marco",
      "preferred_voice_constraints": ["young male voice"]
    },
    {
      "speaker_id": "spk-3",
      "name": "Uomo con cappotto",
      "role": "character",
      "gender": "male",
      "continuity_key": "unnamed-man-coat",
      "preferred_voice_constraints": ["deep calm voice"]
    }
  ]
}

Rules:
- There must be exactly one narrator speaker with role "narrator" for the entire text.
- Assign continuity_key as a lowercase-hyphenated slug: use the character name if known, or a stable physical description if unnamed (e.g. unnamed-man-coat, unnamed-woman-red-dress).
- Reuse the same speaker_id and continuity_key for the same character across all chunks.
- Infer gender from names, pronouns, kinship roles, and context. Use null only when genuinely ambiguous.
- preferred_voice_constraints: zero to two short phrases maximum. Leave empty array if no constraint applies.
- Do not emit placeholder literals like "string" or angle-bracketed examples.
- Do not segment text or assign segments here.