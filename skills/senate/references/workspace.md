# Workspace layout

All runtime state for a debate lives in the **user's current working directory**, under `.senate/`. The skill repo is never written to at runtime.

## Layout — single-stage run

```
<cwd>/
  .senate/
    runs/
      2026-04-27-1432-parliament/
        agenda.md            # the plan (written by debate-agenda)
        context.md           # shared scratchpad — free-form, every agent reads each turn
        transcript.jsonl     # append-only structured per-turn record
        state.json           # current status (running / paused_at_checkpoint / completed / stalled / aborted / revising)
        verdict.md           # canonical decision (written by meeting-note)
        meeting-notes.md     # user-facing summary (written by meeting-note)
        failures.md          # written only if any failures occurred
        agents/
          codex.md           # codex's private memory across turns (moderator-owned writer)
          codex.1.log        # raw stdout for codex, turn 1 (per-turn subagent-owned writer)
          codex.1.stderr     # raw stderr, turn 1; absent when stderr was empty
          codex.2.log
          gemini.md
          gemini.1.log
          claude.md
          claude.1.log
```

**Writer ownership for `agents/` files.** The `<cli>.md` private memory is written only by the moderator (it appends `private_delta` blocks returned by per-turn subagents, in turn order). The `<cli>.<turn>.log` and `<cli>.<turn>.stderr` files are written only by the per-turn subagent that ran that turn (see `../../moderate-debate/SKILL.md` §4a). The `.log` is always kept (so `log_path` on dispatched CLI transcript lines resolves); the `.stderr` is kept only when non-empty. Any retry the subagent performs — contract re-prompt, `rate_limit`/`timeout` retry, or exit-0 empty-stdout retry per `../../moderate-debate/references/failures.md` — produces sibling files tagged `<turn>r1` (e.g., `codex.7r1.log`); only one retry per turn is allowed under any policy, so `r2` never exists. The moderator never opens any of these files at runtime — they are for replay and debugging only — but it records `log_path` (and `retry_log_path` when present) on the corresponding `transcript.jsonl` line.

Exception: if a per-turn subagent crashes or returns malformed data before creating its first-attempt `.log`, the moderator may create an empty synthetic `agents/<cli>.<turn>.log` solely to preserve the dispatched-turn `log_path` invariant. This is the only moderator write to a `<cli>.<turn>.log` file; the transcript line should also record `error: "unknown"` and a synthetic `stderr_tail` such as `subagent_crash`.

## Layout — multi-stage run (pipeline)

```
<cwd>/
  .senate/
    runs/
      2026-04-27-1500-rfc-pipeline/
        agenda.md            # the multi-stage plan
        context.md           # shared across all stages
        transcript.jsonl     # all stages, monotonic turn numbering
        state.json
        verdict.md           # top-level pipeline verdict (stitches stage verdicts)
        meeting-notes.md
        failures.md
        bindings.json        # named values flowing between stages
        agents/
          claude.md          # one private-memory file per CLI across the whole run
          codex.md
          gemini.md
          ...
        stages/
          1-draft/
            verdict.md       # this stage's own verdict
            transcript.jsonl # (subset; copy of relevant slice for replay convenience)
          2-review/
            verdict.md
          3-synthesize/
            verdict.md
        sub/                 # composed sub-debates (if any)
          jury-verdict-1/
            agenda.md
            context.md
            transcript.jsonl
            agents/
              ...
            verdict.md
```

## File roles

### `agenda.md`

The plan. Schema in `../../debate-agenda/references/agenda-schema.md`. YAML frontmatter for machine-parseable fields, markdown body for the human-readable rationale. The **planner is the sole writer**; if the moderator needs to revise mid-run it calls back to `debate-agenda`, which appends a `## Revisions` entry and rewrites the file (see `../../moderate-debate/SKILL.md` § 5 "Plan-validate-execute gate").

### `context.md`

