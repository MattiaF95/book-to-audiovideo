Task: add only lightweight annotations to already attributed segments.
Return only JSON.
Do not produce reasoning, analysis, or thinking text. Return only the requested JSON object.
Do not add explanations.
Every segment from the input list must appear in the output.

Schema:
{
  "annotations": [
    {
      "segment_id": "seg-N",
      "emotion_hint": "<one word from the allowed list, or null>",
      "importance_score": 0.5
    }
  ]
}

Allowed values for emotion_hint (use only these, or null):
neutral, tense, fearful, angry, sad, joyful, surprised, disgusted, calm, mysterious, threatening, ironic

importance_score scale:
- 0.0–0.3: background, atmospheric, or transitional segment
- 0.4–0.6: normal narrative or dialogue segment
- 0.7–0.9: key plot moment, emotional peak, or character reveal
- 1.0: reserved for the single most important moment in the text

Rules:
- Use emotion_hint only when it clearly applies. Use null for segments with no dominant emotion.
- Narration segments may have emotion_hint if the narration has a clear emotional charge.
- Do not use emotion values outside the allowed list.
- importance_score must be a float between 0.0 and 1.0. Vary scores meaningfully — do not set every segment to 0.5.
- Do not change segmentation or speaker identity.
- Output one annotation object per input segment, in the same order as the input.