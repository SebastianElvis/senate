# `notes.md` schema

The single user-facing summary of the run. This file replaces the old `verdict.md` + `meeting-notes.md` pair: it carries both the load-bearing structured outcome (which downstream tools and humans can parse) and the dense narrative (TL;DR, decision elaboration, rationale, dissent, process, action items).

Designed to be skimmed in under a minute and read in full in under five.

Lives at `<run-dir>/notes.md`. Written by `meeting-note`.

## Shape — single-stage run

```markdown
# <agenda-name>

**Task:** <one-line task>
**Run:** `.senate/runs/<id>/`
**When:** <ISO date> ・ <wall-clock duration>
**Format:** <format>
**Roster:** <role: cli>, <role: cli>, ...
**Disposition:** completed | stalled | aborted | partial

## TL;DR

<one paragraph, ~3 sentences. The thing a busy reader gets if they read nothing else. Includes the decision, the confidence level, and any major caveat.>

## Decision

<2-4 sentences elaborating the verdict. For voting formats, include the tally. For consensus, the converged plan in plain prose. For court, the ruling.>

## Why

<3–6 bullets, each citing turn numbers. Each bullet captures one load-bearing reason. Order: most load-bearing first.>

- <reason 1> [T4, T7]
- <reason 2> [T9]
- ...

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

## What didn't get resolved

<Open questions, dissent, anything the format flagged as remaining work. Empty section header if everything's tied off.>

- <open question 1>
- <dissent point, citing turn>

## Process

<short prose: how the debate ran. Who advocated for what (most useful in adversarial formats). Whether anyone changed their mind.>

If any transcript line has a non-null `error`, surface a failure rollup here:

> **Failures:** T7 (gemini, rebuttal): rate_limit after 2 retries; continued. T11 (codex, vote): contract_violation on retry; recorded as abstain.

If `agents/moderator.md` recorded non-trivial governance decisions (re-plans, format swaps, tie-breaks), reference them by their cross-link IDs.

## Action items

<concrete next steps, if the format implies any. One bullet per item, with an owner if obvious.>

- [ ] <action item 1>
- [ ] <action item 2>

## Artifacts

- [Full transcript](transcript.jsonl)
- [Shared context](context.md)
- [Stage 1 verdict](stages/1-<format>/verdict.md)

---

**Run budget:** Xm Ys wall / cap • Zk tokens / cap • N timeouts/failures
```

## Shape — multi-stage run (pipeline)

