---
name: evals
description: Evaluation harness for the senate skill. Runs fixture debates end-to-end, applies deterministic graders against the run-dir contract, and uses Claude CLI as an LLM judge for quality dimensions (verdict, agenda, meeting-notes, transcript). Use when the user wants to measure which models are reliable in which formats, benchmark a new CLI playbook, or verify a format file after changes.
---

# evals — evaluation harness

A sibling skill to `senate`. Runs **fixtures** through the full senate lifecycle, then grades the result with two complementary signals:

- **Deterministic graders** — schema/contract conformance against `skills/senate/references/workspace.md`. Cheap, run first.
- **LLM judges** — quality of `verdict.md`, `agenda.md`, `meeting-notes.md`, and transcript process. Invoked via `claude -p --output-format json` (no API key needed; uses your Claude Code OAuth session).

Methodology follows [Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) — capability vs. regression sets, deterministic + model-based + (eventual) human review, eval-driven iteration.

## When to trigger

- User asks to evaluate, benchmark, or test the senate skill.
- User adds a new CLI playbook (`skills/invoke-agent/references/<name>.md`) and wants to validate it.
- User edits a format file and wants to confirm it still produces parseable output.
- CI job running nightly.

## Layout

```
evals/
  SKILL.md            # this file
  scoring.md          # rubric for the deterministic side
  run.sh              # thin entrypoint (calls scripts/run_eval.py)
  fixtures/           # one fixture per .md file
  judges/             # markdown rubrics, one per LLM-judge dimension
    verdict.md
    agenda.md
    meeting_notes.md
    transcript_quality.md
    pairwise.md       # for regression A/B comparison
  scripts/
    run_eval.py       # orchestrates a fixture: spawn senate → grade → judge
    grade_deterministic.py  # universal contract + fixture assertions
    run_judge.py      # invoke one LLM judge against one artifact
    report.py         # roll up scorecard.jsonl into markdown
  stubs/              # CLI shims for replay-mode harness runs
    _stub.py
    {claude,codex,gemini,cursor,kimi} -> _stub.py
  .evals/             # gitignored; runtime output (scorecard.jsonl, reports)
```

## Fixture schema

Each fixture lives in `fixtures/<id>.md`. Frontmatter declares the canned setup; body has the task and human-readable expectations.

```markdown
---
fixture_id: parliament-migration
format: parliament
preset: null
roster:
  - {role: mp_pro, cli: codex}
  - {role: mp_con, cli: gemini}
  - {role: mp_neutral, cli: kimi}
  - {role: speaker, cli: claude}
rounds: 2
assertions:
  - {kind: section_contains_one_of, section: Decision, values: ["yes", "no", "remand"]}
  - {kind: section_turn_refs, section: Rationale, min: 2}
  - {kind: section_present, section: Dissent}
judge_rubrics: [verdict, agenda, meeting_notes]
---

# Task
<the debate task>

# Expected verdict shape
<human-readable bullets — for documentation; the machine-checkable form is the `assertions:` block>
```

`preset` is required for closed-family primitives (`court`, `panel`, `workshop`) and omitted or null for `parliament` and `brainstorm`.

### Assertion rule kinds

Supported in `assertions:`:

- `section_present` — heading exists with non-empty body.
- `section_contains_one_of` — body contains one of `values` (case-insensitive).
- `section_regex` — body matches `pattern` at least `min_count` times.
- `section_regex_count` — body matches `pattern` exactly N times. Supply any of `min`, `max`, `exact`. Use this when "at least one" is too lax (e.g., the artifact section must contain *exactly two* HTTP endpoints).
- `section_turn_refs` — body contains ≥ `min` `T<n>` references. Pass `validate_against_transcript: true` to also verify the cited turn numbers actually exist in `transcript.jsonl` (catches hallucinated citations).
- `section_mentions_any` / `text_mentions_any` — substring match against a list of terms.
- `transcript_turn_regex` — the Nth turn for a given role contains ≥ `min_count` regex matches.

For anything more nuanced, use an LLM judge.

## Fixtures shipped

| Fixture | Format | Preset | Tests |
| --- | --- | --- | --- |
| `parliament-migration.md` | parliament | — | Open policy question; vote tally + dissent |
| `court-pr-review.md` | court | court | Adversarial review; numbered objections |
| `consensus-api-design.md` | workshop | consensus | Convergence on artifact |
| `peer-review-rfc.md` | panel | peer-review | Blind reviewer comments + editor decision |
| `red-team-auth.md` | court | red-team | Attacker/defender numbered exchanges |

Capability set today. Once a format hits ≥95% pass@3 across its fixtures (the H1 quality bar from `dev/PRODUCT.md`), we promote those fixtures to a `fixtures/regression/` set.

## Running

```bash
# All fixtures, default models (sonnet 4.6 orchestrator, opus 4.7 judge)
evals/run.sh

# A specific fixture
evals/run.sh fixtures/parliament-migration.md

# Override models
evals/run.sh --orchestrator-model claude-opus-4-7 --judge-model claude-opus-4-7

# Generate a markdown report from accumulated scorecard data
python3 evals/scripts/report.py --out evals/.evals/report.md
```

The runner needs the `senate` skill installed in your Claude skills directory (`npx skills add SebastianElvis/senate`, or symlink the local `skills/` tree). The orchestrator runs in a fresh tmp workspace per fixture; the run-dir lands at `<workspace>/.senate/runs/<id>/`.

### Stub-CLI replay (CI mode)