Shared free-form scratchpad. Every agent reads it at the top of every turn; agents append to it via a `context-delta` block in their reply. See `../../moderate-debate/references/context.md`.

### `agents/<cli>.md`

Per-CLI private memory across turns. Only that CLI's prompts include this file. Agents update it via a `private-delta` block. One file per CLI for the whole run, even if the CLI plays multiple roles.

### `transcript.jsonl`

Append-only, one JSON object per line. Monotonic `turn` numbering. Schema below.

### `state.json`

Source of truth for whether the run is running, paused, completed, etc. Used for resume. Write cadence (moderator-owned, atomic temp-file + rename every time):

- Every **turn boundary**: bump `last_activity_at`. This is the heartbeat — a crashed or stalled run leaves no signal of progress otherwise.
- Every **stage boundary** and every **checkpoint**: full re-write including `current_stage`, `stages_completed`, `stages_pending`, `stages[*]`, `checkpoint`, `budget_remaining`.
- On `auth` error or any abort: write `status: "aborted"` with `aborted_reason` before handing back to `senate`.

The per-turn subagent never writes `state.json`.

### `verdict.md` and `meeting-notes.md`

Written by `meeting-note` after the moderator finishes. Verdict is short and canonical; notes are denser and user-facing. Schemas in `../../meeting-note/references/verdict-schema.md` and `../../meeting-note/references/notes-schema.md`.

### `bindings.json` (multi-stage only)

Named values extracted from each stage's verdict per the agenda's `output_bindings`. Downstream stages consume them.

```json
{
  "draft_doc": "<full markdown body of stage 1's verdict>",
  "annotated_doc": "<full markdown body of stage 2's verdict>",
  "resolution_rate": 0.8
}
```

### `failures.md`

Written by the moderator if any turn produced a non-empty `error` code. Referenced from `meeting-notes.md`. If absent, the run had zero failures.

## `transcript.jsonl` schema

This is the **canonical** schema. Every other file that needs to record or interpret a transcript line refers back to this.

```json
{
  "turn": 1,
  "stage": 1,
  "phase": "opening",
  "role": "mp_pro",
  "cli": "codex",
  "ts": "2026-04-27T14:32:18Z",
  "prompt": "...full prompt body sent to the CLI...",
  "prompt_tokens": 1840,
  "completion_tokens": 612,
  "tokens_estimated": false,
  "exit_code": 0,
  "text": "...full agent reply...",
  "structured": { "vote": "yes", "reason": "..." },
  "context_delta_appended": true,
  "private_delta_appended": true,
  "error": null,
  "retry_count": 0,
  "stderr_tail": null,
  "log_path": "agents/codex.1.log",
  "retry_log_path": null,
  "sub_run_id": null
}
```

Field notes:

- `stage` — `1` for single-stage runs; the stage index for multi-stage.
- `prompt` — the full prompt body sent to the CLI. Required for replay. Long prompts may be stored gzipped+base64 as `prompt_gz` instead.
- `tokens_estimated` — `true` when the CLI didn't report token counts and the moderator estimated from char count.
- `structured` — present only when the format's output contract produced a parseable machine-readable block, usually fenced JSON. Omitted when `error` is set and omitted for free-text contracts that validate `text` without producing a separate parsed object. Sourced from the per-turn subagent's `parsed_output` field (see `../../moderate-debate/SKILL.md` §4a).
- `context_delta_appended` / `private_delta_appended` — booleans recording whether the moderator appended the deltas the subagent returned; absence of a delta is not a failure.
- `error` — one of the codes in `../../moderate-debate/references/failures.md` (`auth`, `rate_limit`, `timeout`, `contract_violation`, `refusal`, `unknown`, `budget_exhausted`), or `null` when the turn succeeded. Sourced from the subagent's `error.kind` (or imposed by the moderator for `budget_exhausted`).
- `retry_count` — number of CLI re-invocations the subagent performed before this line was committed (rate-limit/timeout retry, exit-0 empty-stdout retry, or contract re-prompt). `0` on first-try success.
- `stderr_tail` — last 200 bytes of stderr when `error` is set, otherwise `null`. Already truncated by the subagent.
- `log_path` — relative path (from the run dir) to the first-attempt raw stdout log written by the per-turn subagent (e.g., `agents/codex.1.log`). Required for dispatched CLI turns, even on error; the file always exists (subagents do not prune the `.log` even when empty, and the moderator may create an empty synthetic log only after a subagent crash). `null` for turns that do not dispatch a CLI subagent, including `budget_exhausted` skips and composed-role parent turns that set `sub_run_id`.
- `retry_log_path` — relative path to the retry attempt's raw stdout log (e.g., `agents/codex.7r1.log`) when the subagent retried this turn (rate-limit/timeout retry, exit-0 empty-stdout retry, or contract re-prompt); `null` otherwise. Naming is uniform: `<cli>.<turn>r1.log`. There is at most one retry per turn under any policy, so `r2` never exists.
- `sub_run_id` — set when the turn was filled by a composed sub-debate (per `../../debate-agenda/references/composition.md`); names the sub-run dir under `<run-dir>/sub/`.

