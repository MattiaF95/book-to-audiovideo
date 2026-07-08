Task: identify only the pronunciation risks that matter for TTS in the provided segments.
Return only JSON.
Do not produce reasoning, analysis, or thinking text. Return only the requested JSON object.
Emit an entry only for segments that have at least one real pronunciation risk. Omit segments with no risk.

{
  "pronunciation": [
    {
      "segment_id": "seg-N",
      "pronunciation_overrides": {
        "<original term>": "<replacement text for TTS to read aloud>"
      },
      "phonetic_hints": {
        "<original term>": "<IPA or phonetic spelling>"
      },
      "problem_terms": ["<term>"],
      "confidence": 0.8
    }
  ]
}

Field definitions:
- pronunciation_overrides: replace the term with a different string that TTS should read instead, e.g. "1.500" -> "millecinquecento", "Dr." -> "Dottore".
- phonetic_hints: IPA or simplified phonetic spelling for terms the TTS engine may mispronounce, e.g. "Clang" -> "klæŋ".
- problem_terms: list of terms that have at least one override or hint in this segment.
- confidence: float 0.0–1.0. Only emit entries with confidence >= 0.75.

Example output:
{
  "pronunciation": [
    {
      "segment_id": "seg-4",
      "pronunciation_overrides": {
        "Clang": "clang metallico"
      },
      "phonetic_hints": {
        "Clang": "klæŋ"
      },
      "problem_terms": ["Clang"],
      "confidence": 0.85
    },
    {
      "segment_id": "seg-10",
      "pronunciation_overrides": {
        "1.500 euro": "millecinquecento euro"
      },
      "phonetic_hints": {},
      "problem_terms": ["1.500 euro"],
      "confidence": 0.95
    }
  ]
}

Rules:
- Only emit entries with confidence >= 0.75. Do not emit low-confidence guesses.
- pronunciation_overrides is for text substitution (numbers, abbreviations, foreign words).
- phonetic_hints is for IPA or phonetic guidance on how to pronounce a specific term.
- The two fields serve different purposes: do not duplicate the same term in both unless both types of hint are needed.
- Keep problem_terms to terms that actually appear verbatim in the segment raw_text.
- Do not assign voices, tone, or media here.