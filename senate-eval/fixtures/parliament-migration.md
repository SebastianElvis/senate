---
fixture_id: parliament-migration
format: parliament
roster:
  - {role: mp_pro, cli: codex}
  - {role: mp_con, cli: gemini}
  - {role: mp_neutral, cli: kimi}
  - {role: speaker, cli: claude}
rounds: 2
---

# Task

Should a mid-sized team (10 engineers, 4 years of Python in production) migrate their core ingest service — currently Python, handling ~500 events/sec, with a team-wide comfort with async/await — to Rust, for performance and memory-footprint reasons? The team has zero production Rust experience today.

Debate this as a parliament. Each MP gives an opening statement, rebuttals over 2 rounds, then votes. The speaker writes the verdict.

# Expected verdict shape

- `## Decision` section contains a clear `yes`, `no`, or `remand`.
- `## Rationale` section cites ≥ 2 turn numbers in the form `T<N>`.
- `## Dissent` section is non-empty unless the vote was 3–0 in one direction.
- Vote tally line is present and sums to 3 (MPs only; speaker tie-breaks only if needed).
- At least one argument mentions either team experience, hiring, or learning curve.
- At least one argument mentions performance, latency, or memory.

# Notes

This fixture is deliberately a balanced question — neither "obviously yes" nor "obviously no". A healthy parliament should produce dissent regardless of the final vote.
