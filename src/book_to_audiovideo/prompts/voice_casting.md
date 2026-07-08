Task: choose one stable voice assignment for each speaker using only the provided available voices.
Return only JSON.
Do not produce reasoning, analysis, or thinking text. Return only the requested JSON object.
Use the voice list as given. Keep narrator and recurring characters stable across the whole project.

{
  "voice_assignments": [
    {
      "speaker_id": "spk-N",
      "voice_id": "<exact voice_id from the provided voice list, or empty string if none matches>",
      "voice_name": "<exact voice name from the provided voice list>",
      "delivery_style": "<one value from the allowed list>",
      "tts_prompt_tags": ["<tag from the allowed list>"],
      "continuity_anchor": "<copy the continuity_key from the speaker registry for this speaker>"
    }
  ]
}

Allowed values for delivery_style (use only one of these):
neutral, dramatic, calm, expressive, whispering, authoritative, childlike, elderly

Allowed values for tts_prompt_tags (use only values from this list, zero to three tags max):
slow-pace, fast-pace, low-pitch, high-pitch, breathy, gravelly, warm, cold, monotone, animated

Example output:
{
  "voice_assignments": [
    {
      "speaker_id": "spk-1",
      "voice_id": "21m00Tcm4TlvDq8ikWAM",
      "voice_name": "Rachel",
      "delivery_style": "neutral",
      "tts_prompt_tags": ["warm"],
      "continuity_anchor": "narrator"
    },
    {
      "speaker_id": "spk-2",
      "voice_id": "AZnzlk1XvdvUeBnXmlld",
      "voice_name": "Domi",
      "delivery_style": "expressive",
      "tts_prompt_tags": ["animated", "fast-pace"],
      "continuity_anchor": "marco"
    }
  ]
}

Rules:
- Assign exactly one stable voice per speaker. Never leave voice_id null.
- If no voice matches, use an empty string for voice_id and explain nothing.
- The narrator must keep one consistent voice for the whole project.
- Reuse speaker_id values exactly as provided in the speaker registry.
- delivery_style and tts_prompt_tags must use only values from the allowed lists above.
- continuity_anchor must be copied verbatim from the speaker registry continuity_key.
- Do not plan pronunciation, media, or tone here.