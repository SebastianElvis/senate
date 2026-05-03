# Deterministic replay

A `transcript.jsonl` is replayable when re-running it against the same agenda produces the same *structure* of debate — same stage and turn order, same prompts constructed, same contract validation points. The *content* of each turn will of course differ run to run (models are non-deterministic), but the orchestration must be reproducible.

Replay is how we compare models, catch regressions, and debug debates without burning fresh tokens on already-answered phases.

## What replay is for

Three use cases, in priority order:

1. **Model swap.** *"Re-run last week's parliament but replace gemini with kimi."* Same agenda, same other participants, just one role's CLI changes.
2. **Deterministic debug.** A debate ended with a strange verdict; rerun to verify the structure of the argument, with CLIs pinned (where possible) to the same versions.
3. **Eval fixtures.** The eval harness feeds replayable runs to measure per-CLI contract compliance over time.

Replay is **not** for exact byte-identical reproduction. LLMs are not deterministic.

## Replay contract

A transcript is replayable iff every turn line conforms to the canonical schema in `workspace.md` (`## transcript.jsonl schema`) — in particular, the `prompt` field (the full prompt that was sent, not just a summary) must be present. Long prompts may be stored as `prompt_gz` (gzip + base64); the moderator decompresses on replay.

Because `context.md` and `agents/<cli>.md` are projections of the transcript (see `workspace.md` § Invariants on derived projections), a replay does not copy them — the moderator regenerates them from the replay transcript as the new run progresses.

## Directory layout

Replayed runs live alongside the original:

```
.senate/runs/
  2026-04-20-1432-parliament/           # original
  2026-04-20-1432-parliament.replay.1/  # first replay
  2026-04-20-1432-parliament.replay.2/
```

The replay directory contains its own `agenda.md` (a copy with override entries in the `## Revisions` log), `transcript.jsonl`, `notes.md`, per-stage `verdict.md`s, and a `replay_manifest.json` recording the parent run and what was changed. The same layout contract from `workspace.md` applies.

## `replay_manifest.json`

```json
{
  "parent_run_id": "2026-04-20-1432-parliament",
  "replayed_at": "2026-04-22T09:15:00Z",
  "overrides": {
    "stage_1": {
      "mp_con": {"cli": "kimi", "model": "kimi-k2"}
    }
  },
  "agenda_version_match": true,
  "format_version_match": true,
  "invoke_agent_version_match": true
}
```

If the skill repo has changed between original and replay (e.g., the parliament format was edited), set the `*_version_match` flags to `false` and include the git SHAs. Replay still works, but results are not directly comparable to the original.

## Replay procedure

When the user says *"replay run X, swapping role R to CLI C"*:

1. Read the original `agenda.md` and `transcript.jsonl`.
2. Read the format file at `../../debate-agenda/formats/<format>.md` (current version; flag mismatch if changed).
3. Verify that every CLI in the new roster has a playbook at `../../invoke-agent/references/<cli>.md`; do not load the playbooks into the replay/orchestrator context. The per-turn subagents dispatched by `../../moderate-debate/` read the relevant playbook when they run.
4. Mint the replay directory per the layout above.
5. Copy `agenda.md` to the replay dir; apply overrides as a new `## Revisions` entry.
6. Hand off to `../../moderate-debate/` as a normal run. The moderator walks stages and phases per the (modified) agenda, building prompts from scratch — **not** from the original transcript.
7. After the moderator finishes, hand off to `../../meeting-note/` as normal.

## Diffing

`replay_manifest.json` makes it easy to diff two verdicts programmatically later. For now, assume a human or a dedicated eval workflow does the comparison.

## What does NOT require replay

- Re-reading `notes.md` (or any `stages/<n>-<name>/verdict.md`) from a past run.
- Resuming a paused run from a checkpoint — that's resume, not replay (handled by `../../moderate-debate/references/checkpoints.md`).
- Running the same format on a fresh task — that's just a new run.

## Constraints

- Replay is only meaningful when `format_version_match == true` and `agenda_version_match == true`. Otherwise you're not replaying, you're re-interpreting.
- Do not replay across more than one format-file revision without reviewing the diff first.
- Model versions drift silently (e.g., `gpt-5-codex` may be updated server-side). Record `model` in `agenda.md` but do not assume it's reproducible.
