Task: decide background video keywords and whether sound effects are needed for this segment.
Return only JSON:
{
  "video_keywords": ["string"],
  "sfx_keywords": ["string"],
  "mood": "string",
  "scene_type": "string",
  "media_intensity": "low medium or high",
  "needs_sfx": true,
  "sfx_timeline_hint": "string or null"
}
Rules:
- needs_sfx true only when audible effects add value.
- Prefer one coherent background scene.
- Keep keywords short and usable in stock search.
- Do not choose a specific asset, URL, video id, or audio file.
