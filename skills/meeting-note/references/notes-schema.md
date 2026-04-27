# `meeting-notes.md` schema

The user-facing summary of the run. Denser than the verdict; lighter than the transcript. Designed to be skimmed in under a minute and read in full in under five.

Lives at `<run-dir>/meeting-notes.md`.

## Shape

```markdown
# Meeting notes — <agenda-name>

**Task:** <one-line task>
**Run:** `.senate/runs/<id>/`
**When:** <ISO date> ・ <wall-clock duration>
**Format:** <format(s)>
**Roster:** <role: cli>, ...
**Disposition:** <one-word disposition>

## TL;DR

<one paragraph, ~3 sentences. The thing a busy reader gets if they read nothing else. Includes the decision, the confidence level, and any major caveat.>

## Decision

<2-4 sentences elaborating the verdict. For voting formats, include the tally. For consensus, the converged plan in plain prose. For court, the ruling.>

## Why

<3–6 bullets, each citing turn numbers. Each bullet captures one load-bearing reason. Order: most load-bearing first.>

- <reason 1> [T4, T7]
- <reason 2> [T9]
- ...

## What didn't get resolved

<Open questions, dissent, anything the format flagged as remaining work. Empty section header if everything's tied off.>

- <open question 1>
- <dissent point, citing turn>

## Process

<short prose: how the debate ran. Who advocated for what (most useful in adversarial formats). Whether anyone changed their mind. Any failures.>

If `failures.md` exists, link to it: `See [failures.md](failures.md) for details.`

## Action items

<concrete next steps, if the format implies any. One bullet per item, with an owner if obvious.>

- [ ] <action item 1>
- [ ] <action item 2>

## Artifacts

- [Verdict](verdict.md)
- [Full transcript](transcript.jsonl)
- [Shared context](context.md)
<one bullet per stage's verdict for multi-stage runs>
- [Stage 1 verdict](stages/1-draft/verdict.md)
- [Stage 2 verdict](stages/2-review/verdict.md)
- ...

---

**Budget:** Xm Ys wall / cap • Zk tokens / cap • N failures
```

## Section-by-section guidance

### TL;DR

One paragraph, ~3 sentences. Must include:

- The decision (what was decided).
- The confidence (was this a clean call or contested?).
- The biggest caveat (what could change this?).

If you can't write a clean TL;DR, the verdict probably has a problem worth surfacing in `## What didn't get resolved`.

### Decision

Elaborates the TL;DR with concrete numbers (vote tally, confidence) and the structured outcome from the verdict's fenced JSON. For multi-stage runs, the decision is the pipeline's overall outcome, not stage 1's.

### Why

The rationale section. Bullets, each citing one or two turns. Start each bullet with the **claim**, not the citation. Example:

- Migration risk dominates expected gains [T4, T7]

Not:

- [T4, T7] argued that migration risk dominates expected gains

### What didn't get resolved

Be honest. If the vote was 2-1 with strong dissent, surface it here. If a stage stalled, surface what stalled it. If the synthesis flagged remaining concerns, list them.

### Process

The narrative section. Describe how the debate flowed, not just what was decided. Useful when:

- The user wants to know which CLI played which role well (informs future roster choices).
- Someone changed their mind mid-debate (a minority position became persuasive).
- The format encountered something unusual (unanimous from a parliament; a court that remanded).

Keep this to ~5 sentences. Don't recap every turn.

### Action items

Only when the format implies them:

- `committee` produced a doc → file the doc, circulate for sign-off.
- `red-team` produced findings → open tickets for each.
- `consensus` produced a spec → implement, validate.
- `peer-review` produced revisions → author addresses each.

For formats whose output is just a decision (parliament, court, oracle), action items are usually empty unless the user specifically asked for them.

Use markdown checkboxes (`- [ ]`) so the user can check them off in their host agent.

## Length budget

400–800 words for single-stage runs. Up to 1200 for multi-stage. The transcript is on disk — don't re-narrate it here.

## Tone

Plain language. Direct. The user paid for a debate; deliver the result. Don't pad. Don't editorialize ("interestingly", "fascinatingly"). Don't apologize for failures — record them and move on.
