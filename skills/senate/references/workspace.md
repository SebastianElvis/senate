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
          codex.md           # codex's private memory across turns
          codex.1.log        # raw stdout for codex, turn 1
          codex.2.log
          gemini.md
          gemini.1.log
          claude.md
          claude.1.log
```

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

The plan. Schema in `../../debate-agenda/references/agenda-schema.md`. YAML frontmatter for machine-parseable fields, markdown body for the human-readable rationale. Mutable: the moderator may append to `## Revisions` if the agenda is re-planned mid-run.

### `context.md`

Shared free-form scratchpad. Every agent reads it at the top of every turn; agents append to it via a `context-delta` block in their reply. See `../../moderate-debate/references/context.md`.

### `agents/<cli>.md`

Per-CLI private memory across turns. Only that CLI's prompts include this file. Agents update it via a `private-delta` block. One file per CLI for the whole run, even if the CLI plays multiple roles.

### `transcript.jsonl`

Append-only, one JSON object per line. Monotonic `turn` numbering. Schema below.

### `state.json`

Source of truth for whether the run is running, paused, completed, etc. The moderator writes it at every stage boundary and every checkpoint. Used for resume.

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
  "sub_run_id": null
}
```

Field notes:

- `stage` — `1` for single-stage runs; the stage index for multi-stage.
- `prompt` — the full prompt body sent to the CLI. Required for replay. Long prompts may be stored gzipped+base64 as `prompt_gz` instead.
- `tokens_estimated` — `true` when the CLI didn't report token counts and the moderator estimated from char count.
- `structured` — present only when the format's output contract produced a parseable block. Omitted when `error` is set.
- `context_delta_appended` / `private_delta_appended` — booleans recording whether the moderator extracted and appended those blocks; absence of a delta is not a failure.
- `error` — one of the codes in `../../moderate-debate/references/failures.md` (`auth`, `rate_limit`, `timeout`, `contract_violation`, `refusal`, `unknown`, `budget_exhausted`), or `null` when the turn succeeded.
- `retry_count` — number of retries before the line was committed. `0` on first-try success.
- `stderr_tail` — last 200 bytes of stderr when `error` is set, otherwise `null`.
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
