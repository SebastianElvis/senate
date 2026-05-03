# Checkpoints — human-in-the-loop pause / resume

A checkpoint is a pause point declared in the agenda where the moderator stops, surfaces the current state to the user, and waits for approval before continuing. Without checkpoints, a multi-stage agenda with an edit loop (draft → review → revise → accept) would be fully autonomous — which is great for efficiency and terrible for alignment.

## Checkpoint types (declared in the agenda)

### `none` (default)

No pause. The moderator runs through.

### `optional`

Stage runs without pausing, but the user may interrupt during or immediately after. Moderator writes a "checkpoint available" signal to `state.json` that an external watcher could pick up. Users can also ask the host agent to pause at any time.

### `required`

The agenda always pauses after this stage. User must explicitly resume. Use for:

- Publication gates (before anything becomes final).
- High-cost next stages (don't burn budget without confirmation).
- Decisions that touch external systems.

### `conditional`

The stage declares a condition on its own output; the moderator evaluates it and pauses iff true.

The condition expression grammar is uniform across all checkpoint files: every condition starts with `stage.verdict.` (the synthesis turn's structured JSON), `stage.bindings.<name>` (a value from the stage's `output_bindings`), or `stage.failures` (count of `error`-coded transcript lines for this stage). Bare binding names without a `stage.` prefix are not valid.

Common conditions:

- `stage.verdict.disposition == "remand"` — re-open prior stage.
- `stage.verdict.confidence < 0.5` — low-confidence result.
- `stage.bindings.resolution_rate < 0.5` — too many open comments.
- `stage.failures > 2` — too many agent failures to trust the output.

In the agenda's stage frontmatter:

```yaml
checkpoint: conditional
condition: "stage.verdict.confidence < 0.5"
```

## State surfaced at a checkpoint

When paused, the moderator presents:

1. **What just happened** — stage name, verdict disposition, number of turns, wall-clock, token usage.
2. **Verdict preview** — first 40 lines of `<run-dir>/stages/<N>/verdict.md`, with a link to the full file.
3. **What's next** — the name of the next stage and its roster.
4. **Remaining budget** — wall-clock and tokens left in the global cap.
5. **User options** — continue / revise / abort / modify-roster.

Example surface:

```markdown
⏸ Paused at checkpoint after stage 2 (review).

**Just completed:** stage 2 (review) — disposition: finalized, 3 commenters, 412s wall-clock, 98k tokens.

**Next stage:** 3 (synthesize) — roster: member=claude, editor=claude.

**Budget remaining:** 488s / 900s cap, 102k / 200k tokens.

**Preview of stage 2 verdict:**
<first 40 lines of verdict.md>

[Full verdict: `.senate/runs/2026-04-20-1500-draft-review-finalize/stages/2-review/verdict.md`]

**Options:**
- `continue` — proceed to stage 3.
- `revise` — edit the stage 2 verdict before continuing (moderator re-extracts bindings on resume).
- `modify-roster` — change who plays which role in stage 3.
- `re-plan` — call back to debate-agenda for a structural change.
- `abort` — terminate the run; keep all artifacts.
```

## State persistence

Before pausing, the moderator writes `<run-dir>/state.json` with `status: paused_at_checkpoint` and the `checkpoint` block populated (`paused_after_stage`, `paused_at`, `type`, `next_stage`). Full schema in `../../senate/references/workspace.md` (`## state.json schema`). If the moderator's process crashes during the pause, resume must still work — `state.json` is the source of truth.

## Resume

User resumes via the host agent: *"Resume run `<run-id>`"*. `senate` invokes the moderator on the run dir.

Moderator procedure on resume:

1. Read `state.json`. Confirm `status == paused_at_checkpoint`.
2. **Reconcile derived projections from the transcript.** A crash between transcript append and projection write (see `../SKILL.md` § Commit pattern) can leave `context.md` / `agents/<cli>.md` lagging the transcript by one entry. Before building any new prompt, walk `transcript.jsonl` end-to-end and rewrite both files from the transcript's `context_delta` / `private_delta` fields and `summarize_context` ledger actions per `../../senate/references/workspace.md` § Invariants on derived projections. The transcript is the source of truth; the `.md` files are regenerated. (This is a no-op for clean shutdowns and idempotent if run twice.)
3. Read the most recent stage's `verdict.md` (re-read, in case user edited).
4. Re-extract `output_bindings` per the agenda's stage spec.
5. If bindings changed, update `bindings.json` and bump a snapshot version.
6. Continue from `checkpoint.next_stage`.

If the user wants to resume with overrides (different CLI, different budget), they say so; the moderator passes the overrides through `debate-agenda` for an agenda revision before continuing.

## User options at a checkpoint

- **`continue`** — proceed to `checkpoint.next_stage`.
- **`revise`** — moderator sets `status: revising`. User edits `verdict.md` and any relevant turn files manually, then says "resume". Moderator re-extracts bindings from the edited verdict and continues. The moderator does **not** re-run the prior stage. Revise is a human edit, not a re-debate.
- **`modify-roster`** — change who plays which role in the next stage. Moderator updates the agenda's roster (with a `## Revisions` entry) and resumes.
- **`re-plan`** — moderator calls `../../debate-agenda/` with the prior agenda + recent transcript slice + the user's reason. The planner returns a revised agenda with a new `## Revisions` entry and `status: ready` (so the moderator can resume immediately). Completed stages are immutable; their verdicts and bindings remain.
- **`abort`** — `status: aborted`. All artifacts preserved. Run directory is renamed from `<id>` to `<id>.aborted` to make it obvious in listings.

In every case, the moderator (not the planner) is responsible for transitioning the run's `state.json` status field. The planner only writes to `agenda.md`.

## Eval mode

Fixture runs (the `evals` harness) bypass `required` checkpoints with an automatic `continue`. They write to `state.json` as if paused, then immediately resume. This means eval bypasses the primary safety function of checkpoints — which is fine, since eval is measuring process mechanics, not final output correctness.

## Guardrails

- **Never skip `required` checkpoints** outside eval mode.
- **Always write `state.json` before pausing.** Crashes during pause must still be resumable.
- **No wall-clock timeout on a pause** by default — a run can sit paused for days. If the user wants a deadline, they set a wake-up reminder externally (e.g., the host's scheduler).
