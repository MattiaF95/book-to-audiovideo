Task: apply minimal conservative cleanup to the input text.
Return only JSON:
{
  "corrected_text": "string",
  "corrections": [
    {
      "original": "string",
      "corrected": "string",
      "reason": "typo, spacing, punctuation, OCR noise, or other",
      "confidence": 0.0
    }
  ],
  "warnings": ["string"]
}
Rules:
- Preserve meaning, wording, and authorial style.
- Fix only obvious typos, spacing, punctuation, and high-confidence OCR noise.
- Do not infer context, emotions, speaker identity, or segmentation here.
- Do not add or remove content unless the correction is obvious.
- If uncertain, keep the original text and add a warning.
