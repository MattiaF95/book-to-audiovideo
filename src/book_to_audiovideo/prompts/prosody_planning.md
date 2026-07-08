Task: define only the per-segment prosody hints needed for TTS delivery.
Return only JSON.
Do not produce reasoning, analysis, or thinking text. Return only the requested JSON object.
Emit an entry for every input segment. Use an empty tags_used list and tagged_text equal to raw_text for segments that need no prosody change.

{
  "tone_tags": [
    {
      "segment_id": "seg-N",
      "tagged_text": "<raw_text with optional SSML-style inline tags, or raw_text verbatim if no tags needed>",
      "tags_used": ["<tag from the allowed list>"],
      "tag_confidence": 0.8
    }
  ]
}

Allowed inline tags for tagged_text (use only these, or none):
- <break time="Xs"/> — insert a pause of X seconds (use 0.3s, 0.5s, 1s only)
- <emphasis level="strong"> ... </emphasis> — stress a word or short phrase
- <emphasis level="moderate"> ... </emphasis> — light stress
- <prosody rate="slow"> ... </prosody> — slow down delivery
- <prosody rate="fast"> ... </prosody> — speed up delivery
- <prosody pitch="low"> ... </prosody> — lower pitch
- <prosody pitch="high"> ... </prosody> — raise pitch

Allowed values for tags_used (list only the tag names actually used in tagged_text):
break, emphasis-strong, emphasis-moderate, prosody-rate-slow, prosody-rate-fast, prosody-pitch-low, prosody-pitch-high

Example output:
{
  "tone_tags": [
    {
      "segment_id": "seg-1",
      "tagged_text": "«<emphasis level=\"strong\">Non muoverti</emphasis>,»",
      "tags_used": ["emphasis-strong"],
      "tag_confidence": 0.85
    },
    {
      "segment_id": "seg-2",
      "tagged_text": "Il battito del suo cuore risuonava nel silenzio della biblioteca.",
      "tags_used": [],
      "tag_confidence": 1.0
    }
  ]
}

Rules:
- Use tags only where they meaningfully improve TTS delivery. Keep markup minimal.
- tagged_text must be the verbatim raw_text with zero or more inline tags added. Do not paraphrase or shorten the text.
- tags_used must list only the tag names actually present in tagged_text for that segment.
- tag_confidence: float 0.0–1.0. Use 1.0 for segments with no tags (no decision needed). Use >= 0.75 for tagged segments.
- Do not assign voices, pronunciation, or media here.
- Output one entry per input segment, in the same order as the input.