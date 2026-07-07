Task: split the chunk into ordered segments with exactly one speaker per segment.
Return only JSON:
{
  "segments": [
    {
      "segment_id": "string",
      "order_index": 1,
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
- Preserve the original reading order.
- A segment must contain either narration or the words of one speaker, never both.
- Split every time the speaker changes or narration resumes.
- Use the fewest coherent segments possible, but never merge different speakers.
- `speaker_hint` must be:
  - `narratore` for narration;
  - the explicit name if the text names the speaker;
  - otherwise a stable placeholder like `personaggio_1`, `personaggio_2`, reused for the same speaker within the chunk.
- Do not invent names, backstories, or extra speakers.
- `order_index` starts at 1 and must match the original order inside the chunk.
