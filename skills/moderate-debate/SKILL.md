---
name: moderate-debate
description: Drives a multi-agent debate from a planned agenda — invokes each CLI per turn, maintains the shared transcript and context, enforces output contracts and budget caps, handles failures, manages checkpoints, and adapts the agenda mid-run when the situation diverges from the plan. Use when senate has an agenda.md and needs the actual turns run.
---

# moderate-debate — run the debate from an agenda

You are the **moderator**. You did not plan the debate (the planner wrote `agenda.md`) and you do not synthesize the verdict (the meeting-note skill does). Your job is the live loop: read the agenda, run each turn, keep the records, enforce the rules, adapt when reality diverges from the plan.

A debate without a moderator is a chat. A moderator without an agenda is a chat with extra steps. Both pieces are required.

## When to trigger

Activate when:

- `senate` has an `agenda.md` ready and asks you to run it.
- A user resumes a paused run (resume the moderator at the next unfinished stage).
- The planner returns a revised agenda mid-run (continue from the next unfinished stage of the new agenda).

## Inputs

1. **Run directory** — `<cwd>/.senate/runs/<id>/`. Must already contain `agenda.md` with `status: ready`.
2. **(Optional) Resume signal** — if non-empty `transcript.jsonl` exists, resume from the last unfinished stage.

## Steps

### 1. Pre-flight

Read `agenda.md` and validate:

- `status: ready` (or `revising` after a re-plan).
- All `cli` values resolve to playbooks under `../invoke-agent/references/`.
- All `format` values resolve to format files under `../debate-agenda/formats/`.
- All `input_bindings` reference an `output_bindings` from an earlier stage.

If any check fails, do not start. Surface to the user via `senate`.

### 2. Initialize shared context

Each run dir contains a set of shared markdown files that agents read every turn (see `references/context.md`):

```
agenda.md             # the plan (already exists)
context.md            # shared scratchpad, free-form, append-only across turns
transcript.jsonl      # append-only structured per-turn record
agents/<cli>.md       # per-agent private memory (one file per CLI in the roster)
agents/<cli>.<turn>.log   # raw stdout per turn
```

On first start of a run: create empty `context.md` (with a brief header explaining its purpose) and an empty `agents/<cli>.md` for each unique CLI in the agenda.

### 3. Walk the stages

For each `stage` in `agenda.stages` (in `index` order):

1. Read `../debate-agenda/formats/<stage.format>.md`. The format file declares roles, phases, turn order, contracts, and termination.
2. Build the stage input prompt: framing wrapper + agenda body excerpt + input bindings (resolved values from prior stages).
3. For each phase the format specifies:
   - For each turn in the phase (sequential or parallel per the format):
     - Build the turn prompt (see "Turn prompt construction" below).
     - Invoke the CLI per `../invoke-agent/references/<cli>.md`.
     - Capture stdout to `agents/<cli>.<turn>.log`.
     - Validate the contract per `references/contracts.md`. Re-prompt once on first failure; on second failure, apply the format fallback.
     - Detect failures per `references/failures.md` and record.
     - Append a JSONL line to `transcript.jsonl`.
     - Apply context updates: any `context-delta` block from the agent's reply gets appended to `context.md`; the agent's own `agents/<cli>.md` gets updated from a `private-delta` block. See `references/context.md`.
4. Check budget per `references/budget.md` between turns. If a cap is near, gracefully terminate and skip to the stage's synthesis turn.
5. Extract the stage's `output_bindings` from the verdict.
6. Honor checkpoints per `references/checkpoints.md`. If a `required` or triggered `conditional` checkpoint fires, write checkpoint state and pause.

### 4. Turn prompt construction

Every turn prompt has these sections, in this order:

