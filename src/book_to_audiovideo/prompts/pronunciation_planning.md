Task: identify only the pronunciation risks that matter for TTS.
Return only JSON:
Use the schema as a shape only. Do not add speaker, scene, or media analysis.
{
  "pronunciation": [
    {
      "segment_id": "string",
      "pronunciation_overrides": {"term": "override"},
      "phonetic_hints": {"term": "phonetic hint"},
      "problem_terms": ["string"],
      "confidence": 0.0
    }
  ]
}
Rules:
- Keep output sparse.
- Add overrides only for real pronunciation risks.
- Do not assign voices, tone, or media here.
