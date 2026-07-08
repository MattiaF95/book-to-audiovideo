Task: choose one stable voice assignment for each speaker using only the provided available voices.
Return only JSON:
Do not produce reasoning, analysis, or thinking text. Return only the requested JSON object.
Use the voice list as given. Keep narrator and recurring characters stable across the whole project.
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
- If the same speaker appears in multiple dialogue segments, keep the same voice_id and voice_name.
- Keep tts_prompt_tags short and sparse.
- Do not plan pronunciation, media, or tone here.
