# Workspace layout

All runtime state for a debate lives in the **user's current working directory**, under `.senate/`. The skill repo is never written to at runtime.

## Layout

```
<cwd>/
  .senate/
    runs/
      2026-04-20-1432-parliament/
        roster.json          # who played which role, task, format, rounds
        transcript.jsonl     # append-only, one line per turn
        verdict.md           # final synthesis
        agents/
          codex.1.log        # stdout for codex, turn 1
          codex.2.log
          gemini.1.log
          claude.1.log
          ...
```

## `roster.json`

```json
{
  "run_id": "2026-04-20-1432-parliament",
  "format": "parliament",
  "task": "Should we migrate the ingest service from Python to Rust?",
  "started_at": "2026-04-20T14:32:05Z",
  "rounds": 3,
  "roster": [
    { "role": "mp_pro", "cli": "codex", "model": "gpt-5-codex" },
    { "role": "mp_con", "cli": "gemini", "model": "gemini-2.5-pro" },
    { "role": "mp_neutral", "cli": "kimi", "model": "kimi-k2" },
    { "role": "speaker", "cli": "claude", "model": "claude-sonnet-4-6" }
  ]
}
```

## `transcript.jsonl`

One JSON object per line. Append-only. Never rewrite past lines.

Schema:

```json
{
  "turn": 1,
  "phase": "opening",
  "role": "mp_pro",
  "cli": "codex",
  "ts": "2026-04-20T14:32:18Z",
  "prompt_tokens": 1840,
  "completion_tokens": 612,
  "exit_code": 0,
  "text": "...full agent reply...",
  "structured": { "vote": "yes", "reason": "..." }
}
```

`structured` is present only when the format's output contract produced a parseable block. On failure, include `"error": "contract violation"` and omit `structured`.

## `verdict.md`

Human-readable synthesis. Structure:

```markdown
# Verdict — <format>

**Task:** <one-line task>
**Run:** `.senate/runs/<id>/`
**Roster:** <role: cli>, ...

## Decision

<one paragraph>

## Rationale

<bullets with turn references like [T4, T7]>

## Dissent

<minority opinion, if any>
```

## Conventions

- Timestamps are ISO 8601 UTC.
- `run_id` format: `YYYY-MM-DD-HHMM-<format>`. Lowercase, hyphens.
- `.senate/` should be gitignored in the user's repo by default. If the user wants to commit debate history, they can remove it from `.gitignore`.
