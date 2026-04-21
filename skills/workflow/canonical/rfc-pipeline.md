---
name: rfc-pipeline
description: Draft an RFC, distribute for parallel async comments, author revises, editor finalizes.
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

Takes ~1–2 hours of wall-clock when run autonomously, longer with human checkpoints.

## Stages

### 1. draft

- **Format:** `committee` (minimum roster: 1 member + 1 editor)
- **Roster:**
  - `member`: `{author}`
  - `editor`: `{author}` (author writes and edits their own draft)
- **Input:** original user task.
- **Output bindings:**
  - `draft_doc` ← `verdict.md body`
- **Checkpoint:** `optional` — user may review the draft before sending for comments.

### 2. review

- **Format:** `rfc`
- **Roster:**
  - `author`: `{author}`
  - `commenter`: each of `{reviewers}`
  - `editor`: `{editor}`
- **Input:** `draft_doc`.
- **Output bindings:**
  - `annotated_doc` ← `verdict.md body`
  - `disposition` ← `fenced-json.disposition`
  - `resolution_rate` ← `fenced-json.resolution_rate`
- **Checkpoint:** `conditional` on `disposition == "withdrawn"` — if withdrawn, pause so user can abort or restart.

### 3. synthesize

- **Format:** `committee` (single member + editor)
- **Roster:**
  - `member`: `{author}`
  - `editor`: `{editor}`
- **Input:** `annotated_doc`, `draft_doc`.
- **Output bindings:**
  - `final_doc` ← `verdict.md body`
- **Checkpoint:** `required` — user confirms final document before publication.

## Branching

None. RFC pipeline is strictly sequential.

## Failure modes

- **Stage 1 fails**: unusable draft; abort and retry with different author roster.
- **Stage 2 has `resolution_rate < 0.5`**: workflow continues but `synthesize` stage's prompt is enriched with a warning that many comments went unaddressed.
- **Stage 3 fails the checkpoint (user rejects)**: user may revise manually and resume, or abort.

## Verdict shape (for `senate-eval` fixtures)

- `workflow_verdict.md` contains sections: Final Document, Process Summary, Resolution Rate.
- `workflow_state.json` status is `completed`.
- All three stages completed without `stalled` status.
- Resolution rate from stage 2 ≥ 0.6 on the shipped fixture.
