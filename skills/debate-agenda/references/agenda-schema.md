# `agenda.md` schema

The agenda is the single planning artifact of a senate run. Every other artifact (transcript, context, verdict, meeting notes) refers back to it.

It lives at `<run-dir>/agenda.md` and is the **first** file written in a run. The moderator and every participating agent reads it.

## Shape

YAML frontmatter for machine-parseable fields, markdown body for the human-readable plan.

```markdown
---
run_id: 2026-04-27-1432-parliament
task: "Should we migrate the ingest service from Python to Rust?"
mode: single | pipeline
status: ready | pending_clarification | revising
created_at: 2026-04-27T14:32:05Z

stages:
  - index: 1
    name: debate
    format: parliament
    roster:
      - { role: mp_pro, cli: codex, model: gpt-5-codex }
      - { role: mp_con, cli: gemini, model: gemini-2.5-pro }
      - { role: mp_neutral, cli: kimi, model: kimi-k2 }
      - { role: speaker, cli: claude, model: claude-sonnet-4-6 }
    rounds: 3
    budget:
      wall_clock_sec: 900
      total_tokens: 200000
    input_bindings: []
    output_bindings:
      - { name: vote_tally, source: "fenced-json.tally" }
      - { name: verdict_body, source: "verdict.md body" }
    checkpoint: none
    composition: []

open_questions: []
---

# Agenda — <task one-liner>

## Why this format

<1-paragraph rationale: what about the task pointed to this format. From format-selection.md>

## Why this roster

<1-paragraph rationale: any role-CLI pairing that isn't the default, why>

## Stage plan

### Stage 1 — debate (parliament)

<1-paragraph description of what this stage produces and why>

## Open questions

<list of things the planner didn't resolve, that the moderator may need to handle adaptively. Empty if status is `ready`.>

## Revisions

<append-only log. Each entry: timestamp, reason, what changed. Empty on first write.>
```

## Field reference

### Top-level frontmatter

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `run_id` | string | yes | Matches the run dir name. Format: `YYYY-MM-DD-HHMM-<format-or-pipeline-name>`. |
| `task` | string | yes | The question being debated, verbatim from the user. |
| `mode` | enum | yes | `single` (one stage) or `pipeline` (≥2 stages). |
| `status` | enum | yes | `ready` (moderator may proceed), `pending_clarification` (caller must ask user), `revising` (moderator paused mid-run for re-plan). |
| `created_at` | ISO 8601 UTC | yes | When the agenda was first written. |
| `stages` | list | yes | At least one. See "Stage object" below. |
| `open_questions` | list of strings | no | Things the planner couldn't pin down. Moderator handles adaptively or calls back for re-plan. |

### Stage object

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `index` | int | yes | 1-indexed. Monotonic across `stages`. |
| `name` | string | yes | Short, lowercase, hyphenated. Becomes a directory name. |
| `format` | string | yes | One of the primitives in `../formats/` (parliament, court, panel, workshop, brainstorm). |
| `preset` | string | conditional | Required when the primitive is a closed family (court, panel, workshop). Names which preset to run (e.g., `red-team`, `rfc`, `committee`). Omit for parliament and brainstorm. |
| `roster` | list | yes | Each entry: `{ role, cli, model? }`. Roles must match the format/preset's role list. |
| `rounds` | int | no | Falls back to the format's default. |
| `budget` | object | no | `wall_clock_sec`, `total_tokens`, `turn_timeout_sec`. Falls back to defaults in `../../moderate-debate/references/budget.md`. |
| `input_bindings` | list | no | Names of bindings this stage consumes from prior stages. |
| `output_bindings` | list | no | Each entry: `{ name, source }`. Source is one of: `verdict.md body`, `verdict.md section <name>`, `fenced-json.<field>`, `transcript.<role>.last`. |
| `checkpoint` | enum | no | `none` (default), `optional`, `required`, `conditional`. See `../../moderate-debate/references/checkpoints.md`. |
| `condition` | string | only if `checkpoint: conditional` | Expression evaluated against this stage's verdict, e.g., `"stage.verdict.confidence < 0.5"`. |
| `composition` | list | no | Composed roles (a role filled by a sub-debate). Each entry: `{ role, format, roster, rounds }`. See `composition.md`. |
| `branches` | list | no | Parallel sub-pipelines. Each entry is itself a stage object. See `branching.md`. |

## Single-stage minimum

A bare-minimum single-stage agenda has one stage, no input bindings, optional output bindings, and an empty `open_questions`. Example:

```markdown
---
run_id: 2026-04-27-1432-court
task: "Is my refactor of payments.go safe to merge?"
mode: single
status: ready
created_at: 2026-04-27T14:32:05Z

stages:
  - index: 1
    name: debate
    format: court
    preset: court
    roster:
      - { role: prosecution, cli: codex }
      - { role: defense, cli: gemini }
      - { role: judge, cli: claude }
    rounds: 2
    checkpoint: none

open_questions: []
---

# Agenda — refactor safety review

## Why this format

A `court` is the right shape: there is a clear proposition (the refactor), the user wants adversarial stress on it, and a single ruling is the desired output.

## Why this roster

Default 3-CLI roster. Codex prosecutes (it tends to find concrete edge cases); Gemini defends (it stays grounded in the diff); Claude judges (synthesis quality).

## Stage plan

### Stage 1 — debate (court)

Two rounds of prosecution / defense, then judge ruling. Verdict: sustain | dismiss | remand. Rationale cites turn numbers.

## Open questions

(none)

## Revisions

(none yet)
```

## Multi-stage with bindings — example

See `../formats/rfc-pipeline.md` for a worked example.

## Revisions log

When the moderator calls `debate-agenda` to re-plan mid-run, append an entry:

```markdown
## Revisions

- **2026-04-27T15:08:42Z** — moderator requested re-plan. Reason: stage 2 `mp_con` (gemini) failed contract twice; replaced with kimi for stages 2+. Stages 1 verdicts unchanged.
- **2026-04-27T15:42:11Z** — user paused at checkpoint `final_doc_accepted`, edited stage 2 verdict; re-extract bindings on resume. No structural changes.
```

The frontmatter is updated to reflect the new state (e.g., the stage's roster entry). The body's stage descriptions are updated. The `Revisions` log is the audit trail of those edits.

## Why YAML frontmatter + markdown

- **Machine-parseable header** for the moderator's pre-flight checks (validate roster CLIs exist, validate format files exist, etc.).
- **Human-readable body** for the participating agents: every agent gets the agenda's body in its prompt, so the planner's prose ("why this format", "why this roster") shapes the debate.
- **One file** rather than a `roster.json` + `workflow.md` + `manifest.json` triple. Simpler to read, simpler to revise.

## Validation

Before returning `status: ready`, the planner validates:

- Every `cli` in every roster has a file at `../../invoke-agent/references/<cli>.md`.
- Every `format` has a file at `../formats/<format>.md`.
- For closed-family primitives (court, panel, workshop), `preset` is set and the named preset exists in the primitive's preset table.
- Every role named in a roster appears in that format/preset's role list.
- Every `input_bindings` entry refers to an `output_bindings` name from an earlier stage.
- Stage indices are monotonic from 1.

Validation failures: surface to the user; do not return `status: ready`.
