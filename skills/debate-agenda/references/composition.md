# Composition — roles filled by sub-debates

Most formats assume each role is filled by exactly one CLI. Some tasks benefit from richer roles: a jury composed of multiple agents reaching consensus; a committee member that is itself a mini-panel; an oracle synthesizer that runs a sub-consensus.

This file is how the planner expresses composition. The agenda may declare that a role is filled not by a single CLI but by a **sub-debate** whose verdict becomes that role's contribution.

This used to live in the `invoke-format` skill. It is now part of agenda planning because composition is a planning decision: who plays which role, and at what level of aggregation. The moderator simply runs whatever the agenda specifies.

## When to compose

Good reasons:

- **A role is high-stakes** and a single CLI's output is too brittle (e.g., the judge in a court).
- **Domain breadth required** in a single role (e.g., the synthesizer of an oracle, where you want consensus across several models).
- **Robustness via ensemble**: compute the role's output as a small consensus rather than one shot.

Bad reasons:

- **"More agents = better."** Composition multiplies cost; use it where it materially raises output quality.
- **Hiding indecision.** If you can't pick which CLI to use, that's a planner problem, not a composition problem.

## Composed-role schema

In the agenda's `composition` array on a stage:

```yaml
composition:
  - role: jury
    format: consensus
    roster:
      - { role: contributor, cli: codex }
      - { role: contributor, cli: gemini }
      - { role: contributor, cli: kimi }
      - { role: arbiter, cli: claude }
    rounds: 2
    budget_multiplier: 0.4
```

The parent stage's `roster` does **not** list the composed role with a `cli` field; instead, the role appears in `composition` with its own format and roster.

The `budget_multiplier` is a fraction of the parent stage's remaining budget that this sub-debate may consume (defaults: 0.4 for wall-clock, 0.3 for tokens — see `../../moderate-debate/references/budget.md`).

## How the moderator uses this

When the parent stage reaches a turn for a composed role:

1. **Mint a sub-run dir** inside the parent run:
   ```
   .senate/runs/<parent-id>/sub/<role>-<phase>-<turn>/
   ```
   The sub-run gets its own agenda.md, transcript.jsonl, context.md, and verdict.md — same layout as a top-level run.

2. **Construct the sub-task prompt.** The framing wrapper says:
   > You are running a sub-debate to fill the role of `{role}` in the parent {parent_format}. The parent is debating: {parent_task}. Your job is to produce a single response for this turn: {parent_turn_prompt}. The verdict of your {child_format} will be treated as if a single participant produced it.

3. **Run the child format** through `moderate-debate` recursively, using the sub-agenda. Same loop, one level deeper.

4. **Extract the child's verdict** as the parent's turn content. The full child transcript stays on disk but is **not pasted into the parent's transcript** — only the verdict text. This matches human norms (a jury's deliberations are private; only the verdict is public).

5. **Record the composition** in the parent's `transcript.jsonl` per the canonical schema in `../../senate/references/workspace.md` (`## transcript.jsonl schema`). Composed-role turns set `cli` to `compose:<child-format>` and populate `sub_run_id` with the sub-run's directory name:
   ```json
   {
     "turn": 3,
     "stage": 1,
     "role": "jury",
     "cli": "compose:consensus",
     "sub_run_id": "<parent-id>.sub.jury-verdict-1",
     "text": "{child verdict text}",
     "completion_tokens": 18432
   }
   ```

## Privacy

Other roles in the parent format see only the child's **verdict text**, never the child's internal debate. Exception: the parent's judge / synthesizer / editor role may request the full sub-transcript during the synthesis phase — record this in the parent transcript as `"action": "read_sub_transcript"`.

## Failure handling

If the sub-debate fails (budget exhausted, all contributors failed contracts, etc.):

- The sub-run writes whatever partial `verdict.md` it has, with the disposition flagged.
- The parent stage treats this as a failed turn for the composed role: apply the parent format's fallback rule (often: abstain / forfeit / reuse previous turn).
- **Never block the parent on a sub-debate failure.**

## Nesting depth

For now: only **one level of composition**. A sub-debate may not itself contain composed roles. This keeps budgets bounded and replay tractable.

(Deeper nesting is a later horizon — explicit depth limit will land alongside it.)

## Canonical compositions

These are not separate format files — they are recipes the planner recognizes when users name them:

| Recipe | Parent format | Composed role | Child format |
| --- | --- | --- | --- |
| `court-with-jury-consensus` | court | `judge` → `jury` (panel) | consensus (3 contributors + arbiter) |
| `parliament-with-committee-parties` | parliament | each `mp_*` | committee (3 members + editor) |
| `oracle-with-consensus-synthesis` | oracle | `synthesizer` | consensus (2 contributors + arbiter) |

If the user asks for a recipe by name, expand it into the agenda's `composition` array per the table.

## Relation to multi-stage

Composition is **within a single stage's turn**: a role's output is itself the output of a sub-debate. Multi-stage agendas (`stages.md`) chain different debates **sequentially**: each stage produces a verdict that the next stage consumes. Both are forms of composition; they live at different scales.

A single agenda can use both: a stage may have composed roles, and an agenda may have many stages.
