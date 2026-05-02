---
fixture_id: smoke-cursor-kimi
format: parliament
roster:
  - {role: mp_pro, cli: cursor}
  - {role: mp_con, cli: kimi}
  - {role: speaker, cli: claude}
rounds: 1
assertions:
  - {kind: section_contains_one_of, section: Decision, values: ["yes", "no", "remand"]}
  - {kind: section_present, section: Rationale}
judge_rubrics: [verdict]
---

# Task

Should a small team prefer trunk-based development over long-lived feature branches? Decide yes / no / remand. Keep arguments short — this fixture exists to smoke-test the cursor and kimi CLI playbooks, not to settle the question.

# Expected verdict shape

- `## Decision`: yes / no / remand.
- `## Rationale`: at least one paragraph.

# Notes

Smoke fixture — minimal 2-MP parliament + speaker, single round, narrow question. Mirrors `_smoke-parliament.md` but exercises `cursor-agent` and `kimi` so that recent playbook changes (kimi `--quiet` invocation; cursor `--trust` requirement, no `-m` short flag, JSON `result` key) get touched by CI/replay runs. Not part of the capability set.
