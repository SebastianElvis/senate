---
fixture_id: court-pr-review
format: court
roster:
  - {role: prosecution, cli: codex}
  - {role: defense, cli: claude}
  - {role: judge, cli: gemini}
rounds: 2
---

# Task

Judge this pull request. The team is proposing to replace a widely-used internal helper `withRetry(fn, attempts)` — currently backed by exponential backoff with jitter — with a minimal version that does only linear backoff and no jitter, claiming "the old one is overengineered". The diff is ~30 lines, touches 4 files.

Proposition on trial: **"This simplification should be merged."**

Prosecution: argue the merge is unsafe / incomplete.
Defense: argue the merge is sound.
Judge: rule sustain / dismiss / remand.

# Expected verdict shape

- `## Decision` section is exactly one of: `sustain`, `dismiss`, `remand` (case-insensitive match).
- `## Reasoning` cites ≥ 2 turn numbers in the form `T<N>`.
- `## Dissent` is non-empty.
- Prosecution turn 1 contains a numbered list of objections (at least 3 items).
- Defense turn 1 references each numbered objection by number.
- Judge's reasoning references at least one point from prosecution AND at least one from defense.

# Notes

This fixture has a concrete technical subject (retry logic) where jitter is a well-known correctness concern. A working court format should surface the jitter issue via prosecution and force the defense to address it.