Non-turn ledger lines (e.g., automatic transcript summaries, sub-transcript reads) appear with `"action": "<name>"` instead of `turn`/`role`/`cli`. Examples:

```json
{"action": "summarize_transcript", "from_turn": 1, "to_turn": 6, "ts": "..."}
{"action": "read_sub_transcript", "sub_run_id": "...", "by_role": "judge", "ts": "..."}
```

## `state.json` schema

This is the **canonical** schema. Every other file that needs to record or interpret state refers back to this.

```json
{
  "run_id": "2026-04-27-1432-parliament",
  "status": "running" | "paused_at_checkpoint" | "completed" | "stalled" | "aborted" | "revising",
  "started_at": "2026-04-27T14:32:05Z",
  "last_activity_at": "2026-04-27T14:47:11Z",
  "completed_at": null,
  "current_stage": 2,
  "stages_completed": [1],
  "stages_pending": [3],
  "stages": [
    {
      "index": 1,
      "name": "draft",
      "status": "completed",
      "started_at": "2026-04-27T14:32:05Z",
      "completed_at": "2026-04-27T14:44:09Z",
      "verdict_path": "stages/1-draft/verdict.md",
      "wall_clock_sec": 724,
      "tokens": 42000
    },
    {
      "index": 2,
      "name": "review",
      "status": "running"
    }
  ],
  "checkpoint": {
    "paused_after_stage": null,
    "paused_at": null,
    "type": null,
    "next_stage": null
  },
  "budget_remaining": { "wall_clock_sec": 488, "tokens": 102000 }
}
```

Field notes:

- `status` — top-level status of the whole run.
- `current_stage` — `1` for single-stage runs, the index of the in-progress (or paused) stage for multi-stage.
- `stages_completed` / `stages_pending` — flat lists of indices, kept in sync with `stages[*].status`.
- `stages` — per-stage detail. Always at least one entry. For single-stage runs, exactly one entry.
- `checkpoint` — populated only when `status == paused_at_checkpoint`; otherwise all fields `null`. Schema described in `../../moderate-debate/references/checkpoints.md`.

## Conventions

- Timestamps are ISO 8601 UTC.
- `run_id` format: `YYYY-MM-DD-HHMM-<name>`. Lowercase, hyphens. `<name>` is the format name for single-stage runs, the pipeline name for multi-stage.
- `.senate/` should be gitignored in the user's repo by default. If the user wants to commit debate history, they can remove it from `.gitignore`.
- The skill never writes to anywhere outside `<cwd>/.senate/`.

## Cleanup

`.senate/runs/<id>/` directories are never garbage-collected automatically. Users can safely `rm -rf .senate/runs/<id>` once they're done. Aborted runs are renamed to `<id>.aborted` to make them obvious in listings.
