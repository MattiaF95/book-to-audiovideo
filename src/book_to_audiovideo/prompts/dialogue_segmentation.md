Task: split the cleaned text into ordered segments and label each one with exactly one of the two valid types below.
Return only JSON.
Do not produce reasoning, analysis, or thinking text. Return only the requested JSON object.
Use the schema as a shape only. Replace every placeholder with real values from the text.
Valid segment types:
- `narration`: prose, description, or narration without direct speech.
- `dialogue`: direct speech or quoted speech from a character.
{
  "segments": [
    {
      "segment_id": "<unique segment id>",
      "order_index": "<1-based order>",
      "raw_text": "<verbatim segment text>",
      "segment_type": "narration",
      "start_offset": "<character start offset>",
      "end_offset": "<character end offset>"
    }
  ]
}
Example output with both valid labels:
{
  "segments": [
    {
      "segment_id": "seg-1",
      "order_index": 1,
      "raw_text": "Il corridoio era buio.",
      "segment_type": "narration",
      "start_offset": 0,
      "end_offset": 22
    },
    {
      "segment_id": "seg-2",
      "order_index": 2,
      "raw_text": "«Andiamo via» disse Marco.",
      "segment_type": "dialogue",
      "start_offset": 23,
      "end_offset": 49
    }
  ]
}
Rules:
- Keep the original reading order.
- Output only segmentation, not speaker attribution.
- If a paragraph contains narration and dialogue, split at the transition points.
- A continuous dialogue turn stays in one segment even if it contains punctuation, symbols, or internal pauses.
- Use `<< >>`, quotes, and dialogue markers as strong cues for dialogue boundaries.
- Use only the exact `segment_type` values `narration` and `dialogue`.
- Every output item must be one real segment from the text. Do not collapse multiple segments into one.
- Do not emit placeholder literals like `string`, `<unique segment id>`, or `<verbatim segment text>`.
- Do not add speaker fields, emotions, or importance.
