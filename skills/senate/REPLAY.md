# Deterministic replay

A `transcript.jsonl` file is replayable when re-running it against the same roster and format produces the same *structure* of debate — same turn order, same prompts constructed, same contract validation points. The *content* of each turn will of course differ run to run (models are non-deterministic), but the orchestration must be reproducible.

Replay is how we compare models, catch regressions, and debug debates without burning fresh tokens on already-answered phases.

## What replay is for

Three use cases, in priority order:

1. **Model swap.** *"Re-run last week's parliament but replace gemini with kimi."* Same format, same other participants, just one role changes.
2. **Deterministic debug.** A debate ended with a strange verdict; rerun to verify the structure of the argument, with CLIs pinned (where possible) to the same versions.
3. **Eval fixtures.** `senate-eval` feeds replayable runs to measure per-CLI contract compliance over time.

Replay is **not** for exact byte-identical reproduction. LLMs are not deterministic.

## Replay contract

A transcript is replayable iff every turn line contains:

- `turn` (int, monotonic)
- `phase` (string, matches a phase name in the format file)
- `role` (string, matches a role in `roster.json`)
- `cli` (string, the CLI that played this turn)
- `ts` (ISO 8601 UTC)
- `prompt` (the full prompt that was sent, not just a summary) — **new field**, required for replay
- `exit_code`, `text` or `error`

`prompt` is large. On-disk it may be gzipped (`prompt_gz` base64) for very long transcripts; orchestrator decompresses on replay.

## Directory layout

Replayed runs live alongside the original:

```
.senate/runs/
  2026-04-20-1432-parliament/           # original
  2026-04-20-1432-parliament.replay.1/  # first replay
  2026-04-20-1432-parliament.replay.2/
```

The replay directory contains its own `roster.json` (noting overrides), `transcript.jsonl`, `verdict.md`, and a `replay_manifest.json` recording the parent run and what was changed.

## `replay_manifest.json`

```json
{
  "parent_run_id": "2026-04-20-1432-parliament",
  "replayed_at": "2026-04-22T09:15:00Z",
  "overrides": {
    "mp_con": {"cli": "kimi", "model": "kimi-k2"}
  },
  "format_version_match": true,
  "invoke_agent_version_match": true
}
```

If the skill repo has changed between original and replay (e.g., the parliament format was edited), set the `*_version_match` flags to `false` and include the git SHAs. Replay still works, but results are not directly comparable to the original.

## Replay procedure

When the user says *"replay run X, swapping role R to CLI C"*:

1. Read the original `roster.json` and `transcript.jsonl`.
2. Read the format file at `debate-format/<format>.md` (current version; flag mismatch if changed).
3. Read the CLI playbooks at `invoke-agent/<cli>.md` for every CLI in the (new) roster.
4. Mint the replay directory per the layout above.
5. Walk the phases in the format file (**not** the original transcript — the format is canonical). For each phase:
   - Rebuild the prompt from the role brief + transcript slice (from the replay transcript, not the original) + turn instruction.
   - For unchanged roles, re-invoke the same CLI.
   - For overridden roles, invoke the new CLI.
6. Append to `transcript.jsonl` as usual.
7. Run synthesis. Write `verdict.md`.

## Diffing

`replay_manifest.json` makes it easy to diff two verdicts programmatically later. For now, assume a human or a dedicated `senate-eval` workflow does the comparison.

## What does NOT require replay

- Re-reading `verdict.md` from a past run.
- Continuing a workflow (H3) from a checkpoint — that's resume, not replay.
- Running the same format on a fresh task — that's just a new run.

## Constraints

- Replay is only meaningful for runs whose `format_version_match == true`. Otherwise you're not replaying, you're re-interpreting.
- Do not replay across more than one format-file revision without reviewing the diff first.
- Model versions drift silently (e.g., `gpt-5-codex` may be updated server-side). Record `model` in `roster.json` but do not assume it's reproducible.