For fast smoke tests without burning quota, prepend `evals/stubs/` to `PATH`. The stubs hash the prompt, look up `evals/stubs/recordings/<cli>/<hash>.json`, and replay. To capture recordings against the real CLIs, run with `EVALS_STUB_MODE=record EVALS_REAL_CLAUDE=$(which claude)` etc. Recordings are gitignored.

The hash key includes a `RECORDING_VERSION` constant (declared in `stubs/_stub.py`). Bump it when the senate skill's prompt template or output contract changes in a way that would invalidate prior recordings — old hashes stop matching, the harness reports "no recording", and you re-record. This is intentional: silent prompt drift would otherwise let stale recordings paper over real regressions.

## Scorecard schema

Each line of `evals/.evals/scorecard.jsonl` is one fixture run. Provenance fields (`fixture_sha256`, `repo_commit`, `claude_cli_version`) are recorded so a row can be re-evaluated against the same source state later.

```json
{
  "fixture_id": "parliament-migration",
  "fixture_path": "evals/fixtures/parliament-migration.md",
  "fixture_sha256": "aa49d430c911413c",
  "repo_commit": "e21b3fafe48b",
  "claude_cli_version": "2.1.126 (Claude Code)",
  "started_at": "2026-04-30T10:00:00+00:00",
  "completed_at": "2026-04-30T10:05:12+00:00",
  "wall_clock_sec": 312,
  "orchestrator_model": "claude-sonnet-4-6",
  "judge_model": "claude-opus-4-7",
  "workspace": "/tmp/evals-parliament-migration-XYZ",
  "orchestrator_exit": 0,
  "run_dir": "/tmp/evals-parliament-migration-XYZ/.senate/runs/...",
  "deterministic": {
    "deterministic_pass": true,
    "checks": [
      {"check": "agenda_schema", "pass": true, "metrics": {...}},
      {"check": "transcript_schema", "pass": true, "metrics": {"turns": 8, "errors": 0, "by_cli": {...}}},
      {"check": "state_terminal", "pass": true},
      {"check": "verdict_md_present", "pass": true},
      {"check": "meeting-notes_md_present", "pass": true},
      {"check": "fixture_assertions", "pass": true, "rules": [...]}
    ]
  },
  "judges": {
    "verdict": {
      "rubric": "verdict",
      "model": "claude-opus-4-7",
      "ts": "2026-04-30T10:05:08+00:00",
      "rubric_sha256": "13ab...",
      "judgement": {"scores": {...}, "overall_score": 4.2, "pass": true, "failure_modes": [], "reasoning": "..."},
      "wrapper_meta": {"usage": {...}}
    }
  },
  "judge_failures": [],
  "pass": true
}
```

A run is `pass: true` only if `deterministic.deterministic_pass` is true AND every requested judge returned a parseable judgement with `pass: true`. A missing or schema-invalid judge counts as a fail (see `judge_failures`) — this prevents silent judge degradation from producing false greens.

## Reports

`evals/scripts/report.py` reads `scorecard.jsonl` and emits a markdown rollup:

- **Latest fixture results** — per-fixture pass/fail with deterministic + judge scores.
- **Per-CLI contract compliance** — first-try / retried / failed aggregated across fixtures.
- **Judge score distribution** — mean/min/max per rubric.
- **Regressions** — fixtures that flipped PASS → FAIL since their previous run.

## Adding a fixture

1. Copy a similar fixture; edit `fixture_id`, `format`, `preset` when required, `roster`, task body.
2. Encode any structural expectations as `assertions:` in the frontmatter (use the rule kinds above).
3. Pick the relevant `judge_rubrics`. Default is `[verdict]` only.
4. Add a one-row entry to the "Fixtures shipped" table in this file.

Fixtures must be deterministic in structure — no time-sensitive topics, no external state.

## Pairwise (regression A/B) judge

Pairwise is **not** a per-fixture rubric — don't list it in a fixture's `judge_rubrics:`. Use it explicitly to compare two completed run dirs for the same fixture (e.g., before/after a skill edit):

```bash
python3 evals/scripts/run_judge.py --rubric pairwise \
  --fixture evals/fixtures/parliament-migration.md \
  --run-dir-a /path/to/old/run --run-dir-b /path/to/new/run \
  --model claude-opus-4-7
```

The harness invokes the judge twice (A/B then B/A) and only accepts a winner when both orderings agree — counterbalances position bias. Disagreement is recorded as `tie` with `consistent_across_orderings: false`.

## Adding a judge

1. Drop a new rubric file under `judges/<name>.md`. Follow the schema in `verdict.md` (rubric → pass/fail rule → failure-mode enum → output JSON contract → calibration anchors).
2. Add the rubric name to `ARTIFACT_FOR_RUBRIC` in `scripts/run_judge.py` so the invoker knows which run-dir files to inline.
3. Reference it from a fixture's `judge_rubrics:` list.

## Iteration loop

Per the methodology:

1. Run the eval. Read transcripts of failures.
2. Distinguish: bad grader, bad skill, or genuine model regression.
3. If grader was wrong → fix grader, re-run.
4. If skill was wrong → fix skill, add the failure as a new fixture under `fixtures/regression/`.
5. If model regressed → log it; consider model pin in CI.
6. Quarterly: spot-check 20 random judge decisions by hand. If agreement < 90%, revise the rubric.

## What the harness does NOT judge

- The *correctness* of the verdict (eval can't tell whether the parliament was right; only the user can).
- Whether the right CLI "won" the debate.
- Style or tone beyond what the rubrics explicitly score.
