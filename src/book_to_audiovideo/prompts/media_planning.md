Task: define only the background media plan for each segment.
Return only JSON.
Do not produce reasoning, analysis, or thinking text. Return only the requested JSON object.
Emit one entry per input segment.

{
  "media_plan": [
    {
      "segment_id": "seg-N",
      "video_keywords": ["<1-3 word searchable keyword>"],
      "sfx_keywords": ["<1-3 word searchable keyword>"],
      "mood": "<one value from the allowed mood list>",
      "scene_type": "<one value from the allowed scene_type list>",
      "media_intensity": "<low | medium | high>",
      "needs_sfx": true,
      "sfx_timeline_hint": "<start | end | throughout | null>"
    }
  ]
}

Allowed values for mood:
tense, calm, mysterious, joyful, sad, threatening, neutral, eerie, romantic, comedic, action

Allowed values for scene_type:
interior, exterior, abstract, transition

media_intensity scale:
- low: background atmosphere, no action
- medium: active scene, moderate emotional charge
- high: climax, confrontation, strong emotional peak

sfx_timeline_hint values:
- "start" — play SFX at the beginning of the segment
- "end" — play SFX at the end
- "throughout" — sustain SFX for the whole segment
- null — no SFX timing hint needed

Example output:
{
  "media_plan": [
    {
      "segment_id": "seg-1",
      "video_keywords": ["dark library", "flashlight"],
      "sfx_keywords": ["heartbeat", "silence"],
      "mood": "tense",
      "scene_type": "interior",
      "media_intensity": "medium",
      "needs_sfx": true,
      "sfx_timeline_hint": "throughout"
    },
    {
      "segment_id": "seg-4",
      "video_keywords": ["dark room", "shadow"],
      "sfx_keywords": ["metal clang"],
      "mood": "eerie",
      "scene_type": "interior",
      "media_intensity": "high",
      "needs_sfx": true,
      "sfx_timeline_hint": "start"
    }
  ]
}

Rules:
- video_keywords: one to three short phrases, each 1-3 words, suitable for a stock video search engine (e.g. Pixabay, Pexels). No full sentences.
- sfx_keywords: one to three short phrases, 1-3 words each. Use null array [] if no SFX is needed.
- mood and scene_type must use only values from the allowed lists above.
- media_intensity: low for atmospheric/transitional segments, medium for normal scenes, high only for emotional peaks or climax moments.
- needs_sfx: true only if at least one sfx_keyword is meaningful for the segment. False for pure narration with no sound cue.
- sfx_timeline_hint: use null if needs_sfx is false.
- Do not assign voices, pronunciation, or tone here.
- Output one entry per input segment, in the same order as the input.