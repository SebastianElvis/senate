---
name: rfc-pipeline
description: Draft an RFC, distribute for parallel async comments, author revises, editor finalizes.
mode: pipeline
default_roster:
  author: claude
  reviewers: [codex, gemini, kimi]
  editor: claude
default_budget:
  wall_clock_sec: 3600
  total_tokens: 500000
---

# rfc-pipeline

Models the canonical IETF-style RFC process: draft → comment → revise → accept. Good for any document that will be widely read and needs input from a distributed group.

This file is a **template** — the planner expands it into a concrete `agenda.md` by substituting the user's roster, validating CLIs, and writing the result into the run dir. The placeholders `{author}`, `{reviewers}`, `{editor}` are filled at expansion time.

Takes ~1–2 hours of wall-clock when run autonomously, longer with human checkpoints.

## Expanded shape

```yaml
mode: pipeline
stages:
  - index: 1
    name: draft
    format: committee
    roster:
      - { role: member, cli: "{author}" }
      - { role: editor, cli: "{author}" }
    output_bindings:
      - { name: draft_doc, source: "verdict.md body" }
    checkpoint: optional        # user may review the draft before sending for comments

  - index: 2
    name: review
    format: rfc
    roster:
      - { role: author, cli: "{author}" }
      - { role: commenter, cli: "{reviewers[0]}" }
      - { role: commenter, cli: "{reviewers[1]}" }
      - { role: commenter, cli: "{reviewers[2]}" }
      - { role: editor, cli: "{editor}" }
    input_bindings: [draft_doc]
    output_bindings:
      - { name: annotated_doc, source: "verdict.md body" }
      - { name: disposition, source: "fenced-json.disposition" }
      - { name: resolution_rate, source: "fenced-json.resolution_rate" }
    checkpoint: conditional
    condition: "stage.bindings.disposition == \"withdrawn\""

  - index: 3
    name: synthesize
    format: committee
    roster:
      - { role: member, cli: "{author}" }
      - { role: editor, cli: "{editor}" }
    input_bindings: [annotated_doc, draft_doc]
    output_bindings:
      - { name: final_doc, source: "verdict.md body" }
    checkpoint: required        # user confirms final document before publication
```

## Why this pipeline

The shape mirrors how RFCs work in practice: an author drafts, a distributed group comments asynchronously, the author revises into a final form, and an editor signs off. Each stage's deliverable is a concrete artifact (draft, annotated doc, final doc).

## Failure modes

- **Stage 1 fails** — unusable draft; the planner can be re-invoked with a different author.
- **Stage 2 has `resolution_rate < 0.5`** — pipeline continues but the synthesize stage's prompt is enriched with a warning that many comments went unaddressed.
- **Stage 3 fails the checkpoint** (user rejects) — user may revise manually and resume, or abort.

## Verdict shape (for evals fixtures)

The top-level `verdict.md` follows the canonical multi-stage shape in `../../meeting-note/references/verdict-schema.md`. Inside its `## Final deliverable` section, this pipeline produces:

- **Final Document** — the published RFC text.
- **Process summary** — a short narrative of the comment + revision rounds.
- **Resolution rate** — the fraction of comments resolved (from stage 2's binding).

Plus:

- `state.json` status is `completed`.
- All three stages completed without `stalled` status.
- Resolution rate from stage 2 ≥ 0.6 on the shipped fixture.
