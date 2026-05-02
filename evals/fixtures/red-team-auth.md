---
fixture_id: red-team-auth
format: red-team
roster:
  - {role: attacker, cli: codex}
  - {role: defender, cli: claude}
  - {role: judge, cli: gemini}
rounds: 1
assertions:
  - {kind: section_present, section: Ruling}
  - {kind: section_present, section: Strongest attacks}
  - {kind: section_present, section: Effective defenses}
  - {kind: section_present, section: Outstanding risks}
  - {kind: section_regex, section: Strongest attacks, pattern: "^\\s*\\d+\\.", min_count: 2}
  - {kind: section_contains_one_of, section: Ruling, values: ["survives", "survives_with_mitigations", "fails"]}
judge_rubrics: [verdict, transcript_quality]
---

# Task

Audit the following authentication scheme for a public API:

- Each user gets a long-lived bearer token at signup, stored in a Postgres table.
- Clients send `Authorization: Bearer <token>` on every request.
- The server compares the token against the DB row using a plain `WHERE token = $1` query.
- Tokens never rotate; users can request a manual reset by emailing support.

The attacker enumerates concrete failure modes (numbered list, ≥3). The defender classifies each as non-applicable, accepted, mitigated, or unresolved. The judge rules `survives`, `survives_with_mitigations`, or `fails`, with outstanding risks documented.

# Expected verdict shape

- `## Ruling` is one of `survives`, `survives_with_mitigations`, `fails`.
- `## Strongest attacks` lists at least 2 concrete failure modes.
- `## Effective defenses` explains which defenses resolved an attack.
- `## Outstanding risks` is present and documents unresolved or weakly mitigated attacks.

# Notes

Authentication audits are a known sweet spot for red-team format. A working format should produce attacker items like "timing attack on token comparison", "no rate limit → online brute force", "no rotation → leaked tokens never expire". This fixture detects formats that produce only generic security platitudes.
