Task: infer only the global narrative context of the cleaned text.
Return only JSON.
Do not produce reasoning, analysis, or thinking text. Return only the requested JSON object.
Replace every placeholder with a real value derived from the text. Never return the literal words "string" or "string or null".

{
  "context": {
    "scene": "<one-sentence description of the main scene or situation>",
    "tone": "<dominant emotional tone of the text, e.g. tense, melancholic, humorous>",
    "setting": "<physical or temporal setting, e.g. abandoned library at night>",
    "time_period": "<historical or narrative period if determinable, otherwise null>"
  }
}

Example output:
{
  "context": {
    "scene": "Two teenagers investigate a noise in a dark library and are confronted by a mysterious stranger",
    "tone": "tense and suspenseful",
    "setting": "a dark library at night",
    "time_period": "contemporary"
  }
}

Rules:
- Describe only global context useful for later TTS and media planning.
- Keep each field to one short sentence or phrase.
- Use null for time_period only when the text gives no temporal cue whatsoever.
- Do not segment the text.
- Do not identify speakers here.
- Do not infer per-segment emotions here.
- Never return placeholder literals like "string", "string or null", or angle-bracketed examples.