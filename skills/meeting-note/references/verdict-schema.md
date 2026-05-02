# Stage `verdict.md` schema

The per-stage verdict is the synthesis turn's content for one stage of the run, written by the **moderator** at stage completion. It is the **bindings target** — pipeline `output_bindings` are extracted from this file (`verdict.md body`, `verdict.md section <name>`, `fenced-json.<field>`).

Lives at `<run-dir>/stages/<n>-<name>/verdict.md`. Always present (single-stage runs have exactly one stage and therefore exactly one stage verdict).

> **Not the user-facing summary.** That is `<run-dir>/notes.md`, written by `meeting-note` (this skill). The merged `notes.md` consolidates the run-wide TL;DR, decision narrative, action items, and a top-level structured outcome. See `notes-schema.md`.
>
> **Not user-edited under normal flow.** The moderator writes this file; the only time it is hand-edited is when the user picks `revise` at a checkpoint (see `../../moderate-debate/references/checkpoints.md`), in which case the moderator re-extracts bindings on resume.

## Shape

```markdown
# <stage-name> — <format>

**Stage:** <n>
**Run:** `.senate/runs/<id>/`
**Roster:** <role: cli>, <role: cli>, ...
**Disposition:** completed | stalled | aborted | partial

## Decision

<one paragraph: what was decided in this stage. For voting formats, include the tally. For ruling formats, the ruling. For draft-producing formats (committee, peer-review), the draft or its summary (or a path to where it lives).>

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
```

The shape is fixed by this schema; format files may add **named subsections** under `## Decision` that downstream stages can target via `verdict.md section <name>` bindings (e.g., `red-team` produces an `## Outstanding risks` subsection that downstream `committee` stages bind to).

## Bindings extraction

Pipelines reference this file in their `output_bindings`. Supported source forms (per `../../debate-agenda/references/stages.md`):

| Source | Meaning |
| --- | --- |
| `verdict.md body` | The full markdown body of this stage's verdict. |
| `verdict.md section <name>` | A named section (e.g., "Decision", "Rationale", "Outstanding risks"). |
| `fenced-json.<field>` | A field from the fenced JSON in `## Structured outcome`. |
| `transcript.<role>.last` | The last turn's `text` field for a given role (used when synthesis isn't a separate turn). |

The moderator extracts bindings at stage completion (and re-extracts on `revise` resume) and writes them to `<run-dir>/bindings.json`.

## Citations

Every non-obvious claim cites a turn number. Format: `[T4]` or `[T4, T7]` or `[T4–T9]` (for a range). Cite the turn that **produced** the claim, not the turn that referenced it.

## Disposition meanings

- **`completed`** — the format's normal termination condition fired.
- **`stalled`** — the stage paused mid-run (budget, repeated failures, all agents refused).
- **`aborted`** — the run was stopped during this stage.
- **`partial`** — some branches of a branched stage succeeded, some failed.

## Length budget

200–400 words plus the structured outcome JSON. If the synthesizer turn produced a much longer reply, summarize here and link to the synthesizer's full reply in the transcript.

## Why this is separate from `notes.md`

The stage verdict is a **machine-readable bindings source** with a fixed contract. The top-level `notes.md` is a **user-facing merged summary** that includes per-stage commentary, narrative, action items, and a pipeline-level structured outcome. Mixing the two would couple the bindings contract to the narrative contract — exactly the dual-write hazard the merged `notes.md` was created to remove at the run level.
