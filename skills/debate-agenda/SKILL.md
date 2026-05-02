---
name: debate-agenda
description: Plans the agenda for a multi-agent debate — picks the format, picks the roster, sequences stages, resolves sub-debate composition, and asks the user for clarification when the request is ambiguous. Use this skill when the senate orchestrator needs an agenda before debating, when the user asks "which format should I use for X?" or "how should we structure this debate?", or when the user describes a multi-step decision (e.g., "draft an RFC, have it reviewed, then vote") that needs stages laid out.
license: MIT
---

# debate-agenda — plan the debate before running it

You are the **agenda planner**. You do not run any turn. You produce `agenda.md`: a single document the moderator (and every participating agent) reads to know what is being debated, by whom, in what order, with what handoffs, and against what budget.

A good agenda is the difference between a debate that converges and one that thrashes. Plan first, debate second.

## When to trigger

Activate when:

- `senate` is invoked with `prepare_agenda: true` (or auto-detects an ambiguous request).
- The user asks *"which format should I use for X?"*.
- The user describes a multi-step decision (*"draft an RFC, have it reviewed, then vote on it"*) and the moderator needs the stages laid out.
- A prior agenda's situation has changed mid-run and the moderator asks for a re-plan.

If the user already supplied a complete debate spec (format, roster, rounds, single-stage), you may produce a minimal agenda directly without clarification questions.

## Inputs

1. **Task** — the question, artifact, or decision to debate.
2. **User-supplied hints** — any of: format, roster, rounds, budget, multi-stage intent, composition (e.g., "the jury is itself a consensus").
3. **Prior agenda** (optional) — if re-planning mid-run, the previous `agenda.md` plus the current `transcript.jsonl` slice.

## Steps

### 1. Clarify if needed

Walk this checklist. Ask **at most one** clarifying question per missing piece, and only when the answer materially changes the agenda:

- **Task unclear** (vague subject, no artifact, two interleaved questions) → ask. See `references/clarification.md`.
- **Single vs. multi-stage** ambiguous → ask. *"Is this one debate, or a pipeline (e.g., draft → review → vote)?"*
- **Format unspecified** → don't ask; pick per `references/format-selection.md` and surface the rationale in the agenda.
- **Roster unspecified** → ask if multi-stage; otherwise default to `codex, gemini, claude` and surface in the agenda.
- **Composition** (jury-of-consensus, MP-as-committee) → only ask if the user gestured at it ("a jury that's itself a debate") but didn't pin it down.

Never ask more than two questions before producing the agenda. If still ambiguous, produce the best-fit agenda and flag uncertainty in the agenda's `## Open questions` section.

### 2. Pick the format(s)

For a single debate, walk the decision tree in `references/format-selection.md`. For a multi-stage decision, sequence formats per `references/stages.md` (commonly: explore → draft → review → finalize).

For composed roles (a role filled by a sub-debate rather than a single CLI), see `references/composition.md`.

### 3. Pick the roster

Default `codex, gemini, claude` for 3-role formats. Add `kimi` and `cursor` for ≥4-role formats. Honor user overrides verbatim. Validate that every CLI named has a playbook in `../invoke-agent/references/`.

### 4. Sequence stages and bindings

Single-stage: skip. Multi-stage: declare each stage's format, roster, input bindings (which prior stages' outputs feed in), output bindings (named values extracted from this stage's verdict), and any checkpoint between this stage and the next. See `references/stages.md` for the binding grammar.

For parallel branches (e.g., security review and perf review running concurrently before a merge), see `references/branching.md`.

### 5. Set budget and checkpoints

Budget defaults from `../moderate-debate/references/budget.md`. Override per stage if any stage is known-expensive (e.g., a 5-commenter `rfc` stage). Checkpoint defaults: none for autonomous runs; `required` before publication-bound stages. See `../moderate-debate/references/checkpoints.md`.

### 6. Write `agenda.md`

Write the agenda to `<run-dir>/agenda.md` using the schema in `references/agenda-schema.md`. The agenda is **the living plan**: the moderator may update it mid-run (e.g., add a stage, swap a CLI) but every change appends a `## Revisions` entry — never silently rewrite the original.

### 7. Hand off

Return to the caller (usually `senate`):

- Path to `agenda.md`.
- One-paragraph summary: format(s), roster, stage count, expected budget, any open questions surfaced.
- Whether the agenda is `ready` (start moderating) or `pending_clarification` (caller must ask the user something before moderation begins).

## Re-planning mid-run

`moderate-debate` may call back here when the situation diverges from the plan — e.g., a CLI keeps refusing, the format's termination condition fires unexpectedly, the user changes their mind. Inputs in that case: prior `agenda.md` + recent transcript slice + reason. Output: a revised `agenda.md` with a new `## Revisions` entry recording what changed and why, and the agenda's `status` field set back to `ready` so the moderator can resume immediately.

The planner only writes to `agenda.md` (the agenda's `status` field). It does not touch the run's `state.json` (the run's `status` field) — that file is the moderator's responsibility, and the moderator clears any `revising` state on `state.json` once the new agenda is in hand. The moderator picks up from the next unfinished stage.

## Reference loading rules

Load each file **only** when the trigger condition fires. Loading everything up front wastes context and surfaces irrelevant guidance.

| File | Load when |
| --- | --- |
| `references/agenda-schema.md` | Always, before writing `agenda.md` (step 6). |
| `references/format-selection.md` | Format is unspecified or ambiguous (step 2). Skip if the user named a format. |
| `references/stages.md` | Multi-stage agenda — sequencing or binding work (step 4). Skip for single-stage. |
| `references/composition.md` | A role is filled by a sub-debate ("a jury that's itself a consensus"). Skip otherwise. |
| `references/branching.md` | Two or more sub-pipelines run in parallel before a join. Skip otherwise. |
| `references/clarification.md` | Step 1 indicates a clarifying question is needed. Skip if the request is already complete. |
| `formats/<name>.md` | Exactly one primitive per stage: the format file you have chosen. Do not pre-load the whole library. |
| `formats/README.md` | Browsing the catalogue when no format clearly fits. Skip once a format is chosen. |
| `../moderate-debate/references/budget.md` | Step 5, only if a stage needs a non-default budget. |
| `../moderate-debate/references/checkpoints.md` | Step 5, only if any stage needs a checkpoint. |

## Files in this skill

- `SKILL.md` — this file.
- `references/format-selection.md` — decision tree for picking a single format.
- `references/stages.md` — multi-stage agendas, bindings, handoffs.
- `references/composition.md` — roles filled by sub-debates.
- `references/branching.md` — parallel sub-pipelines.
- `references/clarification.md` — when and how to ask the user.
- `references/agenda-schema.md` — the on-disk schema for `agenda.md`.
- `formats/<name>.md` — primitive playbook library. Five single-stage primitives (parliament, court, panel, workshop, brainstorm) — court / panel / workshop are closed families with named presets (e.g., `court:appeals-court`, `panel:oracle`, `workshop:committee`). Multi-stage pipelines (rfc-pipeline, design-review, bill-to-law, incident-post-mortem) are recipes in `references/stages.md`; each stage points to one of these primitive files.

## Related skills

- `../invoke-agent/` — per-CLI invocation playbooks (used to validate roster).
- `../moderate-debate/` — consumes `agenda.md` and runs the debate.
- `../meeting-note/` — consumes the completed transcript and writes the final notes.
