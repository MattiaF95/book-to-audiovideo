Task: define only the per-segment prosody hints needed for TTS delivery.
Return only JSON:
Use the schema as a shape only. Do not add speaker, pronunciation, or media analysis.
{
  "tone_tags": [
    {
      "segment_id": "string",
      "tagged_text": "string",
      "tags_used": ["string"],
      "tag_confidence": 0.0
    }
  ]
}
Rules:
- Keep tags minimal and only where they help delivery.
- Preserve the original text of the segment unless a markup-like emphasis is truly useful.
- Do not assign voices, pronunciation, or media here.
