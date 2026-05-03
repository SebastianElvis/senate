# Workspace layout

All runtime state for a debate lives in the **user's current working directory**, under `.senate/`. The skill repo is never written to at runtime.

## Design principles

The layout splits responsibilities so every artifact has a single owner and a single home:

- **`agents/`** holds only the *soul* of each agent: cross-turn private memory and (for the moderator) governance rationale. Nothing per-turn lives here.
- **`stages/`** holds the per-stage synthesis verdict and a `turns/` subfolder of per-turn forensics. One subfolder per turn keeps prompt + output + side-channel cohesively together.
- **Top-level files** are the run-wide signal: the plan (`agenda.md`), the live record (`transcript.jsonl`, `state.json`), the shared scratchpad (`context.md`), the scribe's user-facing summary (`notes.md`), and pipeline data flow (`bindings.json`).
- **Sub-debates** are embedded under the turn that spawned them, never as a top-level peer.

## Layout — single-stage run

A single-stage run still gets a `stages/` directory with one entry. The filesystem mirrors `state.json.stages[]` (which always has at least one entry).

```
<cwd>/
  .senate/
    runs/
      2026-04-27-1432-parliament/
        agenda.md            # the plan (written by debate-agenda)
        context.md           # shared scratchpad — delta-only, every agent reads each turn
        transcript.jsonl     # canonical append-only per-turn record (`prompt` inline + `prompt_sha256`)
        state.json           # current status (running / paused_at_checkpoint / completed / stalled / aborted / revising)
        notes.md             # user-facing summary written by meeting-note (merges old verdict.md + meeting-notes.md)
        agents/
          moderator.md       # moderator's governance log — narrow, policy-focused, cross-links turn/stage IDs
          codex.md           # codex's private memory across turns (delta-only; moderator-owned writer)
          gemini.md
          claude.md
        stages/
          1-parliament/
            verdict.md       # the synthesis turn's content (bindings target for pipelines)
            turns/
              001-codex-mp_pro/
                prompt.derived.md   # do-not-edit; one-way derivation from transcript.jsonl turn 1
                stdout.log          # raw stdout; always present, possibly empty on failure
                stderr.log          # only present if non-empty
                reply.md            # cleaned reply text (no fenced delta blocks)
              002-gemini-mp_con/
                ...
              003-claude-speaker/
                ...
```

**Writer ownership.** The moderator owns top-level files (`agenda.md` indirectly via planner callbacks, `context.md`, `transcript.jsonl`, `state.json`, `bindings.json`, `agents/<cli>.md`, `agents/moderator.md`) and per-stage `stages/<n>-<name>/verdict.md`. Each per-turn subagent owns `stages/<n>-<name>/turns/<NNN>-<cli>-<role>/{prompt.derived.md, stdout.log, stderr.log, reply.md}` for the turn it ran (see `../../moderate-debate/SKILL.md` §4a). `stdout.log` is always kept (so `log_path` on dispatched CLI transcript lines resolves); `stderr.log` is kept only when non-empty. Any retry the subagent performs — contract re-prompt, `rate_limit`/`timeout` retry, or exit-0 empty-stdout retry per `../../moderate-debate/references/failures.md` — produces sibling files `stdout.r1.log` (and `stderr.r1.log` if non-empty); only one retry per turn is allowed under any policy, so `r2` never exists. The moderator never opens any of these per-turn files at runtime — they are for replay and debugging only — but it records `log_path` (and `retry_log_path` when present) on the corresponding `transcript.jsonl` line.

Exception: if a per-turn subagent crashes or returns malformed data before creating its first-attempt `stdout.log`, the moderator may create an empty synthetic `stages/<n>-<name>/turns/<NNN>-<cli>-<role>/stdout.log` solely to preserve the dispatched-turn `log_path` invariant. This is the only moderator write to a per-turn `stdout.log`; the transcript line should also record `error: "unknown"` and a synthetic `stderr_tail` such as `subagent_crash`.

## Layout — multi-stage run (pipeline)

```
<cwd>/
  .senate/
    runs/
      2026-04-27-1500-draft-review-finalize/
        agenda.md
        context.md
        transcript.jsonl
        state.json
        notes.md
        bindings.json        # named values flowing between stages
        agents/
          moderator.md
          claude.md          # one private-memory file per CLI across the whole run
          codex.md
          gemini.md
        stages/
          1-draft/
            verdict.md
            turns/
              001-claude-author/
              002-codex-commenter/
              ...
          2-review/
            verdict.md
            turns/
              009-gemini-reviewer/
              ...
          3-synthesize/
            verdict.md
            turns/
              018-compose-arbiter/      # composed role; sub-debate lives under this turn
                prompt.derived.md
                sub-verdict.md          # the only thing that bubbled up to the parent
                sub/                    # full recursive sub-run dir (same layout)
                  agenda.md
                  transcript.jsonl
                  state.json
                  notes.md
                  agents/
                  stages/
              019-claude-editor/
                ...
```

