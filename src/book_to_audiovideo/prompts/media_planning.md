Task: define only the background media plan for each segment.
Return only JSON:
{
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
- Keep keywords short, practical, and searchable.
- Use only broad scene and mood information already implied by the segment and context.
- Do not assign voices, pronunciation, or tone here.
