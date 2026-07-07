Task: add only lightweight descriptive annotations to the existing attributed segments.
Return only JSON:
{
  "annotations": [
    {
      "segment_id": "string",
      "emotion_hint": "string or null",
      "importance_score": 0.0
    }
  ]
}
Rules:
- Keep annotations minimal and stable.
- Use broad emotion labels only when useful for audio delivery.
- importance_score must stay between 0.0 and 1.0.
- Do not modify segmentation or speaker identity.
