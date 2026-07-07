Task: read the corrected text and identify the narrator, all recurring speakers, and the exact reading order.
Return only JSON:
{
  "speakers": [
    {
      "speaker_id": "string",
      "name": "string",
      "role": "narrator or character",
      "gender": "male, female, or null",
      "continuity_key": "string",
      "preferred_voice_constraints": ["string"]
    }
  ],
  "segments": [
    {
      "segment_id": "string",
      "order_index": 1,
      "raw_text": "string",
      "segment_type": "narration or dialogue",
      "speaker_hint": "string or null",
      "resolved_speaker_id": "string",
      "start_offset": 0,
      "end_offset": 0,
      "emotion_hint": "string or null",
      "importance_score": 0.0
    }
  ]
}
Rules:
- Keep the original reading order.
- Narration must map to one narrator only.
- A dialogue segment must contain one continuous turn by one speaker only.
- Do not split a dialogue because of commas, ellipses, punctuation, or internal pauses.
- Split only when the speaker changes or narration resumes.
- Reuse the same speaker_id for the same person everywhere in the story.
- If a speaker is unnamed, use a stable placeholder like `personaggio_1`.
- If a name is explicit, use it consistently.
- Do not invent extra speakers or backstories.
- Every segment must have exactly one resolved speaker.