## File roles

### `agenda.md`

The plan. Schema in `../../debate-agenda/references/agenda-schema.md`. YAML frontmatter for machine-parseable fields, markdown body for the human-readable rationale. **Mutable, but only via `## Revisions`** — record plan-state changes here and nowhere else. The **planner is the sole writer**; if the moderator needs to revise mid-run it calls back to `debate-agenda`, which appends a `## Revisions` entry and rewrites the file (see `../../moderate-debate/SKILL.md` § 5 "Plan-validate-execute gate").

### `context.md`

Shared free-form scratchpad. Every agent reads it at the top of every turn. **Derived projection of `transcript.jsonl.context_delta`** — see "Invariants on derived projections" below; agent-side contract in `../../moderate-debate/references/context.md`.

### `agents/<cli>.md`

Per-CLI private memory across turns. Only that CLI's prompts include this file. Same derivation pattern as `context.md`, projected from `private_delta` filtered to that CLI. One file per CLI for the whole run, even if the CLI plays multiple roles.

### `agents/moderator.md`

The moderator's governance log. Narrow scope: re-plan triggers, contract retries, role/format swaps, tie-break rationale, decisions to pause vs continue. Every entry must cross-link the relevant `turn:` / `stage:` / `incident:` ID rather than duplicating the underlying fact. Append-only.

This is **not** a diary, **not** a duplicate of `agenda.md`'s `## Revisions` (plan state belongs there), and **not** a duplicate of failure facts (those live in `transcript.jsonl`). If an entry doesn't add governance rationale that points back to a fact elsewhere, it doesn't belong here.

### `transcript.jsonl`

Append-only, one JSON object per line. Monotonic `turn` numbering across the whole run. Schema below. The **canonical** record — `prompt.derived.md` derives from its `prompt` field; `context.md` / `agents/<cli>.md` derive from its `context_delta` / `private_delta` fields. **System-only**: read by the moderator, scribe, and evals (agents never read it; see "Invariants on derived projections" below).

### `state.json`

Source of truth for whether the run is running, paused, completed, etc. Used for resume. Write cadence (moderator-owned, atomic temp-file + rename every time):

- Every **turn boundary**: bump `last_activity_at`. This is the heartbeat — a crashed or stalled run leaves no signal of progress otherwise.
- Every **stage boundary** and every **checkpoint**: full re-write including `current_stage`, `stages_completed`, `stages_pending`, `stages[*]`, `checkpoint`, `budget_remaining`.
- On `auth` error or any abort: write `status: "aborted"` with `aborted_reason` before handing back to `senate`.

The per-turn subagent never writes `state.json`.

### `notes.md`

Written by `meeting-note` after the moderator finishes. Single user-facing summary that merges the old `verdict.md` (canonical decision + structured outcome) with the old `meeting-notes.md` (TL;DR, narrative, action items). Schema in `../../meeting-note/references/notes-schema.md`.

### `stages/<n>-<name>/verdict.md`

The synthesis turn's content for that stage, written by the moderator at stage completion. **Bindings target** — pipeline `output_bindings` source from this file (`verdict.md body` and `verdict.md section <name>`). Schema in `../../meeting-note/references/verdict-schema.md`.

### `stages/<n>-<name>/turns/<NNN>-<cli>-<role>/`

One directory per turn. `<NNN>` is the monotonic turn number across the whole run, zero-padded to 3 digits, matching `transcript.jsonl`'s `turn` field. `<cli>` is the invoked CLI; `<role>` is the format role this turn played. Contents:

- `prompt.derived.md` — full prompt sent to the CLI, mirrored from `transcript.jsonl`. **Do not edit.** Header reads `<!-- generated from transcript.jsonl turn N (sha256 …); do not edit -->`. Drift detection via `prompt_sha256` in the transcript line.
- `stdout.log` — raw stdout from the CLI invocation. Always present, even when empty on a hard failure, so the per-turn directory has a stable raw-output slot.
- `stderr.log` — raw stderr. **Only present if non-empty** (clean runs delete the empty file per `../../invoke-agent/SKILL.md`).
- `reply.md` — cleaned reply text with fenced `context-delta` / `private-delta` / structured-output blocks stripped. Byte-identical to `transcript.jsonl.text`; the human-readable mirror of the canonical bytes.

