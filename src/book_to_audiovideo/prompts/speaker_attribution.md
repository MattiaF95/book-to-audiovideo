Task: assign each existing segment to one speaker from the provided speaker registry.
Return only JSON.
Do not produce reasoning, analysis, or thinking text. Return only the requested JSON object.
Use the provided speaker registry only. Reuse the same speaker_id for the same character across all matching segments.

{
  "assignments": [
    {
      "segment_id": "seg-N",
      "speaker_hint": "character name as it appears in text, or null",
      "resolved_speaker_id": "spk-N"
    }
  ]
}

Every segment in the input list MUST appear in the output assignments list. Do not skip any segment.

Attribution rules — apply in strict priority order:

1. NARRATION ALWAYS MAPS TO NARRATOR: Every segment with `segment_type` = `narration` must resolve to the narrator speaker_id. Do not assign narration to a character.

2. ADJACENT VERB OF SAYING: For each dialogue segment, first look at the immediately adjacent narration segment (before or after). If it contains a verb of saying with a character name (e.g. `disse Marco`, `gridò Giulia`, `interruppe`, `sussurrò Marco`), assign the dialogue segment to that character.

3. CONVERSATIONAL TURN ALTERNATION: If no verb of saying is present, infer the speaker from the conversational turn order. Characters typically alternate turns. Use the previous known speaker to determine who speaks next.

4. BROADER CONTEXT: If neither rule 2 nor rule 3 resolves the speaker, use the surrounding paragraph context (character names mentioned nearby, scene setup) to infer the speaker.

5. UNKNOWN SPEAKER: If the speaker cannot be resolved with confidence after applying rules 2-4, use the unknown or unnamed speaker entry from the registry if one exists. Do not invent a new speaker_id.

Additional rules:
- Use only speaker_id values already present in the input speakers list. Never invent new ones.
- Assign every dialogue segment to exactly one speaker. Never leave resolved_speaker_id empty or null.
- Assign every narration segment to the narrator speaker_id.
- `speaker_hint` is the character name as written in the text (e.g. `Marco`, `Giulia`), or null if not explicitly named.
- Do not add emotions, importance scores, or extra fields.
- Do not create new speakers.
- Output one assignment object per input segment, in the same order as the input.
