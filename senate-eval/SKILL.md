---
name: senate-eval
description: Evaluation harness for the senate skill. Runs fixture debates against a roster of CLIs and reports per-CLI contract-compliance, failure distribution, and verdict quality. Use when the user wants to measure which models are reliable in which debate formats, benchmark a new CLI playbook, or verify a format file after changes.
---

# senate-eval — evaluation harness

A sibling skill to `senate`. Does not run real debates — runs **fixtures**, measures the run, and writes a report. The primary output is a per-CLI, per-format contract-compliance table.

## When to trigger

- User asks to evaluate, benchmark, or test the senate skill.
- User adds a new CLI playbook (`skills/invoke-agent/<name>.md`) and wants to validate it.
- User edits a format file and wants to confirm it still produces parseable output.
- CI job running nightly.

## What a fixture is

A fixture is a markdown file under `fixtures/` describing a canned debate task, the expected roster, and the expected *shape* of the verdict (not its content). Fixtures are replayable — `senate-eval` uses the H1 replay machinery.

Fixture schema:

```markdown
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

<the debate task, verbatim, as the user would phrase it>

# Expected verdict shape

- Decision section contains "yes" or "no" (not "remand").
- Rationale cites ≥2 turn numbers.
- Dissent is non-empty unless vote was unanimous.
```

## Fixtures shipped

| Fixture | Format | Purpose |
| --- | --- | --- |
| `parliament-migration.md` | parliament | Canonical 3-MP + speaker; open decision question |
| `court-pr-review.md` | court | Canonical 3-role; adversarial review of a small diff |
| `consensus-api-design.md` | consensus | 3 contributors converging on an interface |

## How a run works

1. Orchestrator reads the fixture.
2. Runs the debate per the senate skill's normal flow, writing to `.senate-eval/runs/<fixture>-<timestamp>/`.
3. At end of run, `scoring.md` spec is applied to produce a score row.
4. Appends one line to `.senate-eval/scorecard.jsonl`.

## Scorecard schema

Each line of `.senate-eval/scorecard.jsonl`:

```json
{
  "fixture_id": "parliament-migration",
  "run_id": "parliament-migration-2026-04-20-1432",
  "ts": "2026-04-20T14:45:11Z",
  "roster": [{"role": "mp_pro", "cli": "codex"}, "..."],
  "contract_compliance": {
    "codex": {"attempts": 3, "first_try": 3, "retried": 0, "failed": 0},
    "gemini": {"attempts": 3, "first_try": 2, "retried": 1, "failed": 0},
    "..."
  },
  "failures": {"auth": 0, "rate_limit": 0, "timeout": 0, "contract_violation": 1, "refusal": 0, "unknown": 0},
  "verdict_shape_pass": true,
  "wall_clock_sec": 412,
  "tokens": 138420
}
```

## Running evals

Invoked by the user or an orchestrator:

- *"Run senate-eval on all fixtures."* → iterate each fixture, produce a summary table.
- *"Run the parliament-migration fixture with kimi in the `mp_con` slot."* → override, one-off run.
- *"Show me the last 7 days of scorecard data."* → read scorecard.jsonl, tally, render markdown.

## Reports

The summary report (`.senate-eval/report-<date>.md`) is a markdown document with:

- **Per-CLI compliance rate** — first-try success / retried / failed, per format.
- **Failure distribution** — which error class dominates, per CLI.
- **Regression flags** — any CLI whose rate dropped >10 percentage points vs. previous run.
- **Recommendations** — "gemini's contract_violation rate in parliament is 23%; consider tightening the vote contract's re-prompt template".

## Files in this skill

- `SKILL.md` — this file.
- `scoring.md` — the scoring rubric applied to each run.
- `fixtures/parliament-migration.md`
- `fixtures/court-pr-review.md`
- `fixtures/consensus-api-design.md`

## Adding a fixture

Copy one of the shipped fixtures, edit the task and expected-shape sections, and drop into `fixtures/`. Fixtures must be deterministic in structure — don't reference external state or time-sensitive topics.