For composed roles, the turn directory also contains these allowed extras:

- `sub-verdict.md` — the sub-debate's verdict copied up; this is the only content that flows into the parent's transcript as the turn's `text`.
- `sub/` — the full recursive sub-run directory (same layout as a top-level run).

### `bindings.json` (multi-stage only)

Named values extracted from each stage's verdict per the agenda's `output_bindings`. Downstream stages consume them.

```json
{
  "draft_doc": "<full markdown body of stage 1's verdict>",
  "annotated_doc": "<full markdown body of stage 2's verdict>",
  "resolution_rate": 0.8
}
```

## What is NOT a top-level file

For migration clarity, the following files **no longer exist** at top level:

- **`verdict.md`** — merged into `notes.md`. Stage-level `stages/<n>/verdict.md` still exists as the bindings target.
- **`meeting-notes.md`** — merged into `notes.md`.
- **`failures.md`** — failures are recorded per-turn in `transcript.jsonl` (the `error` / `stderr_tail` / `retry_count` fields). The scribe surfaces a failure rollup inside `notes.md` if any turns errored.
- **`sub/`** — sub-debates are no longer a top-level peer. They live under the turn that spawned them, at `stages/<n>/turns/<NNN>-compose-<role>/sub/`.

Replay runs may add one top-level metadata file, `replay_manifest.json`, as described in `replay.md`. That file is replay provenance, not a live-run artifact.

## `transcript.jsonl` schema

This is the **canonical** schema. Every other file that needs to record or interpret a transcript line refers back to this.

The schema below is shown across multiple lines for readability. **On disk, each transcript line MUST be a single physical line** — the JSON object must be serialized without internal newlines, with embedded newlines in `prompt` / `text` / `context_delta` / `private_delta` / `stderr_tail` escaped as `\n`. Multi-line records break `jq -c .` and the eval harness's per-line parser.

```json
{
  "turn": 1,
  "stage": 1,
  "phase": "opening",
  "role": "mp_pro",
  "cli": "codex",
  "ts": "2026-04-27T14:32:18Z",
  "prompt": "...full prompt body sent to the CLI...",
  "prompt_sha256": "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
  "prompt_tokens": 1840,
  "completion_tokens": 612,
  "tokens_estimated": false,
  "exit_code": 0,
  "text": "...cleaned reply, byte-identical to reply.md...",
  "structured": { "vote": "yes", "reason": "..." },
  "context_delta": "- migration cost hinges on tokenizer compatibility — see crate `tiktoken-rs` v0.5.",
  "private_delta": "- need to double-check the GIL claim before next turn.",
  "error": null,
  "retry_count": 0,
  "stderr_tail": null,
  "log_path": "stages/1-parliament/turns/001-codex-mp_pro/stdout.log",
  "retry_log_path": null,
  "sub_run_id": null
}
```

Field notes:

