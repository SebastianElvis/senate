# `verdict.md` schema

The verdict is the canonical output of a debate. It is short, structured, and citable. It should be possible to read it in 60 seconds and know what was decided.

## Single-stage verdict

Lives at `<run-dir>/verdict.md`.

```markdown
# Verdict — <format>

**Task:** <one-line task>
**Run:** `.senate/runs/<id>/`
**Roster:** <role: cli>, <role: cli>, ...
**Disposition:** completed | stalled | aborted | partial

## Decision

<one paragraph: what was decided. For voting formats, include the tally. For ruling formats, the ruling. For consensus, the converged-upon plan in 3-5 sentences.>

## Rationale

<bullets, each citing turn numbers like [T4], [T7]. 3–6 bullets is typical. Each bullet captures one load-bearing reason.>

## Dissent

<minority opinion, if any. Empty section header if unanimous. Cite the dissenting turn(s).>

## Structured outcome

\`\`\`json
{
  "format": "parliament",
  "decision": "no",
  "tally": {"yes": 1, "no": 2, "abstain": 0},
  "confidence": 0.7,
  "dissent_present": true
}
\`\`\`

---

**Run budget:** Xm Ys wall / cap • Zk tokens / cap • N timeouts/failures
```

## Multi-stage verdict

Lives at `<run-dir>/verdict.md`. Stitches together the per-stage verdicts (which already exist at `<run-dir>/stages/<N>-<name>/verdict.md`).

```markdown
# Verdict — <agenda-name> pipeline

**Task:** <one-line task>
**Run:** `.senate/runs/<id>/`
**Pipeline:** <stage-1 (format)> → <stage-2 (format)> → ... → <stage-N (format)>
**Disposition:** completed | stalled | aborted | partial

## Outcome

<one paragraph: what the pipeline as a whole produced. Reference the final stage's deliverable.>

## Stage trail

| Stage | Format | Disposition | Verdict |
| --- | --- | --- | --- |
| 1. draft | committee | completed | [stages/1-draft/verdict.md](stages/1-draft/verdict.md) |
| 2. review | rfc | completed | [stages/2-review/verdict.md](stages/2-review/verdict.md) |
| 3. synthesize | committee | completed | [stages/3-synthesize/verdict.md](stages/3-synthesize/verdict.md) |

## Final deliverable

<the artifact the pipeline produced — a draft doc, a ruling, a spec. Either inline if short, or a path to where it lives.>

Each canonical pipeline declares the **inner** structure of this section in its own "Verdict shape" section (e.g., `bill-to-law` produces "Final Law Text / Vote Record / Dissent / Public Comment Summary" subsections within `## Final deliverable`). The top-level shape (Task / Run / Pipeline / Disposition / Outcome / Stage trail / Final deliverable / Open questions / Structured outcome) is fixed by this schema.

## Open questions

<questions the pipeline did not resolve, if any.>

## Structured outcome

\`\`\`json
{
  "pipeline": "rfc-pipeline",
  "stages_completed": 3,
  "stages_stalled": 0,
  "final_disposition": "completed",
  "key_bindings": {
    "final_doc": "<path or short value>"
  }
}
\`\`\`

---

**Run budget:** Xm Ys wall / cap • Zk tokens / cap • N timeouts/failures
```

## Verdict vs. meeting notes

The **verdict** is short and canonical: what was decided. The **meeting notes** are denser and more user-facing: what happened, why, and what to do next. The verdict is what downstream stages bind against; the notes are what the human reads.

Both are written by `meeting-note`. Keep them in sync — if you discover something in the transcript that changes the rationale, update both files.

## Citations

Every non-obvious claim in the verdict cites a turn number. Format: `[T4]` or `[T4, T7]` or `[T4–T9]` (for a range). Cite the turn that **produced** the claim, not the turn that referenced it.

For multi-stage verdicts, cite as `[stage-2 T4]` if a turn from a non-final stage matters.

## Disposition meanings

- **`completed`** — every stage's termination condition fired normally. The verdict reflects what the synthesizer/judge/editor produced.
- **`stalled`** — the run paused because of an obstacle (budget, repeated failures, all agents refused). The verdict still gets written, but the Decision section names the obstacle and proposes options.
- **`aborted`** — the user explicitly stopped the run. The verdict captures what was reached so far.
- **`partial`** — for branched pipelines, some branches succeeded and some failed. The verdict documents what each branch produced.

A stalled or partial verdict is **not** a failure to deliver — it's an honest record. The meeting notes will surface the issue prominently.

## Length budget

- Single-stage verdict: 200–400 words. Anything longer is signal of poor synthesis.
- Multi-stage verdict: 300–600 words plus the stage trail table.

If the synthesizer turn produced a much longer verdict, summarize it here and link to the synthesizer's full reply (it's in the transcript).
