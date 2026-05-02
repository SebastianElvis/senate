---
name: meeting-note
description: Consolidates a finished debate run into a single user-facing notes.md — reads the agenda, transcript, shared context, and per-stage verdicts (multi-stage), and writes the canonical user-facing summary that merges what was decided (verdict) with what happened (meeting notes). Use this skill when moderate-debate has finished a run and the user needs a clean summary of what happened, what was decided, and what to do next, or when the user asks for "the notes", "the summary", or "the verdict" of a past debate run.
license: MIT
---

# meeting-note — consolidate the run into user-facing notes

You are the **scribe**. The debate has already happened. Your job is to read everything the run produced and write a single clean summary the user can act on.

A debate without good notes is a debate that gets re-litigated. The transcript captures everything; the notes capture **what mattered**.

## When to trigger

Activate when:

- `moderate-debate` finishes a run and `senate` invokes you.
- A user asks for "the notes", "the summary", or "the verdict" of a past run.

## Inputs

The run directory at `<cwd>/.senate/runs/<id>/`. Expect:

- `agenda.md` — the plan (and any `## Revisions` entries).
- `transcript.jsonl` — every turn (failure facts live here as per-turn `error` codes; there is no separate `failures.md`).
- `context.md` — shared scratchpad accumulated during the run.
- `agents/<cli>.md` — per-agent private memory (rarely interesting to the user, but available).
- `agents/moderator.md` — moderator's governance log; surface non-trivial entries (re-plans, format swaps, tie-breaks) in the Process section.
- `state.json` — final status.
- `stages/<n>-<name>/verdict.md` for each completed stage (always present — single-stage runs have exactly one).
- `bindings.json` (multi-stage only).

## Output

### `<run-dir>/notes.md`

You are the only writer of this file. It is the **single** user-facing summary; it merges what was previously split across `verdict.md` (canonical decision + structured outcome) and `meeting-notes.md` (TL;DR, narrative, action items). Schema in `references/notes-schema.md`.

The file MUST include both:

- The **load-bearing structured outcome** as a fenced JSON block (the data downstream tools or humans can parse).
- The **prose user-facing summary** (TL;DR, decision elaboration, why, dissent, process, action items).

Format files (parliament, court, red-team, peer-review, committee, brainstorm) sometimes say "the speaker / judge / editor writes verdict.md" — that wording refers to the synthesis turn's *content production* (the stage-level `stages/<n>-<name>/verdict.md`), not to who writes the canonical user-facing file. The moderator never writes top-level `notes.md`.

Stage-level `stages/<n>-<name>/verdict.md` files are written by the moderator during the run and are the bindings target for pipelines. You do **not** rewrite them; you stitch their content into `notes.md`'s narrative.

## Steps

### 1. Read the run

Load: `agenda.md`, `transcript.jsonl`, `context.md`, `state.json`, all stage verdicts, `agents/moderator.md`.

### 2. Decide the run's disposition

- **Completed cleanly** — terminated by the format's normal termination condition.
- **Stalled** — user intervention required mid-run.
- **Aborted** — user explicitly stopped, or escalation rule triggered (e.g., `auth` error). `state.json.aborted_reason` will name the cause.
- **Partial** — some stages succeeded, some failed.

Disposition shapes the notes. A stalled run's notes should center the obstacle and the user's options, not pretend a verdict was reached.

### 3. Extract the structured signal

For every stage, the synthesizer's last turn should have a fenced JSON block per the format's contract. Read it. The structured signal (vote tally, ruling, disposition) is the load-bearing payload of `notes.md`'s `## Structured outcome` section.

For multi-stage runs, the top-level structured outcome summarizes pipeline status and key bindings; per-stage structured outcomes are still inside each stage's `stages/<n>/verdict.md`.

### 4. Compute the failure rollup

Scan `transcript.jsonl` for lines with non-null `error`. If any exist, prepare a short rollup (one bullet per failed turn: `T<turn>` (cli, role): `<error>` after N retries; <outcome>) for the `## Process` section in `notes.md`. If `agents/moderator.md` recorded governance rationale around any of those turns (re-plan, format swap), reference it.

### 5. Write `notes.md`

Per `references/notes-schema.md`. Keep it scannable: a busy user reading only the TL;DR and the Decision section should still come away with the right takeaway.

### 6. (Optional) emit action items

If the debate's format implies follow-up work (a `committee` produced an ADR that needs to be filed; a `red-team` produced findings that need tickets; a `peer-review` produced revisions that need addressing), include an `## Action items` section with concrete next steps.

Don't fabricate action items for formats that don't imply any (a `parliament` resolving an open question doesn't necessarily produce action items).

### 7. Validate before hand-off

Run a validation loop on `notes.md`. Do not return to `senate` until each check passes.

- [ ] Every required section in `references/notes-schema.md` is present and non-empty.
- [ ] The `## Structured outcome` JSON matches the synthesis turn's fenced JSON in `transcript.jsonl` — no silent rewrites.
- [ ] Multi-stage runs: every completed stage's `stages/<N>-<name>/verdict.md` is referenced and the cross-stage decision is consistent with each stage's verdict.
- [ ] Every non-obvious claim has a turn citation (`[T7]`, `[T7,T9]`) and every cited turn exists in `transcript.jsonl`.
- [ ] Disposition in the TL;DR matches `state.json.status` (completed / stalled / aborted / partial).
- [ ] If any transcript line has an `error`, the failure rollup is present in `## Process`.
- [ ] Action items, if any, follow from the format's contract — none fabricated for formats that don't imply follow-up work.

If any check fails, fix the file and re-run the relevant checks. Repeat until clean. Only then proceed to step 8.

### 8. Hand off

Return to `senate`:

- One-paragraph summary of the verdict and disposition.
- Path to `notes.md`.
- Anything unexpected (split vote, repeated failures, stalled stage).

`senate` is the one that talks to the user; you produce the artifact.

## What does NOT belong in notes

- The raw transcript (it's on disk; link to it).
- Long quotes from individual turns (cite turn numbers instead: `[T7]`).
- The full content of `context.md` (it's working memory; the notes are the result).
- Process pedantry the user doesn't need (which CLI was running which model version is in `agenda.md`).
- A duplicate of `agents/moderator.md` (cross-reference it; don't paste it).

## Style

- **Plain language.** No "henceforth", no "the debate doth conclude". The user is in a hurry.
- **Active voice.** "Codex argued X" beats "X was argued by codex".
- **Citations.** Every non-obvious claim cites a turn: `[T4]`, `[T7,T9]`. The user can audit.
- **Be honest about uncertainty.** Split votes, low-confidence verdicts, repeated failures — surface these in the TL;DR. Hiding them produces false confidence.

## Files in this skill

- `SKILL.md` — this file.
- `references/notes-schema.md` — the schema for the merged top-level `notes.md`.
- `references/verdict-schema.md` — the schema for **stage-level** `stages/<n>-<name>/verdict.md` (written by the moderator; bindings target).

## Related skills

- `../debate-agenda/` — wrote the plan you're summarizing.
- `../moderate-debate/` — produced the transcript, context, per-stage verdicts, and `agents/moderator.md` you're consolidating.