- `stage` — `1` for single-stage runs; the stage index for multi-stage.
- `prompt` — the full prompt body sent to the CLI. Required for replay. Long prompts may be stored gzipped+base64 as `prompt_gz` instead.
- `prompt_sha256` — SHA-256 of the `prompt` (or the decompressed `prompt_gz`). Used to detect drift between the canonical record and the on-disk `prompt.derived.md` mirror. Always present.
- `tokens_estimated` — `true` when the CLI didn't report token counts and the moderator estimated from char count.
- `text` — the cleaned reply (ANSI-stripped, fenced `context-delta` / `private-delta` / structured-output blocks removed); byte-identical to `<turn-dir>/reply.md`. On a failed turn, whatever cleaned stdout arrived (often empty).
- `structured` — present only when the format's output contract produced a parseable machine-readable block, usually fenced JSON. Omitted when `error` is set and omitted for free-text contracts that validate `text` without producing a separate parsed object. Sourced from the per-turn subagent's `parsed_output` field (see `../../moderate-debate/SKILL.md` §4a).
- `context_delta` — string or `null`. The verbatim bytes the subagent extracted from a `context-delta` fenced block (no `[T<n>, <role>]` prefix; `null` for an absent or whitespace-only block). The canonical source for `context.md`'s shared-notes projection — see "Invariants on derived projections" below.
- `private_delta` — string or `null`. Same shape; canonical source for `agents/<cli>.md`'s `## Memory` projection.
- `error` — one of the codes in `../../moderate-debate/references/failures.md` (`auth`, `rate_limit`, `timeout`, `contract_violation`, `refusal`, `unknown`, `budget_exhausted`), or `null` when the turn succeeded. Sourced from the subagent's `error.kind` (or imposed by the moderator for `budget_exhausted`).
- `retry_count` — number of CLI re-invocations the subagent performed before this line was committed (rate-limit/timeout retry, exit-0 empty-stdout retry, or contract re-prompt). `0` on first-try success.
- `stderr_tail` — last 200 bytes of stderr when `error` is set, otherwise `null`. Already truncated by the subagent.
- `log_path` — relative path (from the run dir) to the first-attempt raw stdout log written by the per-turn subagent (e.g., `stages/1-parliament/turns/001-codex-mp_pro/stdout.log`). Required for dispatched CLI turns, even on error; the file always exists (subagents do not prune `stdout.log` even when empty, and the moderator may create an empty synthetic log only after a subagent crash). `null` for turns that do not dispatch a CLI subagent, including `budget_exhausted` skips and composed-role parent turns that set `sub_run_id`.
- `retry_log_path` — relative path to the retry attempt's raw stdout log (e.g., `stages/1-parliament/turns/007-codex-mp_pro/stdout.r1.log`) when the subagent retried this turn (rate-limit/timeout retry, exit-0 empty-stdout retry, or contract re-prompt); `null` otherwise. Naming is uniform: `stdout.r1.log` next to the canonical `stdout.log`. There is at most one retry per turn under any policy, so `r2` never exists.
- `sub_run_id` — set when the turn was filled by a composed sub-debate (per `../../debate-agenda/references/composition.md`); the value is the relative path to the sub-run dir, e.g. `stages/3-synthesize/turns/018-compose-arbiter/sub/`.

Non-turn ledger lines (e.g., automatic transcript summaries, sub-transcript reads, shared-context summaries) appear with `"action": "<name>"` instead of `turn`/`role`/`cli`. Examples:

```json
{"action": "summarize_transcript", "from_turn": 1, "to_turn": 6, "ts": "..."}
{"action": "read_sub_transcript", "sub_run_id": "stages/3-synthesize/turns/018-compose-arbiter/sub/", "by_role": "judge", "ts": "..."}
{"action": "summarize_context", "after_turn": 12, "summary": "<auto-summary text>", "ts": "..."}
```

`summarize_context` is emitted when `context.md` hits the size cap (see `../../moderate-debate/references/context.md` § Size cap); it carries the bytes the projection logic uses to reproduce the divider and summary block.

## Invariants on derived projections

1. **Agents never read `transcript.jsonl`.** The only transcript bytes that reach an agent are inside the curated "transcript slice" the moderator builds at prompt-build time; cross-turn agent-visible state otherwise lives in `context.md` / `agents/<cli>.md`.
2. **`context.md` and `agents/<cli>.md` are append-only side-effects of committing a transcript row.** Replay rule: for every row whose `context_delta` is non-null, append `[T<n>, <role>] ` + the delta to `context.md`; same for `private_delta` → `agents/<cli>.md` with `[T<n>] ` prefix; for every `summarize_context` ledger action, project its divider + summary block. The bootstrap headers the moderator writes on first start are configuration and sit above the projected region.

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
- `current_stage` — the index of the in-progress (or paused) stage. Always at least `1`.
- `stages_completed` / `stages_pending` — flat lists of indices, kept in sync with `stages[*].status`.
- `stages` — per-stage detail. Always at least one entry, even for single-stage runs.
- `checkpoint` — populated only when `status == paused_at_checkpoint`; otherwise all fields `null`. Schema described in `../../moderate-debate/references/checkpoints.md`.
- For aborted runs, `aborted_reason` is added at the top level (e.g., `"auth_failure_codex"`).

## Conventions

- Timestamps are ISO 8601 UTC.
- `run_id` format: `YYYY-MM-DD-HHMM-<name>`. Lowercase, hyphens. `<name>` is the format name for single-stage runs, the pipeline name for multi-stage.
- Turn numbering is **monotonic across the whole run**, even across stages — stage 2's first turn might be `010-...` if stage 1 ran 9 turns. This matches `transcript.jsonl`'s `turn` field 1:1, so a directory path uniquely identifies a transcript line.
- `.senate/` should be gitignored in the user's repo by default. If the user wants to commit debate history, they can remove it from `.gitignore`.
- The skill never writes to anywhere outside `<cwd>/.senate/`.

## Cleanup

`.senate/runs/<id>/` directories are never garbage-collected automatically. Users can safely `rm -rf .senate/runs/<id>` once they're done. Aborted runs are renamed to `<id>.aborted` to make them obvious in listings.