The same shape, with two adjustments: the `## Decision` section names the pipeline-level outcome (not stage 1's), and the `## Artifacts` section links each stage's verdict.

```markdown
# <agenda-name> pipeline

**Task:** <one-line task>
**Run:** `.senate/runs/<id>/`
**When:** <ISO date> ・ <wall-clock duration>
**Pipeline:** <stage-1 (format)> → <stage-2 (format)> → ... → <stage-N (format)>
**Roster:** ...
**Disposition:** ...

## TL;DR

...

## Decision

<one paragraph: what the pipeline as a whole produced. Reference the final stage's deliverable.>

## Stage trail

| Stage | Format | Disposition | Verdict |
| --- | --- | --- | --- |
| 1. draft | committee | completed | [stages/1-draft/verdict.md](stages/1-draft/verdict.md) |
| 2. review | rfc | completed | [stages/2-review/verdict.md](stages/2-review/verdict.md) |
| 3. synthesize | committee | completed | [stages/3-synthesize/verdict.md](stages/3-synthesize/verdict.md) |

## Final deliverable

<the artifact the pipeline produced — a draft doc, a ruling, a spec. Either inline if short, or a path to where it lives.>

Each canonical pipeline declares the **inner** structure of this section in its own "Verdict shape" section (e.g., `bill-to-law` produces "Final Law Text / Vote Record / Dissent / Public Comment Summary" subsections). The top-level shape (header / TL;DR / Decision / Stage trail / Final deliverable / Why / Structured outcome / What didn't get resolved / Process / Action items / Artifacts) is fixed by this schema.

## Why

...

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

## What didn't get resolved

...

## Process

...

## Action items

...

## Artifacts

- [Full transcript](transcript.jsonl)
- [Shared context](context.md)
- [Bindings](bindings.json)
- [Stage 1 verdict](stages/1-draft/verdict.md)
- [Stage 2 verdict](stages/2-review/verdict.md)
- [Stage 3 verdict](stages/3-synthesize/verdict.md)

---

**Run budget:** ...
```

## Section-by-section guidance

### TL;DR

One paragraph, ~3 sentences. Must include:

- The decision (what was decided).
- The confidence (was this a clean call or contested?).
- The biggest caveat (what could change this?).

If you can't write a clean TL;DR, the verdict probably has a problem worth surfacing in `## What didn't get resolved`.

### Decision

Elaborates the TL;DR with concrete numbers (vote tally, confidence) and reflects the structured outcome below. For multi-stage runs, the decision is the pipeline's overall outcome, not stage 1's.

### Why

The rationale section. Bullets, each citing one or two turns. Start each bullet with the **claim**, not the citation. Example:

- Migration risk dominates expected gains [T4, T7]

Not:

- [T4, T7] argued that migration risk dominates expected gains

### Structured outcome

A fenced `json` block. This is the load-bearing payload — the part downstream tools or eval harnesses parse. It must match the synthesis turn's fenced JSON in `transcript.jsonl`; do not silently rewrite it. For multi-stage runs, this is the pipeline-level rollup; per-stage structured outcomes stay inside each stage's `stages/<n>/verdict.md`.

### What didn't get resolved

Be honest. If the vote was 2-1 with strong dissent, surface it here. If a stage stalled, surface what stalled it. If the synthesis flagged remaining concerns, list them.

### Process

The narrative section. Describe how the debate flowed, not just what was decided. Useful when:

- The user wants to know which CLI played which role well (informs future roster choices).
- Someone changed their mind mid-debate (a minority position became persuasive).
- The format encountered something unusual (unanimous from a parliament; a court that remanded).

If the run had any failures (transcript lines with non-null `error`), include a one-paragraph failure rollup here. If `agents/moderator.md` recorded notable governance decisions, reference them.

Keep this to ~5 sentences (excluding the failure rollup). Don't recap every turn.

### Action items

Only when the format implies them:

- `committee` produced a doc → file the doc, circulate for sign-off.
- `red-team` produced findings → open tickets for each.
- `consensus` produced a spec → implement, validate.
- `peer-review` produced revisions → author addresses each.

For formats whose output is just a decision (parliament, court, oracle), action items are usually empty unless the user specifically asked for them.

Use markdown checkboxes (`- [ ]`) so the user can check them off in their host agent.

## Citations

Every non-obvious claim cites a turn number. Format: `[T4]` or `[T4, T7]` or `[T4–T9]` (for a range). Cite the turn that **produced** the claim, not the turn that referenced it.

For multi-stage notes, cite as `[stage-2 T4]` if a turn from a non-final stage matters.

## Disposition meanings

- **`completed`** — every stage's termination condition fired normally. The notes reflect what the synthesizer/judge/editor produced.
- **`stalled`** — the run paused because of an obstacle (budget, repeated failures, all agents refused). The notes still get written, but the Decision section names the obstacle and proposes options.
- **`aborted`** — the user explicitly stopped the run, or an escalation rule (e.g., `auth` failure) terminated it. `state.json.aborted_reason` will name the cause; surface it in the TL;DR.
- **`partial`** — for branched pipelines, some branches succeeded and some failed. The notes document what each branch produced.

A stalled, aborted, or partial disposition is **not** a failure to deliver — it's an honest record. Surface it prominently.

## Length budget

- Single-stage notes: 400–800 words.
- Multi-stage notes: up to 1200 words plus the stage trail table.

The transcript is on disk — don't re-narrate it here.

## Tone

Plain language. Direct. The user paid for a debate; deliver the result. Don't pad. Don't editorialize ("interestingly", "fascinatingly"). Don't apologize for failures — record them and move on.
