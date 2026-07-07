Task: minimally clean the input text.
Return only JSON.
Do not add explanations.
The schema below is illustrative only: replace placeholder values with the real cleaned content.

Schema:
{
  "corrected_text": "string",
  "corrections": [
    {
      "original": "string",
      "corrected": "string",
      "reason": "typo | spacing | punctuation | OCR noise | other",
      "confidence": 0.0
    }
  ],
  "warnings": []
}

Rules:
- Preserve meaning and style.
- Fix only obvious errors.
- Do not infer speaker, scene, emotion, or context.
- Do not split the text.
- If unsure, leave it unchanged.
- If no changes are needed, return the original input text verbatim in `corrected_text`.
- `corrected_text` must contain the actual cleaned text, never the literal word `string`.
