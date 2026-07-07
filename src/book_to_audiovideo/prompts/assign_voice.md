Task: assign one consistent voice to each canonical speaker using only the provided available voices.
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
- Give the narrator one stable voice for the whole project.
- Give each character one stable voice for all their segments.
- Do not create, merge, or rename speakers here.
- Return short, stable assignments.
