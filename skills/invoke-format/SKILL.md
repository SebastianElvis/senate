---
name: invoke-format
description: Composition primitive for debate formats. Runs one format as a sub-debate whose verdict feeds into a parent format's role. Use when a format's role needs to be filled not by a single CLI but by the collective output of another debate (e.g., a court where the jury is itself a 3-agent consensus, or a parliament where one MP is itself a sub-committee).
---

# invoke-format — format composition

Most formats assume each role is filled by exactly one CLI. Some tasks benefit from richer roles: a jury composed of multiple agents reaching consensus; a committee member who is itself a mini-panel. `invoke-format` is the primitive that makes this work: a role can be filled by a sub-debate instead of a CLI.

This is the plumbing that (later, in H4) enables arbitrary nested hierarchies. At H2, it enables simple one-level composition, which is enough for the common cases.

## When to trigger

Invoked **only from within another format's execution**, not directly by the user. If the orchestrator, while running format F, encounters a role slot whose `cli` field is a format invocation (`{"format": "consensus", "roster": [...]}` instead of `{"cli": "codex"}`), it calls this skill.

Users typically opt in by:

- Asking for it explicitly: *"run a court where the jury is a 3-way consensus of codex, gemini, kimi"*.
- Using a pre-baked composed format (coming in H4).

## Role invocation shape

In a parent format's `roster.json`, a composed role looks like:

```json
{
  "role": "jury",
  "filled_by": {
    "format": "consensus",
    "roster": [
      {"role": "contributor", "cli": "codex"},
      {"role": "contributor", "cli": "gemini"},
      {"role": "contributor", "cli": "kimi"},
      {"role": "arbiter", "cli": "claude"}
    ],
    "max_rounds": 2
  }
}
```

## How invocation works

When the parent format reaches a turn for a composed role:

1. **Mint a sub-run directory** inside the parent run:
   ```
   .senate/runs/<parent-id>/sub/<child-id>/
   ```
   `<child-id>` = `<parent-id>.sub.<role-name>.<phase-name>.<turn-num>` (deterministic, enables replay).

2. **Construct the sub-task prompt.** Combine the parent's turn prompt with a framing wrapper:
   ```
   You are running a sub-debate to fill the role of "{role}" in a parent {parent_format}.

   The parent is answering: {parent_task}

   Your job is to produce a response for this specific turn: {parent_turn_prompt}

   Run your {child_format} process and produce the final verdict. The verdict will be treated as if a single participant with the expertise of your collective produced it.
   ```

3. **Run the child format normally.** Same orchestration flow as a top-level run. All `.senate/runs/<parent-id>/sub/<child-id>/` artifacts are written exactly as for a regular run.

4. **Extract the child's verdict** as the parent's turn content. The full child transcript is on disk but is **not** pasted into the parent's transcript — only the verdict text.

5. **Record the composition** in the parent's `transcript.jsonl`:
   ```json
   {
     "turn": 3,
     "role": "jury",
     "cli": "invoke-format:consensus",
     "sub_run_id": "2026-04-20-1432-court.sub.jury.verdict.1",
     "text": "{child verdict text}",
     "tokens": 18432
   }
   ```

## Budget propagation

Sub-debates inherit a fraction of the parent's remaining budget per `../senate/BUDGET.md`:

- `sub_wall_clock = parent_remaining_wall_clock * 0.4`
- `sub_tokens = parent_remaining_tokens * 0.3`

Overridable per composed role (`"budget_multiplier": 0.5`) if the parent knows this role is expensive.

## Privacy

The child's transcript is **opaque to the parent's peer roles**. Other roles in the parent format see only the child's verdict text, never the child's internal debate. This matches human norms (a jury's deliberations are private; only the verdict is visible).

Exception: the parent's judge / synthesizer / editor role may request the full sub-transcript during the synthesis phase — record this in the parent transcript as `"action": "read_sub_transcript"`.

## Failure handling

If the sub-debate fails (budget exhausted, all contributors failed contracts, etc.):

- The sub-run writes whatever partial `verdict.md` it has with `disposition: stalled`.
- The parent format treats this as a failed turn for the composed role: apply the parent format's fallback rule (often: abstain / forfeit / reuse previous turn).
- Never block the parent run on a sub-debate failure.

## Nesting depth

At H2, only **one level of composition** is supported. A sub-debate may not itself contain composed roles.

H4 lifts this restriction: nested composition with explicit depth limit (default 3, max 5). Depth ≥ 5 produces budget explosions and diminishing returns.

## Canonical compositions (provided)

These are not separate format files — they are recipes the orchestrator recognizes when users name them:

| Recipe | Parent format | Composed role | Child format |
| --- | --- | --- | --- |
| `court-with-jury-consensus` | court | `judge` → `jury` (panel) | consensus (3 contributors + arbiter) |
| `parliament-with-committee-parties` | parliament | each `mp_*` | committee (3 members + editor) |
| `oracle-with-consensus-synthesis` | oracle | `synthesizer` | consensus (2 contributors + arbiter) |

## Files in this skill

- `SKILL.md` — this file. Composition is a thin wrapper; it doesn't need more.

## Relation to workflow (H3)

`invoke-format` runs a sub-debate **within** a single format's turn. `workflow` (H3) runs multiple formats **sequentially** as a pipeline. Both are composition, but at different scales. A workflow stage may use a composed format via `invoke-format`.
