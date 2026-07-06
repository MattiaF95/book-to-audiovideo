Task: clean only the provided text chunk conservatively.
Return only JSON:
{
  "cleaned_text": "string",
  "changes": [
    {
      "original": "string",
      "cleaned": "string",
      "reason": "string",
      "confidence": 0.0,
      "start_offset": 0,
      "end_offset": 0,
      "needs_review": false
    }
  ],
  "warnings": ["string"]
}
Rules:
- Preserve meaning and style.
- Fix only obvious punctuation, spacing, quotes, OCR noise, and high-confidence misspellings.
- Keep edits minimal. If unsure, leave text unchanged and warn.
