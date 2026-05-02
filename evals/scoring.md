# Scoring rubric (deterministic side)

How a single fixture run's *deterministic* checks become one entry in `scorecard.jsonl`. This file describes the contract-compliance / structural side only. The full scoring also runs LLM judges per `judges/<rubric>.md`; those produce the `judges` block in the scorecard. See `SKILL.md` for the combined scorecard schema and pass/fail rule.

## Inputs

- The fixture file (task, roster, rounds, expected verdict shape).
- The completed run directory under the harness workspace at `<workspace>/.senate/runs/<run-id>/` with `transcript.jsonl`, `notes.md`, and (in multi-stage runs) `stages/<n>/verdict.md` files. The `.evals/` directory is for scorecards and reports, not run dirs. Failure facts are in `transcript.jsonl` (per-turn `error` codes); there is no separate `failures.md`.

## Outputs per run

### 1. Contract compliance

Walk `transcript.jsonl`. For each turn that had a contract:

- `attempts = 1` if first reply parsed, `2` if re-prompt succeeded, else attempt count before giving up.
- `first_try = 1` if parsed on first reply, else `0`.
- `retried = 1` if re-prompt was needed AND succeeded.
- `failed = 1` if both attempts failed (recorded as `contract_violation`).

Sum per CLI to produce the `contract_compliance` object.

### 2. Failure distribution

Count occurrences of each `error` code in `transcript.jsonl`. Zero-fill missing codes.

### 3. Verdict shape

Apply each rule from the fixture's "Expected verdict shape" section to the first completed stage verdict by default (`stages/<n>-<name>/verdict.md`). These assertions describe the format's synthesis shape, and that shape now lives in the stage verdict, not in the merged top-level `notes.md`. Rules can target `notes.md` explicitly via the rule's `target` field when they care about the run-wide user-facing summary.

Rules are expressed as simple predicates. Two common ones:

- `"Decision section contains X or Y"` — regex match on the text under the `## Decision` heading.
- `"Rationale cites ≥N turn numbers"` — count `T\d+` patterns in the `## Rationale` section.

A fixture passes shape iff all rules pass. Record as `verdict_shape_pass: bool`. Also record which rules failed, for the report.

### 4. Timing and tokens

Sum turn durations and token usage from `transcript.jsonl`. Round wall-clock to whole seconds; tokens to integer.

## Writing the scorecard line

Append one JSON object to `.evals/scorecard.jsonl` matching the schema in `SKILL.md`. Never overwrite prior lines.

## Regression detection

When producing a report across multiple runs of the same fixture:

- For each CLI in each format, compute first-try rate = `first_try / attempts`.
- Compare the latest rate to the median of the previous 5 runs.
- Flag regression if the latest is ≥10 percentage points below the median AND attempts ≥ 3 (enough signal).

Do not flag improvements as regressions. Do not flag anything with fewer than 3 attempts.

## What scoring does NOT judge

- The *correctness* of the verdict. An eval harness cannot tell whether the parliament was right about the migration; only the user can.
- Style, tone, or prose quality.
- Which model "won" the debate.

Scoring is about **process compliance**, not argument quality. Argument quality is the user's call, informed by the verdict.

## Extending

When adding a new rule type to verdict-shape, edit this file. Rule types should be:

1. Mechanically checkable (regex, count, parseable JSON).
2. Stable across LLM non-determinism (a reasonable model should pass or fail the same way 9/10 times).
3. Focused on structural claims, not content claims.
