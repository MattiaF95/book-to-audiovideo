Task: add expressive delivery tags only when justified for ElevenLabs style prompting.
Return only JSON:
{
  "tagged_text": "string",
  "tags_used": ["string"],
  "tag_confidence": 0.0
}
Rules:
- Keep the original text intact.
- Avoid over-tagging.
- If no tags are needed, return the input text unchanged.
