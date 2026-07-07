Task: split the cleaned text into ordered segments of narration or dialogue only.
Return only JSON:
{
  "segments": [
    {
      "segment_id": "string",
      "order_index": 1,
      "raw_text": "string",
      "segment_type": "narration or dialogue",
      "start_offset": 0,
      "end_offset": 0
    }
  ]
}
Rules:
- Keep the original reading order.
- Output only segmentation, not speaker attribution.
- If a paragraph contains narration and dialogue, split at the transition points.
- A continuous dialogue turn stays in one segment even if it contains punctuation, symbols, or internal pauses.
- Use `<< >>`, quotes, and dialogue markers as strong cues for dialogue boundaries.
- Do not add speaker fields, emotions, or importance.
