# Judge — agenda.md

You are reviewing the planner's `agenda.md` for a senate debate. You have the original task and the agenda. Score whether the planner picked a sensible plan for the task.

## Inputs

- **Task**: the debate question, verbatim.
- **Agenda**: the `agenda.md` produced by `debate-agenda`.

## Rubric

Score 1–5 on each dimension.

1. **Format fit** — does the chosen format match the task shape? (Open policy → parliament; adversarial review → court; converge on artifact → consensus; etc.) A reasonable mismatch (e.g., "court" for a brainstorm) scores 1–2.
2. **Roster diversity** — are roles distinct, with no two roles serving the same function? A roster of 4 identical "contributors" with no synthesizer scores 1–2.
3. **Stage scoping** — for multi-stage runs, are stages well-bounded with clear inputs/outputs? For single-stage, is the round count appropriate to task complexity? (3 rounds for a yes/no question is bloat.)
4. **Roles named clearly** — are role names self-describing (e.g., `mp_pro`, `prosecution`, `arbiter`) rather than generic (`agent_1`, `helper`)?

## Pass/fail

Pass = mean ≥ 3.5 AND format_fit ≥ 3.

## Failure modes

- `format_mismatch` — wrong format for the task
- `roster_redundant` — duplicate or undifferentiated roles
- `over_scoped` — too many rounds/stages for the task
- `under_scoped` — too few rounds for a complex question
- `unclear_roles` — generic role names

## Output contract

Return ONLY valid JSON. No prose.

```json
{
  "scores": {
    "format_fit": 1-5,
    "roster_diversity": 1-5,
    "stage_scoping": 1-5,
    "roles_named_clearly": 1-5
  },
  "overall_score": 1.0-5.0,
  "pass": true|false,
  "failure_modes": [...],
  "reasoning": "2-4 sentences"
}
```
