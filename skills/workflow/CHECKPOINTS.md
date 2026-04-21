# Checkpoints — human-in-the-loop

A checkpoint is a pause point in a workflow where the orchestrator stops, surfaces the current state to the user, and waits for approval before continuing. Without checkpoints, a workflow with an edit loop (draft → review → revise → accept) would be fully autonomous — which is great for efficiency and terrible for alignment.

## Checkpoint types

### `required`

The workflow always pauses after this stage. User must explicitly resume. Use for:

- Publication gates (before anything becomes final).
- High-cost next stages (don't burn budget without confirmation).
- Decisions that touch external systems (even if senate itself doesn't push, a human might act on the verdict).

### `optional`

Stage runs without pausing, but the user may interrupt during or immediately after. Orchestrator writes a "checkpoint available" signal to `workflow_state.json` that a watcher could pick up. Users can also `senate pause-workflow <id>` at any time.

### `conditional`

The stage declares a condition on its own output; the orchestrator evaluates it and pauses iff true. Common conditions:

- `stage.verdict.disposition == "remand"` — re-open prior stage.
- `stage.verdict.confidence < 0.5` — low-confidence result.
- `stage.failures > 2` — too many agent failures to trust the output.

Expressed in the workflow file as:

```yaml
checkpoint: conditional
condition: "stage.verdict.confidence < 0.5"
```

## State surfaced at a checkpoint

When paused, the orchestrator presents:

1. **What just happened** — stage name, verdict disposition, number of turns, wall-clock, token usage.
2. **Verdict preview** — first 40 lines of `stages/<N>/verdict.md`, with a link to the full file.
3. **What's next** — the name of the next stage and its roster.
4. **Remaining budget** — wall-clock and tokens left in the global workflow cap.
5. **User options** — continue / revise / abort / modify-roster.

Example surface:

```markdown
⏸ Workflow paused at checkpoint: `final_doc_accepted`

**Just completed:** stage 2 (review) — disposition: finalized, 3 commenters, 412s wall-clock, 98k tokens.

**Next stage:** 3 (synthesize) — roster: author=claude, editor=claude.

**Budget remaining:** 488s / 900s cap, 102k / 200k tokens.

**Preview of stage 2 verdict:**
<first 40 lines of verdict.md>

[Full verdict: `.senate/workflows/rfc-pipeline-2026-04-20-1500/stages/2-review/verdict.md`]

**Options:**
- `continue` — proceed to stage 3.
- `revise` — edit the stage 2 verdict before continuing (orchestrator reads the file again on resume).
- `modify-roster` — change who plays which role in stage 3.
- `abort` — terminate the workflow; keep all artifacts.
```

## Resume

User resumes with a single command (invoked in their host agent):

*"Resume workflow `rfc-pipeline-2026-04-20-1500`"*.

Orchestrator:

1. Reads `workflow_state.json`. Confirms `status == "paused"`.
2. Reads the current stage's verdict from disk (re-read, in case user edited it).
3. Re-extracts bindings (may have changed if user edited verdict).
4. Continues with the next stage.

If the user wants to resume with overrides (different CLI, different budget), they say so; orchestrator updates `workflow_state.json` before continuing.

## Revise semantics

If the user chooses `revise`:

1. Orchestrator marks the stage as `status: revising` in `workflow_state.json`.
2. User edits `verdict.md` and any relevant turn files manually.
3. User says "resume".
4. Orchestrator re-extracts bindings from the edited verdict and continues.

Orchestrator does NOT re-run the prior stage. Revise is a human edit, not a re-debate. If the user wants a re-debate, they abort this workflow and start a fresh one, or use `revise_and_repost` disposition semantics from the format.

## Abort

`status: aborted`. All artifacts preserved. Workflow run directory renamed from `rfc-pipeline-2026-04-20-1500` to `rfc-pipeline-2026-04-20-1500.aborted` to make it obvious in listings.

## Interaction with `senate-eval`

Fixtures for workflows must declare expected checkpoint behavior — whether each checkpoint was hit, whether the test auto-continued (eval mode bypasses `required` checkpoints with a default continue), whether the verdict shape held through the pipeline.

Eval-mode checkpoints never prompt a real user; they write to `workflow_state.json` and continue immediately. This means eval bypasses the primary safety function of checkpoints — which is fine, since eval is measuring process mechanics, not final output correctness.

## Guardrails

- **Never skip `required` checkpoints** outside eval mode.
- **Always write `workflow_state.json` before pausing**. If the orchestrator crashes during the pause itself, resume must work.
- **Timeout on pause**: checkpoints have no wall-clock timeout by default — a workflow can sit paused for days. If the user wants a deadline, they set a wake-up reminder externally.
