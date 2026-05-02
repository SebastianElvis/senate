---
name: senate
description: Top-level orchestrator for multi-agent debates between coding CLIs (codex, gemini, cursor, kimi, claude). Routes a request through three sub-skills — debate-agenda (plan), moderate-debate (run), meeting-note (consolidate) — and returns a verdict and meeting notes. Use this skill when the user wants a debate, second opinion, adversarial review, or cross-model consensus on a non-trivial question — even if they don't say "debate" — and especially when they say "debate", "parliament", "court", "consensus", "senate", "have X and Y argue", or "ask multiple models".
license: MIT
---

# senate — top-level debate orchestrator

You are the **orchestrator**, not the planner, not the moderator, not the scribe. Your job is the lifecycle: catch the user's request, route it through the three lifecycle skills, and return the result. Each phase has a dedicated sub-skill that knows how to do that phase well.

Glossary (used throughout this skill bundle, single canonical meaning):

- **Orchestrator** — the `senate` skill (this file): top-level lifecycle conductor.
- **Planner** — the `debate-agenda` skill: produces `agenda.md`.
- **Moderator** — the `moderate-debate` skill: runs turns from the agenda.
- **Scribe** — the `meeting-note` skill: writes `verdict.md` + `meeting-notes.md`.
- **Synthesizer** — the in-format role (speaker / judge / editor / arbiter / synthesizer) that produces a single stage's synthesis content. Distinct from the scribe.
- **Format** — the umbrella term for any debate playbook in `../debate-agenda/formats/`.
- **Primitive** — a single-stage format (parliament, court, panel, workshop, brainstorm).
- **Preset** — a named configuration of a primitive that is a closed family (e.g., `court:appeals-court`, `panel:rfc`, `workshop:committee`).
- **Pipeline** — a multi-stage format (rfc-pipeline, design-review, …) declared with `mode: pipeline`.
- **Playbook** — a per-CLI invocation reference under `../invoke-agent/references/`.
- **Run** — one execution; lives at `<cwd>/.senate/runs/<id>/`.

```
senate
  → debate-agenda     (optional)   — plan: pick format, pick roster, sequence stages, ask if needed
  → moderate-debate                 — run: drive turns, enforce contracts, manage context, handle failures
  → meeting-note                    — consolidate: write verdict.md and meeting-notes.md
```

## When to trigger

Activate when the user asks for any of:

- A debate, parliament, court, consensus, peer-review, brainstorm, RFC, etc., between multiple agents/models.
- A "second opinion" or "third opinion" from another CLI.
- Adversarial review where one model attacks and another defends.
- Cross-model agreement on a decision, design, or plan.
- A multi-stage decision pipeline (draft → review → finalize).

If the user just wants one model's answer, **do not use this skill** — call the CLI directly.

## Inputs

1. **Task** — the question or artifact to debate.
2. **Format** (optional) — parliament, court, panel, workshop, brainstorm; plus a preset where applicable (e.g., `court:red-team`, `panel:oracle`, `workshop:committee`). If unspecified, the planner will choose.
3. **Roster** (optional) — which CLIs participate. Default: `codex, gemini, claude`.
4. **Multi-stage hint** (optional) — pipeline language ("draft, then review") triggers multi-stage planning.
5. **`prepare_agenda`** (option) — `auto` (default) | `true` | `false`.
   - `auto`: planner runs if the request is ambiguous, format is unspecified, multi-stage is implied, or composition is gestured at; otherwise skipped.
   - `true`: planner always runs.
   - `false`: skip planner; senate writes a minimal `agenda.md` directly from the user's request and proceeds. Only use when the user has provided format + roster + rounds explicitly.

## Steps

### 1. Mint the run directory

Create `<cwd>/.senate/runs/<YYYY-MM-DD-HHMM>-<format-or-pipeline-name>/` (never in the skill dir). See `references/workspace.md` for the full layout.

### 2. Decide on the agenda

Based on `prepare_agenda`:

