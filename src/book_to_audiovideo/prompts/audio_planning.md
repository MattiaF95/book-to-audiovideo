Task: plan voices, pronunciation, tone tags, and background media for the ordered segments.
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
  ],
  "pronunciation": [
    {
      "segment_id": "string",
      "pronunciation_overrides": {"term": "override"},
      "phonetic_hints": {"term": "phonetic hint"},
      "problem_terms": ["string"],
      "confidence": 0.0
    }
  ],
  "tone_tags": [
    {
      "segment_id": "string",
      "tagged_text": "string",
      "tags_used": ["string"],
      "tag_confidence": 0.0
    }
  ],
  "media_plan": [
    {
      "segment_id": "string",
      "video_keywords": ["string"],
      "sfx_keywords": ["string"],
      "mood": "string",
      "scene_type": "string",
      "media_intensity": "low, medium, or high",
      "needs_sfx": true,
      "sfx_timeline_hint": "string or null"
    }
  ]
}
Rules:
- Use the provided available voices only.
- Give the narrator one stable voice for the whole project.
- Give each character one stable voice across the entire story.
- Choose voices from the emotional, gender, and role information.
- Keep tone tags minimal and only where they help TTS.
- Keep pronunciation hints only for real risks.
- Keep media keywords practical and short.
- Do not create or rename speakers here.
