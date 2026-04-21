# Timeline — time-spanning runs

Workflows can span hours, days, or weeks. An RFC process that would take a team 2 weeks to run manually should also take 2 weeks when the team's comments are collected incrementally. Workflows persist state across pauses and can be resumed indefinitely later.

## `workflow_state.json`

The single source of truth for a workflow's state. Written at every stage boundary and every checkpoint. Read on resume.

```json
{
  "workflow_name": "rfc-pipeline",
  "workflow_run_id": "rfc-pipeline-2026-04-20-1500",
  "status": "paused" | "running" | "completed" | "stalled" | "aborted",
  "started_at": "2026-04-20T15:00:00Z",
  "last_activity_at": "2026-04-20T16:23:11Z",
  "completed_at": null,

  "workflow_file_sha": "a1b2c3...",
  "bindings_snapshot_version": 2,

  "stages": [
    {
      "index": 1,
      "name": "draft",
      "status": "completed",
      "started_at": "2026-04-20T15:00:00Z",
      "completed_at": "2026-04-20T15:12:04Z",
      "verdict_path": "stages/1-draft/verdict.md",
      "wall_clock_sec": 724,
      "tokens": 42000
    },
    {
      "index": 2,
      "name": "review",
      "status": "paused_at_checkpoint",
      "checkpoint_name": "final_doc_accepted",
      "paused_at": "2026-04-20T16:23:11Z",
      "verdict_path": "stages/2-review/verdict.md"
    },
    {
      "index": 3,
      "name": "synthesize",
      "status": "pending"
    }
  ],

  "global_budget": {
    "wall_clock_sec": 3600,
    "wall_clock_used": 1892,
    "tokens": 500000,
    "tokens_used": 178000
  }
}
```

## Status values

- **`running`** — a stage is currently executing. Should be transient; if seen in a workflow that hasn't been touched in hours, the previous orchestrator session crashed.
- **`paused_at_checkpoint`** — hit a checkpoint; awaiting user continue / revise / abort.
- **`stalled`** — a stage failed in a way that requires user intervention (budget exhausted, invalid binding, all agents failed).
- **`completed`** — all stages finished; `workflow_verdict.md` exists.
- **`aborted`** — user explicitly aborted.

## Resume

Resume command: *"Resume workflow `<run-id>`"*.

Orchestrator procedure:

1. Read `workflow_state.json`.
2. Verify the workflow file SHA still matches. If the workflow file has been edited since pause, warn the user; offer continue-with-current-file or abort.
3. Re-read all completed stages' `verdict.md` files (they may have been edited by the user during revise).
4. Re-extract bindings. Compare against `bindings.json`; if different, write new `bindings.json` and bump `bindings_snapshot_version`.
5. Resume at the current stage:
   - If `status == paused_at_checkpoint`: present the checkpoint view (see `CHECKPOINTS.md`) and wait.
   - If `status == stalled`: present the failure and options.
   - If `status == running`: something's wrong (previous crash). Ask user whether to restart the stage or mark it failed.
6. Proceed as normal.

## Orchestrator crash recovery

If the orchestrating session crashes mid-stage:

- `workflow_state.json` may show `status: running` even though no process is alive.
- On next resume, orchestrator detects this by checking `last_activity_at` — if > 1h ago and status is `running`, assume the previous run crashed.
- Roll back the current stage: its partial verdict (if any) moves to `stages/<N>-<name>.partial/`; the stage restarts with a fresh attempt.
- This rollback burns the stage's budget allocation.

## Time-based triggers

Some workflows benefit from calendar-based pauses:

- An RFC's comment period is 7 days.
- A postmortem review should happen 48h after the incident is resolved.

Workflows declare these as `checkpoint: conditional` with a time-based condition (H3+ supports this):

```yaml
checkpoint: conditional
condition: "time_since_stage_start > 7d"
action: "proceed_when_met"
```

The orchestrator does not autonomously wake up at `+7d`; it just refuses to proceed until the condition is met. The user (or an external scheduler) triggers resume after the time has passed.

For actual scheduling, pair with the host agent's scheduling capabilities (e.g., Claude Code's `CronCreate` or a system `cron` job invoking the host to resume the workflow).

## Long-lived artifacts

For workflows that span days:

- **Verdicts must be self-contained.** Someone reading `verdict.md` a week later should not need to reconstruct context from memory.
- **Transcripts are canonical.** If bindings are ambiguous later, re-extract from the transcript rather than relying on summaries.
- **Model versions drift.** A workflow started on 2026-04-20 may finish on 2026-04-27 with a subtly different model version. Record the CLI + model string in every turn; accept that cross-day runs are not perfectly reproducible.

## Cleanup

`workflow_state.json` never gets garbage-collected automatically. Users can safely `rm -rf .senate/workflows/<name>` once they're done — the skill treats missing directories as non-existent runs.

For convenience, `senate list-workflows` shows all workflows in the current workspace with their statuses, sorted by `last_activity_at`.
