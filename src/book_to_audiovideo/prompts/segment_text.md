Task: split the chunk into ordered narration/dialogue segments.
Return only JSON:
{
  "segments": [
    {
      "segment_id": "string",
      "raw_text": "string",
      "segment_type": "narration or dialogue",
      "speaker_hint": "string or null",
      "start_offset": 0,
      "end_offset": 0,
      "emotion_hint": "string or null",
      "importance_score": 0.0
    }
  ]
}
Rules:
- Keep wording unchanged.
- Use the fewest coherent segments possible.
- speaker_hint is best effort only.