- **`auto` and request is well-specified** (format named, roster named, single-stage, no composition) — or **`false`**: write a minimal `agenda.md` directly from the user's request. The minimal agenda fills the same `references/agenda-schema.md` shape the planner would: one stage, format from the user, roster from the user (or default `codex, gemini, claude`), default budget from `../moderate-debate/references/budget.md`, `checkpoint: none`, `status: ready`. Validate per the schema; if validation fails, fall back to invoking `../debate-agenda/`.
- **`auto` and request is ambiguous** OR **`true`**: invoke `../debate-agenda/`. The planner produces `agenda.md`. If the planner returns `status: pending_clarification`, surface its question to the user, get the answer, and ask the planner to revise.

Either way, the agenda lives at `<run-dir>/agenda.md` with `status: ready` before step 3 begins. Senate does not touch `agenda.md` after step 3 — only the planner (via re-plan) writes to it.

### 3. Moderate the debate

Invoke `../moderate-debate/`. It reads `agenda.md` and runs the debate to completion (or pauses at a checkpoint). On a checkpoint pause, surface the checkpoint state to the user; on continue/revise/abort/re-plan, route accordingly.

### 4. Consolidate the result

When the moderator returns `status: completed` (or `stalled` / `aborted` with whatever was produced), invoke `../meeting-note/`. It writes `verdict.md` and `meeting-notes.md`.

### 5. Report back

Return to the user:

- A 2–4 sentence summary of what was decided.
- Path to `meeting-notes.md` and `verdict.md`.
- Any anomaly worth surfacing (split vote, repeated failures, stalled stage).

Do **not** dump the full transcript into the chat — it's on disk, linkable.

## Resume

If the user asks to resume a paused or stalled run, jump straight to step 3 (`moderate-debate`) on the existing run dir. The moderator handles re-extraction of bindings and the resume flow per `../moderate-debate/references/checkpoints.md`.

## Replay

If the user asks to replay a past run with a different roster, see `references/replay.md`. Replay produces a sibling run dir with its own agenda (copied + roster-adjusted) and runs the full lifecycle on it.

## Long-running runs

A multi-stage agenda may pause for hours or days at a checkpoint. See `references/timeline.md` for time-spanning conventions and resumability across sessions.

## Guardrails

- **Workspace state only in `<cwd>/.senate/`**, never in the skill directory. The skill is read-only at runtime.
- **Don't synthesize yourself.** Synthesis is `meeting-note`'s job. You return the path; the user reads the file.
- **Don't moderate yourself.** Turn-by-turn invocation is `moderate-debate`'s job.
- **Don't pick a format yourself** unless the request is unambiguous. Defer to `debate-agenda`.
- **No secrets in prompts.** Strip env vars, tokens, and credentials from anything sent to another CLI.

## Reference loading rules

Load each reference **only** when its condition fires:

| File | Load when |
| --- | --- |
| `references/workspace.md` | Step 1 (mint the run dir) and any time you need the canonical `<run-dir>/` layout or `state.json` schema. |
| `references/replay.md` | The user explicitly asked to replay a past run with a different roster. Never load otherwise. |
| `references/timeline.md` | A run has been paused at a checkpoint long enough that resumability across sessions matters (hours+), or the user is explicitly resuming a run from a previous session. Skip for routine runs that complete in one sitting. |

## Files in this skill

- `SKILL.md` — this file.
- `references/workspace.md` — spec for `.senate/runs/<id>/` layout.
- `references/replay.md` — deterministic replay of past runs.
- `references/timeline.md` — time-spanning runs and resumability across sessions.

## Sub-skills (lifecycle phases)

- `../debate-agenda/` — plan: format selection, roster, stage sequencing, composition, branching. Also hosts the format library at `../debate-agenda/formats/`.
- `../moderate-debate/` — run: turns, contracts, failures, budget, checkpoints, shared and private context.
- `../meeting-note/` — consolidate: verdict.md and meeting-notes.md.

## Primitives

- `../invoke-agent/` — per-CLI invocation playbooks (used by `moderate-debate`, referenced by `debate-agenda` for validation).