1. **Run header** — task, run_id, current stage name, format name. From `agenda.md`.
2. **Role brief** — from the format file. Who this agent is in this debate.
3. **Shared context** — full content of `context.md`. Read fresh each turn.
4. **Private memory** — full content of `agents/<cli>.md`. The agent's own scratchpad from prior turns.
5. **Transcript slice** — prior turns this role is allowed to see (some formats redact).
6. **Turn instruction** — what to produce this turn, including the output contract (fenced JSON) if any, and the fence labels for an optional `context-delta` block (free-form prose to append to shared context) and an optional `private-delta` block (free-form prose to append to the agent's own memory).

Pass the prompt via stdin (heredoc) per `../invoke-agent/SKILL.md`. Wrap in `timeout` per `references/budget.md`.

### 5. Adaptive moderation

The agenda is the plan, not a script. When reality diverges, decide whether to:

- **Continue as planned** — minor variance (one slow turn, one retried contract). Default.
- **Re-prompt** — agent's reply was off-spec but recoverable. Per `references/contracts.md`.
- **Apply format fallback** — agent failed twice. Per the format file's fallback rule.
- **Pause for the user** — checkpoint hit, or stage failed catastrophically (all agents refused, budget exhausted). Per `references/checkpoints.md`.
- **Call back to `debate-agenda` for a re-plan** — the situation has changed in a way the plan didn't anticipate (user changed direction, an agent kept refusing across stages, a checkpoint was rejected with a request for new structure). Pass: prior agenda, recent transcript slice, the reason. Receive: revised agenda. Resume at the next unfinished stage.

The bias should be toward continuing; only escalate when continuing would clearly produce a worse run.

### 6. Stage completion

When a stage's termination condition fires (per the format file), the moderator:

- Runs the stage's synthesis turn — one designated role per the format (speaker / judge / editor / synthesizer). The synthesis turn's structured output and prose become the stage's verdict content.
- Writes the stage's verdict to `<run-dir>/stages/<index>-<name>/verdict.md` (multi-stage runs only). Single-stage runs do not write a stage-level verdict file; the synthesis turn's text lives in `transcript.jsonl` and `meeting-note` reads it from there.
- Extracts `output_bindings` and writes them to `<run-dir>/bindings.json` (cumulative across stages).
- Honors any checkpoint declared on this stage.

The moderator does **not** write the top-level `<run-dir>/verdict.md` — that is `meeting-note`'s job. The format-level "speaker writes verdict.md" wording in the format files refers to the synthesis turn's *content production*, not to who writes the canonical top-level file.

### 7. Hand off

When the last stage finishes:

- Update `<run-dir>/state.json`: `status: completed`, `completed_at: "..."`. Full schema in `../senate/references/workspace.md` (`## state.json schema`).
- Return to `senate` with a one-line summary and the path to the run dir.

`senate` then invokes `meeting-note`, which writes both `verdict.md` and `meeting-notes.md`. The moderator never writes either.

## Single-stage vs multi-stage

There is one code path. A single-stage agenda walks one stage; a multi-stage agenda walks N. Bindings, checkpoints, and re-planning all work the same way.

## Resume from pause

If the moderator is invoked on a run dir that already has `transcript.jsonl` content, follow the full resume / crash-recovery / revise / re-plan flows in `references/checkpoints.md`. The moderator owns `state.json`; the planner owns `agenda.md`. After the appropriate flow, continue from the first unfinished stage per the (possibly revised) agenda.

## Files in this skill

- `SKILL.md` — this file.
- `references/context.md` — `context.md` (shared scratchpad) and per-agent memory file conventions.
- `references/contracts.md` — structured-output contract discipline.
- `references/failures.md` — error taxonomy and retry policy.
- `references/budget.md` — wall-clock, token, and per-turn caps.
- `references/checkpoints.md` — human-in-the-loop pause / resume.

## Related skills

- `../debate-agenda/` — produces the `agenda.md` this skill consumes; called back for mid-run re-plans. Format library at `../debate-agenda/formats/`.
- `../invoke-agent/` — per-CLI invocation playbooks.
- `../meeting-note/` — runs after the moderator finishes; consolidates the transcript into user-facing notes.
