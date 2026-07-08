NOTE: this prompt is kept as a fallback only.
Primary segmentation is performed deterministically in DialogueSegmentationAgent
using « » as hard boundaries. This prompt is NOT called in normal pipeline runs.

If called as fallback for texts without « » delimiters (e.g. using — or " "):
Task: split the cleaned text into ordered narration/dialogue segments.
Return only JSON. Do not produce reasoning or thinking text.

{
  "segments": [
    {
      "segment_id": "seg-N",
      "order_index": 1,
      "segment_id": "seg-N",
      "order_index": 1,
      "raw_text": "<verbatim segment text>",
      "segment_type": "narration",
      "start_offset": 0,
      "end_offset": 0
    }
  ]
}

Rules:
- Every opening dialogue delimiter (—, ", ') starts a new dialogue segment.
- Every closing delimiter ends that dialogue segment.
- Verbs of saying (disse, sussurrò, gridò, interruppe) are always narration.
- Split at every narration↔dialogue transition. Minimum segment length: 1 word.
- Use only values "narration" and "dialogue" for segment_type.
- Output only segmentation. Do not assign speakers.