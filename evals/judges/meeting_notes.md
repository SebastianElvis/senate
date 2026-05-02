# Judge — meeting-notes.md

You are reviewing the scribe's `meeting-notes.md`. The notes should be a faithful, fast-to-read summary of the verdict — not a re-derivation.

## Inputs

- **Verdict**: the canonical `verdict.md`.
- **Meeting notes**: the `meeting-notes.md` produced by the scribe.

## Rubric

Score 1–5 on each dimension.

1. **TL;DR fidelity** — does the TL;DR match the verdict's actual decision (not a softened or distorted version)?
2. **Readable in <60 seconds** — could a busy reader skim and grasp the decision? Walls of text score 1–2.
3. **Preserves disagreement** — if the verdict had dissent, do the notes mention it (not bury it)?
4. **Adds value over verdict** — do the notes provide context, next steps, or stakeholder framing — or do they just paraphrase the verdict word-for-word? Pure paraphrase scores 1–2.

## Pass/fail

Pass = mean ≥ 3.5 AND tl_dr_fidelity ≥ 4 (the TL;DR must not lie about the decision).

## Failure modes

- `tldr_distorts` — TL;DR contradicts or softens the verdict
- `wall_of_text` — too long to skim
- `buries_dissent` — disagreement omitted or hidden
- `pure_paraphrase` — nothing added beyond the verdict
- `missing_next_steps` — doesn't say what to do next when the verdict implies action

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
