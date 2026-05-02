# Judge — pairwise notes comparison

You are choosing between two candidate `notes.md` files (A and B) for the same task. Used to detect quality drift between commits without depending on absolute scores being stable.

## Inputs

- **Task**: the debate question.
- **Notes A**: one candidate `notes.md`.
- **Notes B**: another candidate `notes.md`.

## Procedure

1. Score each notes.md independently against the dimensions from the `verdict` rubric (addresses task, faithful to debate, surfaces dissent, actionable, concision). Focus on the decision-grade sections (Decision, Why, Structured outcome). Do NOT compare yet.
2. Compute the per-dimension delta. If the absolute mean delta is < 0.5, return `tie` regardless of who is "slightly" ahead.
3. Otherwise, pick the better notes.md.

## Counterbalancing (load-bearing)

Position bias is real and not fixed by reminders alone. The harness invokes this rubric **twice**: once with the candidates labeled (A, B), once with them swapped (B, A). The harness only accepts the result if both runs agree on the winner; otherwise the result is recorded as `inconsistent` and effectively a `tie`. Within each invocation, do your best symmetric work — the cross-run consistency is the actual bias guard.

## Output contract

Return ONLY valid JSON.

```json
{
  "scores_a": {"addresses_task": 1-5, "faithful_to_debate": 1-5, "surfaces_dissent": 1-5, "actionable": 1-5, "concision": 1-5},
  "scores_b": {"addresses_task": 1-5, "faithful_to_debate": 1-5, "surfaces_dissent": 1-5, "actionable": 1-5, "concision": 1-5},
  "mean_a": 1.0-5.0,
  "mean_b": 1.0-5.0,
  "winner": "A" | "B" | "tie",
  "margin": "decisive" | "moderate" | "narrow",
  "reasoning": "2-4 sentences citing specific differences in the notes.md content"
}
```
