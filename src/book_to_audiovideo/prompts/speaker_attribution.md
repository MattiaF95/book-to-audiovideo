Task: assign each existing segment to one speaker from the provided speaker registry.
Return only JSON:
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
- Keep one dialogue turn assigned to one speaker only.
- Do not create new speakers.
- Do not add emotions, importance, or extra fields.
