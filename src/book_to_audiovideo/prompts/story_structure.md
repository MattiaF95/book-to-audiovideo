Task: read the corrected text and identify the narrator, all recurring speakers, and the exact reading order.
Analyze the text as narrative prose, not as a flat sequence of sentences:
- Use paragraph boundaries as the first clue, but split a paragraph when it contains both narration and one or more quoted or clearly attributed dialogue turns.
- Treat `<< >>`, quoted speech, em dashes, and explicit speaker attributions as speaker cues.
- When narration surrounds a dialogue turn, create separate segments so the dialogue is isolated and assigned to the correct speaker.
- Prefer smaller, cleaner segments over one mixed segment if that improves speaker attribution.
- A narrator is a single stable speaker for the entire text: use one and only one `speaker_id` for narration everywhere, never create narrator variants for different moments.
- A single continuous speech turn must stay in one segment even if it contains periods, commas, semicolons, dashes, ellipses, parentheses, exclamation marks, question marks, symbols, or interruptions that do not change speaker.
- Do not split one speaker's dialogue into multiple people just because the text contains punctuation, symbols, or short narrative asides inside the same turn.
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
- Narration must map to one narrator only, with exactly one narrator speaker used across all narration segments.
- When `<<` opens a dialogue and `>>` closes it, treat the text inside as one dialogue turn unless there is a real speaker change inside the same block.
- A dialogue segment must contain one continuous turn by one speaker only.
- Do not split a dialogue because of commas, ellipses, punctuation, or internal pauses.
- Split only when the speaker changes or narration resumes.
- If a paragraph contains narration plus dialogue, split it into multiple segments at the transition points.
- If a quoted line is clearly spoken by a character, never label that whole mixed paragraph as narration.
- If a narration sentence introduces or follows a quoted line, keep the narration in its own segment unless it is inseparable from the dialogue turn.
- Use the dialogue delimiters and nearby attribution text to infer which speaker owns the turn before falling back to broader context.
- Infer speaker gender from explicit names, pronouns, titles, narration cues, and surrounding context.
- Use the explicit name in the text as a strong gender signal when it is clearly gendered or culturally associated, for example `Marco` -> `male`.
- If the text uses a relation or role instead of a name, infer gender from that relation and the surrounding context, for example `the sister said` -> `female`.
- Use `male` or `female` when the context makes it reasonably clear; use `null` only when the gender is genuinely ambiguous.
- For the narrator, choose the gender you judge most appropriate from the narrative context; if the narrator is clearly neutral or not inferable, use `null`.
- Reuse the same speaker_id for the same person everywhere in the story.
- If a speaker is unnamed, use a stable placeholder like `personaggio_1`.
- If a name is explicit, use it consistently.
- Do not invent extra speakers or backstories.
- Every segment must have exactly one resolved speaker.
