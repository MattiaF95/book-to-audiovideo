Task: enrich one segment for downstream processing.
Return only JSON:
{
  "pronunciation": {
    "pronunciation_overrides": {"term": "override"},
    "phonetic_hints": {"term": "phonetic hint"},
    "problem_terms": ["string"],
    "confidence": 0.0
  },
  "tone": {
    "tagged_text": "string",
    "tags_used": ["string"],
    "tag_confidence": 0.0
  },
  "media": {
    "video_keywords": ["string"],
    "sfx_keywords": ["string"],
    "mood": "string",
    "scene_type": "string",
    "media_intensity": "low medium or high",
    "needs_sfx": true,
    "sfx_timeline_hint": "string or null"
  }
}
Rules:
- Keep the response short and structured.
- pronunciation only for real TTS risks.
- tone should stay close to the original text.
- media keywords must be practical for stock search.
- Do not select a concrete media asset.
