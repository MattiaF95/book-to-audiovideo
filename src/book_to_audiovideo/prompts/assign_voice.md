Task: assign one consistent voice to each speaker using only provided available voices.
Return only JSON:
{
  "assignments": [
    {
      "speaker_id": "string",
      "voice_id": "string or empty if unavailable",
      "voice_name": "string",
      "delivery_style": "string",
      "tts_prompt_tags": ["string"],
      "continuity_anchor": "string"
    }
  ]
}
Rules:
- Select only from available voices.
- Keep narrator separate from characters.
- Return short, stable assignments.
