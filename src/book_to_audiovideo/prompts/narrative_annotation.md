Task: add only lightweight annotations to already attributed segments.
Return only JSON.
Do not produce reasoning, analysis, or thinking text. Return only the requested JSON object.
Do not add explanations.

Schema:
{
  "annotations": [
    {
      "segment_id": "string",
      "emotion_hint": "string",
      "importance_score": 0.0
    }
  ]
}

Rules:
- Keep annotations minimal.
- Use broad emotion labels only if useful.
- importance_score must be between 0.0 and 1.0.
- Do not change segmentation or speaker identity.
