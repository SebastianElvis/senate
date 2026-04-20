---
name: debate-format
description: Playbook library for multi-agent debate formats (parliament, court, consensus, and custom). Use when the senate skill needs to know the roles, turn order, parallel vs sequential phases, termination condition, and output contract for a chosen format.
---

# debate-format — format playbook library

This skill is a **reference library**, not a flow. When `senate` (or any orchestrator) needs to run a debate, read the relevant file below for the full format spec.

## Supported formats

| Format | File | Shape | Best for |
| --- | --- | --- | --- |
| parliament | `parliament.md` | Multi-party, voting | Open questions, design choices, "should we do X?" |
| court | `court.md` | Prosecution vs. defense, judge ruling | Decisions with a clear for/against, adversarial review |
| consensus | `consensus.md` | Iterate until agreement or N rounds | Converging on a plan, API design, spec |

Template for new formats: `_template.md`.

## Common schema

Every format file documents these sections in order:

1. **Summary** — one paragraph on when to pick this format.
2. **Roles** — named slots, each with a short brief. Orchestrator maps CLIs from the roster to roles.
3. **Phases** — ordered list. Each phase declares:
   - sequential or parallel,
   - which roles speak,
   - what prompt each role gets (role brief + transcript slice + turn instruction),
   - the output contract for that turn.
4. **Termination** — when the debate ends (fixed rounds, convergence check, judge ruling).
5. **Synthesis** — which role produces `verdict.md` and the prompt template for it.
6. **Defaults** — recommended rounds, minimum / maximum roster size, fallback behavior on agent failure.

## Picking a format

If the user didn't specify one:

- "Should we do X?" / "Is Y a good idea?" → **parliament**.
- "Is my refactor safe?" / "Review this PR adversarially" → **court**.
- "Help us agree on a design for Z" → **consensus**.

If none fits cleanly, ask the user.

## Adding a format

Copy `_template.md` to `<name>.md`, fill in all six sections, and add a row to the table above.

## Files in this skill

- `parliament.md`
- `court.md`
- `consensus.md`
- `_template.md`
