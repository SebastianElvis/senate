# Judge — meeting_notes (narrative-grade rubric for notes.md)

You are reviewing the **narrative sections** of `notes.md` — TL;DR, Process, Action items, and the way the dense summary is presented to a busy reader. The decision-grade sections (Decision, Why, Structured outcome) are scored separately by the `verdict` rubric; here you are evaluating whether the user can act on this without reading the raw transcript.

## Inputs

- **Notes**: the `notes.md` produced by the run (the merged user-facing summary).

## Rubric

Score 1–5 on each dimension.

1. **TL;DR fidelity** — does the TL;DR match the actual decision (not a softened or distorted version)?
2. **Readable in <60 seconds** — could a busy reader skim TL;DR + Decision and grasp the outcome? Walls of text score 1–2.
3. **Preserves disagreement** — if the run had dissent, is it surfaced (not buried) in TL;DR / What didn't get resolved?
4. **Adds value over the raw decision** — do the narrative sections (Process, Action items) provide context, next steps, or stakeholder framing — or do they just paraphrase the Decision word-for-word? Pure paraphrase scores 1–2.

## Pass/fail

Pass = mean ≥ 3.5 AND tl_dr_fidelity ≥ 4 (the TL;DR must not lie about the decision).

## Failure modes

- `tldr_distorts` — TL;DR contradicts or softens the decision
- `wall_of_text` — too long to skim
- `buries_dissent` — disagreement omitted or hidden
- `pure_paraphrase` — narrative sections add nothing beyond the decision-grade sections
- `missing_next_steps` — Action items absent when the format clearly implies them (committee, red-team, peer-review)

## Output contract

```json
{
  "scores": {
    "tl_dr_fidelity": 1-5,
    "readable_under_60s": 1-5,
    "preserves_disagreement": 1-5,
    "adds_value_over_verdict": 1-5
  },
  "overall_score": 1.0-5.0,
  "pass": true|false,
  "failure_modes": [...],
  "reasoning": "2-4 sentences"
}
```
