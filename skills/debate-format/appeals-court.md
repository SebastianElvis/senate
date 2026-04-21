# appeals-court

## Summary

Re-examines a prior `court` verdict with a **different** roster, looking specifically for errors in the original ruling. Does not re-litigate the underlying facts from scratch — reviews the original transcript and asks whether the judge got it right. Best for:

- surfacing whether a past debate was decided on shaky reasoning,
- catching cases where a single judge's idiosyncrasy dominated,
- producing a "second opinion" on a controversial verdict.

Takes a prior `run_id` as input; does not generate its own task.

## Roles

| Role | Brief |
| --- | --- |
| `appellant` | Argues the original ruling was wrong. Typically takes the losing side's position from the original court. |
| `respondent` | Argues the original ruling was right. Typically takes the winning side's position. |
| `appeals_judge` | Rules on the appeal. Does NOT re-rule on the underlying case. Only answers: did the original ruling stand on sound reasoning? |

Minimum: 3. Appeals courts do not have juries or witnesses.

**Roster constraint**: at least the `appeals_judge` must be a different CLI than the original `judge`. If feasible, all three roles should use different CLIs than the original court.

## Phases

### 1. Case review — **sequential**, single turn

Role: `appeals_judge`.

Prompt:

```
You are an appeals judge. A prior court has ruled on this task:

{original_task}

The original roster was:
{original_roster}

The original ruling was:

{original_verdict}

Read the original transcript (below) and produce a neutral case summary in 200–400 words. Identify:
- the core question the court answered,
- the original ruling's disposition (sustain / dismiss / remand),
- the reasoning the original judge cited.

Do NOT opine on whether the original was correct. That comes after the appeal.

{transcript_slice: original full transcript}
```

Output contract: free text.

### 2. Appeal — **sequential**, single turn

Role: `appellant`.

Prompt:

```
You are the appellant. The original ruling went against your position. Case summary:

{case_summary}

Argue the ruling was in error in 300–500 words. You may argue:
- **Factual error** — the judge misread the evidence (cite specific original turn numbers).
- **Procedural error** — the judge relied on a point neither side actually argued.
- **Reasoning error** — the judge's stated rationale does not actually support the disposition.
- **Missing consideration** — a decisive point was raised but not addressed in the ruling.

Do NOT introduce new arguments that could have been raised at trial. Appeal is limited to errors in the prior proceeding.
```

Output contract: free text, must name at least one specific error class above.

### 3. Response — **sequential**, single turn

Role: `respondent`.

Prompt:

```
You are the respondent. The appellant's claim of error is below.

{appeal turn}

Respond in 300–500 words. For each alleged error, defend the original ruling or concede. You may cite the original transcript's turn numbers to support your defense.
```

Output contract: free text.

### 4. Appellate ruling — **sequential**, single turn

Role: `appeals_judge`.

Prompt:

```
You are the appeals judge. The appeal, response, and original case are all before you.

{transcript_slice: full appeal}

Rule on the appeal. Produce a markdown document:

- **Original ruling** — restated one line.
- **Appeal disposition** — one of:
  - `affirmed` — the original ruling stands; appellant's claims of error are insufficient.
  - `reversed` — the original ruling was in error; the appeal prevails.
  - `remanded` — the original proceeding was flawed enough that the case should be re-heard (trigger a new `court` run).
- **Reasoning** — weigh each alleged error; cite the original and appeal turn numbers.
- **Scope of ruling** — what this disposition does and does NOT establish about the underlying question.
```

Output contract: markdown + trailing fenced json:

```json
{"disposition": "affirmed" | "reversed" | "remanded", "confidence": 0.0-1.0}
```

On contract failure, fallback to `affirmed` (default toward status quo) with confidence 0.3.

## Termination

- After phase 4.
- On `remanded`, orchestrator may offer the user to run a fresh `court` on the original task.

## Defaults

- **Rounds**: 1 (no cross-appeal). Unlike court, appeals has no cross-examination phase.
- **Roster size**: exactly 3.
- **Agent failure**: if the appellant cannot complete their turn, the appeal is dismissed as abandoned.
- **Output of this format is narrower** than court — appeal verdicts do not rule on the underlying question, only on the original ruling's validity.

## Inputs

Orchestrator needs:

- `original_run_id` — the prior court run.
- A roster that differs from the original per the constraint above.

If the user invokes appeals-court without naming a prior run, ask them which run to appeal.
