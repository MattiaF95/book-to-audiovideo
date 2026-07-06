Task: resolve canonical speakers across the provided segment list.
Return only JSON:
{
  "speakers": [
    {
      "speaker_id": "string",
      "name": "string",
      "role": "narrator or character",
      "gender": "string or null",
      "continuity_key": "string",
      "preferred_voice_constraints": ["string"]
    }
  ],
  "segment_speaker_map": {
    "segment_id": "speaker_id"
  }
}
Rules:
- Use minimal stable speaker ids.
- Prefer one narrator plus recurring characters.
- If uncertain, pick the most probable match.
