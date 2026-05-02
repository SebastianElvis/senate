---
fixture_id: smoke-parliament
format: parliament
roster:
  - {role: mp_pro, cli: codex}
  - {role: mp_con, cli: claude}
  - {role: speaker, cli: claude}
rounds: 1
assertions:
  - {kind: section_contains_one_of, section: Decision, values: ["yes", "no", "remand"]}
  - {kind: section_present, section: Rationale}
judge_rubrics: [verdict]
---

# Task

Should a small team adopt mandatory code review for every PR, including 1-line typo fixes? Decide yes / no / remand. Keep arguments short — this is a smoke test fixture and the question is intentionally narrow.

# Expected verdict shape

- `## Decision`: yes / no / remand.
- `## Rationale`: at least one paragraph.

# Notes

Smoke fixture — minimal 2-MP parliament + speaker, single round, narrow question. Not part of the capability set; exists so the harness has a tiny footprint that runs anywhere `codex` and `claude` are installed (no `kimi`/`gemini` dependency).
