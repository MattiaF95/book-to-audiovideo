Task: choose one stable voice assignment for each speaker using only the provided available voices.
Return only JSON:
{
  "voice_assignments": [
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
- Assign exactly one stable voice per speaker.
- The narrator must keep one consistent voice for the whole project.
- Reuse speaker_id values exactly as provided.
- Keep tts_prompt_tags short and sparse.
- Do not plan pronunciation, media, or tone here.
