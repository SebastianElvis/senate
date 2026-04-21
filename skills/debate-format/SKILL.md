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
| committee | `committee.md` | Small group drafts a document | Memos, ADRs, position papers — where the deliverable is the prose |
| peer-review | `peer-review.md` | Author / blind reviewers / editor | Design docs, specs — structured independent critique |
| brainstorm | `brainstorm.md` | Diverge then converge | Early ideation, naming, API exploration — produces options, not decisions |
| oracle | `oracle.md` | Questioner / independent experts / synthesizer | "What do we need to know before deciding X?" |
| socratic | `socratic.md` | One interviewer, one subject, narrow probes | Stress-testing a single claim or reasoning chain |
| appeals-court | `appeals-court.md` | Re-review of a prior court verdict | Second opinion on a controversial ruling |
| rfc | `rfc.md` | Author / parallel commenters / editor | Asynchronous distributed review at scale (≥ 5 participants) |
| red-team | `red-team.md` | Attackers / defender / judge | Security, reliability, pre-mortems — finding failure modes |

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

If the user didn't specify one, consult `../format-selector/` or pick directly using this heuristic:

| User says... | Format |
| --- | --- |
| "Should we do X?" / "Is Y a good idea?" | **parliament** |
| "Is my refactor safe?" / "Review this adversarially" | **court** |
| "Help us agree on a design for Z" | **consensus** |
| "Draft a memo / ADR / position paper" | **committee** |
| "Review this design doc / spec" | **peer-review** |
| "Give me ideas for X" / "Brainstorm Y" | **brainstorm** |
| "What do we need to know about X?" | **oracle** |
| "Test this claim" / "Is X really true?" | **socratic** |
| "Get a second opinion on the court verdict in run Z" | **appeals-court** |
| "Distribute this spec for async comments" | **rfc** |
| "Attack this plan" / "Find failure modes in X" | **red-team** |

If none fits cleanly, ask the user.

## Adding a format

Copy `_template.md` to `<name>.md`, fill in all six sections, and add a row to the table above.

## Files in this skill

- `parliament.md`, `court.md`, `consensus.md` — H0 formats.
- `committee.md`, `peer-review.md`, `brainstorm.md`, `oracle.md`, `socratic.md`, `appeals-court.md`, `rfc.md`, `red-team.md` — H2 formats.
- `_template.md` — starter for new formats.

## Related skills

- `../invoke-format/` — composition primitive: one format calls another as a sub-debate.
- `../format-selector/` — recommends a format given a task description.
- `../workflow/` — chains multiple formats into multi-stage pipelines.
