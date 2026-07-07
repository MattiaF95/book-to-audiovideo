Task: correct the text conservatively, infer the scene context, and describe the dominant emotions.
Return only JSON:
{
  "corrected_text": "string",
  "corrections": [
    {
      "original": "string",
      "corrected": "string",
      "reason": "typo, intentional style, OCR noise, or other",
      "confidence": 0.0
    }
  ],
  "context": {
    "scene": "string",
    "emotions": ["string"],
    "tone": "string"
  },
  "warnings": ["string"]
}
Rules:
- Preserve meaning and style.
- Fix only obvious typos, spacing, punctuation, and high-confidence misspellings.
- Keep intentional wording, dialect, and authorial style.
- Do not split the text.
- Do not invent missing content.
- If a change is uncertain, leave it unchanged and add a warning.
