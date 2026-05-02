---
fixture_id: red-team-auth
format: red-team
roster:
  - {role: attacker, cli: codex}
  - {role: defender, cli: claude}
  - {role: arbiter, cli: gemini}
rounds: 3
assertions:
  - {kind: section_present, section: Attacks attempted}
  - {kind: section_present, section: Mitigations}
  - {kind: section_present, section: Residual risks}
  - {kind: section_regex, section: Attacks attempted, pattern: "^\\s*\\d+\\.", min_count: 3}
  - {kind: section_regex, section: Mitigations, pattern: "^\\s*\\d+\\.", min_count: 3}
  - {kind: section_contains_one_of, section: Verdict, values: ["safe", "unsafe", "needs work"]}
judge_rubrics: [verdict, transcript_quality]
---

# Task

Audit the following authentication scheme for a public API:

- Each user gets a long-lived bearer token at signup, stored in a Postgres table.
- Clients send `Authorization: Bearer <token>` on every request.
- The server compares the token against the DB row using a plain `WHERE token = $1` query.
- Tokens never rotate; users can request a manual reset by emailing support.

The attacker enumerates concrete attacks (numbered list, ≥3). The defender proposes mitigations (numbered list, ≥3, addressing the attacker's points by number). The arbiter rules `safe`, `unsafe`, or `needs work`, with residual risks documented.

# Expected verdict shape

- `## Attacks attempted` is a numbered list with at least 3 items.
- `## Mitigations` is a numbered list with at least 3 items, each tying back to one or more attacks.
- `## Residual risks` is non-empty.
- `## Verdict` is one of `safe`, `unsafe`, `needs work`.

# Notes

Authentication audits are a known sweet spot for red-team format. A working format should produce attacker items like "timing attack on token comparison", "no rate limit → online brute force", "no rotation → leaked tokens never expire". This fixture detects formats that produce only generic security platitudes.
