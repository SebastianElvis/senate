---
name: meeting-note
description: Consolidates a finished debate run into user-facing meeting notes — reads the agenda, transcript, shared context, per-stage verdicts (multi-stage), and any failures, and writes the canonical verdict.md plus meeting-notes.md. Use when moderate-debate has finished and the user needs a clean summary of what happened, what was decided, and what to do next.
---

# meeting-note — consolidate the run into user-facing notes

You are the **scribe**. The debate has already happened. Your job is to read everything the run produced and write a clean summary the user can act on.

A debate without good notes is a debate that gets re-litigated. The transcript captures everything; the meeting notes capture **what mattered**.

## When to trigger

Activate when:

- `moderate-debate` finishes a run and `senate` invokes you.
- A user asks for "the notes" or "the summary" of a past run.

## Inputs

The run directory at `<cwd>/.senate/runs/<id>/`. Expect:

- `agenda.md` — the plan (and any `## Revisions` entries).
- `transcript.jsonl` — every turn.
- `context.md` — shared scratchpad accumulated during the run.
- `agents/<cli>.md` — per-agent private memory (rarely interesting to the user, but available).
- `state.json` — final status.
- For single-stage runs: a synthesizer turn already in the transcript (judge / speaker / editor / synthesizer).
- For multi-stage runs: `stages/<N>-<name>/verdict.md` for each completed stage.
- `failures.md` (if any failures occurred).
- `bindings.json` (multi-stage only).

## Outputs

### `<run-dir>/verdict.md`

You are the only writer of the top-level `verdict.md`. Schema in `references/verdict-schema.md`.

- **Single-stage runs:** read the synthesizer turn's structured output and prose from `transcript.jsonl`, package them into the canonical verdict shape.
- **Multi-stage runs:** stitch each stage's `stages/<N>-<name>/verdict.md` (written by the moderator) into a top-level verdict. Each stage's own verdict file stays where it is; your job is the connective tissue.

Format files (parliament, court, …) sometimes say "the speaker writes verdict.md" — that wording refers to the synthesis turn's *content production*, not to who writes the canonical top-level file. The moderator never writes top-level `verdict.md`.

### `<run-dir>/meeting-notes.md`

The user-facing document. Schema in `references/notes-schema.md`. Includes:

- TL;DR (the one paragraph a busy reader gets).
- Decision (what was decided and by whom).
- Rationale (why, with turn references).
- Dissent / open questions (what wasn't resolved).
- Process summary (format, roster, budget, failures).
- Action items (concrete next steps if the format implies any).

### `<run-dir>/failures.md`

If failures occurred, the moderator already wrote a structured `failures.md`. You don't rewrite it; you reference it from the meeting notes.

## Steps

### 1. Read the run

Load: `agenda.md`, `transcript.jsonl`, `context.md`, `state.json`, all stage verdicts (multi-stage), `failures.md` if present.

### 2. Decide the run's disposition

- **Completed cleanly** — terminated by the format's normal termination condition.
- **Stalled** — user intervention required mid-run.
- **Aborted** — user explicitly stopped.
- **Partial** — some stages succeeded, some failed.

Disposition shapes the notes. A stalled run's notes should center the obstacle and the user's options, not pretend a verdict was reached.

### 3. Extract the structured signal

For every stage, the synthesizer's last turn should have a fenced JSON block per the format's contract. Read it. The structured signal (vote tally, ruling, disposition) is the load-bearing part of the verdict; the prose is around it.

### 4. Write `verdict.md`

Per `references/verdict-schema.md`. For single-stage: full verdict. For multi-stage: a top-level "what was decided across the pipeline" verdict that references each stage's own verdict file.

### 5. Write `meeting-notes.md`

Per `references/notes-schema.md`. The notes are denser and more user-facing than the verdict. They include process commentary the verdict doesn't (failure incidents, time spent, who was the strongest advocate for what).

Keep the notes scannable: a busy user reading only the TL;DR and the Decision section should still come away with the right takeaway.

### 6. (Optional) emit action items

If the debate's format implies follow-up work (a `committee` produced an ADR that needs to be filed; a `red-team` produced findings that need tickets; a `consensus` produced a spec that needs implementing), include an `## Action items` section with concrete next steps.

Don't fabricate action items for formats that don't imply any (a `parliament` resolving an open question doesn't necessarily produce action items).

### 7. Hand off

Return to `senate`:

- One-paragraph summary of the verdict and disposition.
- Path to `meeting-notes.md` and `verdict.md`.
- Anything unexpected (split vote, repeated failures, stalled stage).

`senate` is the one that talks to the user; you produce the artifacts.

## What does NOT belong in meeting notes

- The raw transcript (it's on disk; link to it).
- Long quotes from individual turns (cite turn numbers instead: `[T7]`).
- The full content of `context.md` (it's working memory; the notes are the result).
- Process pedantry the user doesn't need (which CLI was running which model version is in `agenda.md`).

## Style

- **Plain language.** No "henceforth", no "the debate doth conclude". The user is in a hurry.
- **Active voice.** "Codex argued X" beats "X was argued by codex".
- **Citations.** Every non-obvious claim cites a turn: `[T4]`, `[T7,T9]`. The user can audit.
- **Be honest about uncertainty.** Split votes, low-confidence verdicts, repeated failures — surface these in the TL;DR. Hiding them produces false confidence.

## Files in this skill

- `SKILL.md` — this file.
- `references/verdict-schema.md` — the schema for `verdict.md`.
- `references/notes-schema.md` — the schema for `meeting-notes.md`.

## Related skills

- `../debate-agenda/` — wrote the plan you're summarizing.
- `../moderate-debate/` — produced the transcript, context, and per-stage verdicts you're consolidating.
