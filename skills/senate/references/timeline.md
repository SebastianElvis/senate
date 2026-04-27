# Timeline — time-spanning runs

Multi-stage runs can span hours, days, or weeks. An RFC process that would take a team 2 weeks to run manually should also take 2 weeks when the team's comments are collected incrementally. Senate runs persist state across pauses and can be resumed indefinitely later.

This is a senate-level concern (not a moderate-debate concern) because resumability across host sessions is part of the lifecycle, not part of any single phase.

## `state.json` is the source of truth

Every run has a `state.json` written at every stage boundary and every checkpoint. On resume, senate reads this file to know where to pick up. The full schema and the meaning of every status value live in `workspace.md` (`## state.json schema`); this file only adds the time-spanning resume semantics that don't fit there.

## Resume

User resumes via the host: *"Resume run `<run-id>`"*. Senate's resume procedure:

1. Read `state.json`. Validate the agenda still parses against `../../debate-agenda/references/agenda-schema.md`.
2. Verify the agenda's frontmatter SHA still matches what was recorded at pause. If the agenda file has been edited since pause, warn the user; offer continue-with-current-agenda or abort.
3. Re-read all completed stages' `verdict.md` files (they may have been edited by the user during a `revise`).
4. Re-extract bindings into `bindings.json`.
5. Hand off to `../../moderate-debate/` with the run dir. The moderator handles the actual continuation.

## Crash recovery

If senate's host session crashes mid-stage:

- `state.json` may show `status: running` even though no process is alive.
- On next resume, senate detects this by checking `last_activity_at` — if > 1h ago and status is `running`, assume the previous session crashed.
- The current stage's partial artifacts (if any) move to `stages/<N>-<name>.partial/`; the stage restarts with a fresh attempt on resume.
- This rollback burns the stage's budget allocation.

## Time-based triggers

Some pipelines benefit from calendar-based pauses:

- An RFC's comment period is 7 days.
- A postmortem review should happen 48h after the incident is resolved.

The agenda may declare these as conditional checkpoints with a time-based condition:

```yaml
checkpoint: conditional
condition: "time_since_stage_start > 7d"
action: "proceed_when_met"
```

Senate does not autonomously wake up at `+7d`; it just refuses to proceed until the condition is met. The user (or an external scheduler) triggers resume after the time has passed.

For actual scheduling, pair with the host agent's scheduling capabilities (e.g., Claude Code's `CronCreate` / `ScheduleWakeup`, or a system `cron` job invoking the host to resume the run).

## Long-lived artifacts

For runs that span days:

- **Verdicts must be self-contained.** Someone reading `verdict.md` a week later should not need to reconstruct context from memory.
- **Transcripts are canonical.** If bindings are ambiguous later, re-extract from the transcript rather than relying on summaries.
- **Model versions drift.** A run started on 2026-04-20 may finish on 2026-04-27 with a subtly different model version. The agenda records the CLI + model string for every stage; accept that cross-day runs are not perfectly reproducible.
- **Shared context grows.** Long-running runs may have a large `context.md` by the time they finish. The auto-summary mechanism in `../../moderate-debate/references/context.md` keeps later turns tractable.

## Listing runs

Senate exposes run listing implicitly: the user can `ls .senate/runs/` to see all runs in the current workspace. Each `state.json` shows the status; filtering by `status: paused_at_checkpoint` finds what's waiting on the user.

A future helper (not yet shipped) may render a status table; for now, manual inspection is the convention.

## Cleanup

Run directories are never garbage-collected automatically. Users can safely `rm -rf .senate/runs/<id>` once they're done — senate treats missing directories as non-existent runs.
