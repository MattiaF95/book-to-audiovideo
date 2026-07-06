Task: detect only real pronunciation risks for TTS.
Return only JSON:
{
  "pronunciation_overrides": {"term": "override"},
  "phonetic_hints": {"term": "phonetic hint"},
  "problem_terms": ["string"],
  "confidence": 0.0
}
Rules:
- Include only risky names, acronyms, or invented terms.
- Do not rewrite the segment.
