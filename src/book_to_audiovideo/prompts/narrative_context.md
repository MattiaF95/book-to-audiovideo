Task: infer only the global narrative context of the cleaned text.
Return only JSON:
Use real values, not placeholder literals from the schema.
{
  "context": {
    "scene": "string",
    "tone": "string",
    "setting": "string",
    "time_period": "string or null"
  }
}
Rules:
- Describe only global context useful for later planning.
- Keep the number of fields fixed and minimal.
- Do not segment the text.
- Do not identify speakers here.
- Do not infer per-segment emotions here.
