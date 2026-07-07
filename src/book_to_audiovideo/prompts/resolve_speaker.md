Task: resolve canonical speakers across the full ordered segment list.
Return only JSON:
{
  "speakers": [
    {
      "speaker_id": "string",
      "name": "string",
      "role": "narrator or character",
      "gender": "string or null",
      "continuity_key": "string",
      "preferred_voice_constraints": ["string"]
    }
  ],
  "segment_speaker_map": {
    "segment_id": "speaker_id"
  }
}
Rules:
- Build the smallest stable cast possible.
- Always keep narration on a dedicated narrator speaker when narration exists.
- Reuse the same `speaker_id` for the same person everywhere in the story, even after narration, description, or long gaps.
- Prefer merging over splitting. If two segments could plausibly be the same person, use the same speaker.
- Use `speaker_hint`, explicit names, dialogue markers, and the segment order to infer identity.
- If a speaker is unnamed, create a stable placeholder `speaker_id` like `personaggio_1`, `personaggio_2`, and reuse it for every matching segment.
- Respect `existing_speakers` as the canonical roster when present.
- Every `segment_id` must appear exactly once in `segment_speaker_map`.
- Do not leave dialogue unmapped.
