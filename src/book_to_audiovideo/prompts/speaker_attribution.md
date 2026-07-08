Task: assign each existing segment to one speaker from the provided speaker registry.
Return only JSON:
Do not produce reasoning, analysis, or thinking text. Return only the requested JSON object.
Use the provided speaker registry only. Reuse the same speaker_id for the same character across all matching segments.
{
  "assignments": [
    {
      "segment_id": "string",
      "speaker_hint": "string or null",
      "resolved_speaker_id": "string"
    }
  ]
}
Rules:
- Use only speaker_id values already present in the input speakers list.
- All narration segments must resolve to the single narrator speaker.
- Use dialogue delimiters and nearby attribution before broader context.
- If the same character speaks multiple times, assign every matching dialogue segment to the same speaker_id.
- Keep one dialogue turn assigned to one speaker only.
- Do not create new speakers.
- Do not add emotions, importance, or extra fields.
