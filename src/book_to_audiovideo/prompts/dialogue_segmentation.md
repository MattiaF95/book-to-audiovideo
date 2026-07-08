Task: split the cleaned text into ordered segments and label each one with exactly one of the two valid types below.
Return only JSON.
Do not produce reasoning, analysis, or thinking text. Return only the requested JSON object.
Use the schema as a shape only. Replace every placeholder with real values from the text.

Valid segment types:
- `narration`: prose, description, or action narration that contains NO direct speech inside quote delimiters.
- `dialogue`: ONLY the direct speech content including its delimiters (« », " ", or — ). Nothing else.

{
  "segments": [
    {
      "segment_id": "seg-N",
      "order_index": 1,
      "raw_text": "<verbatim segment text>",
      "segment_type": "narration",
      "start_offset": 0,
      "end_offset": 0
    }
  ]
}

Example — a single sentence containing both narration and dialogue MUST become two segments:

Input: `«Non muoverti,» sussurrò Marco, stringendo la torcia spenta.`

Correct output:
{
  "segments": [
    {
      "segment_id": "seg-1",
      "order_index": 1,
      "raw_text": "«Non muoverti,»",
      "segment_type": "dialogue",
      "start_offset": 0,
      "end_offset": 15
    },
    {
      "segment_id": "seg-2",
      "order_index": 2,
      "raw_text": "sussurrò Marco, stringendo la torcia spenta.",
      "segment_type": "narration",
      "start_offset": 16,
      "end_offset": 60
    }
  ]
}

WRONG output (do not do this — never mix narration and dialogue in one segment):
{
  "segments": [
    {
      "segment_id": "seg-1",
      "order_index": 1,
      "raw_text": "«Non muoverti,» sussurrò Marco, stringendo la torcia spenta.",
      "segment_type": "dialogue"
    }
  ]
}

Splitting rules — apply in strict priority order:

1. MANDATORY SPLIT ON DELIMITERS: Every opening « (or " or —) starts a new dialogue segment. Every closing » (or " or end-of-dash-speech) ends that dialogue segment. The delimiter characters are HARD boundaries. Never cross them.

2. SPLIT NARRATION FROM DIALOGUE WITHIN THE SAME SENTENCE: If a sentence contains both a narration fragment (verb of saying, action, description) and a quoted speech fragment, they MUST become separate segments. Do not merge them into one.

3. VERB OF SAYING GOES TO NARRATION: Phrases like `disse Marco`, `sussurrò`, `gridò Giulia`, `interruppe`, `rispose` are always narration, never dialogue. They belong in a narration segment either before or after the quoted speech.

4. SPLIT AT EVERY TRANSITION: Each change from narration to dialogue or from dialogue to narration requires a new segment. There is no minimum segment length. A segment of 3 words is valid.

5. CONTINUOUS QUOTED TURN: If the same character speaks and the quote is not interrupted by narration, keep the full quoted span in one dialogue segment. Do not split a quote in the middle.

6. READING ORDER: Output segments in the order they appear in the input text, left to right.

Additional rules:
- Output only segmentation. Do not assign speakers.
- Use only the exact values `narration` and `dialogue` for `segment_type`.
- `raw_text` must be the verbatim substring from the input. Do not paraphrase or shorten.
- Offsets are character positions (0-based) in the input text.
- Do not emit placeholder literals like `string`, `<unique segment id>`, or `<verbatim segment text>`.
- Do not add speaker fields, emotions, or importance scores.
