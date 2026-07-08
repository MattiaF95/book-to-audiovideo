Task: minimally clean the input text.
Return only JSON.
Do not produce reasoning, analysis, or thinking text. Return only the requested JSON object.
Do not add explanations.
Replace every placeholder with real values. Never return the literal word "string".

Schema:
{
  "corrected_text": "<the full cleaned text here — never the word string>",
  "corrections": [
    {
      "original": "<exact original substring>",
      "corrected": "<corrected substring>",
      "reason": "typo | spacing | punctuation | OCR noise | other",
      "confidence": 0.9
    }
  ],
  "warnings": []
}

Example output when no corrections are needed:
{
  "corrected_text": "Marco entrò nella stanza buia.",
  "corrections": [],
  "warnings": []
}

Example output with one correction:
{
  "corrected_text": "Marco entrò nella stanza buia.",
  "corrections": [
    {
      "original": "entroo",
      "corrected": "entrò",
      "reason": "typo",
      "confidence": 0.95
    }
  ],
  "warnings": []
}

Rules:
- corrected_text must contain the actual cleaned text, never the literal word "string".
- Preserve meaning and style. Fix only obvious errors.
- Do not infer speaker, scene, emotion, or context.
- Do not split the text.
- If unsure, leave it unchanged.
- If no changes are needed, return the original input text verbatim in corrected_text.
- confidence values are floats between 0.0 and 1.0. Only emit corrections with confidence >= 0.7.
- Do not emit corrections with confidence below 0.7.