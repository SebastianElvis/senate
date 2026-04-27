# Format playbook library

A reference library, not a skill. The `debate-agenda` planner picks one of these and expands it into a concrete `agenda.md`; the `moderate-debate` runner reads each stage's underlying primitive format file to drive its turns.

Two kinds of files live here:

- **Single-stage primitives** — one debate, defining roles / phases / contracts / termination. No frontmatter; the markdown body is the spec.
- **Multi-stage pipelines** — a sequence of stages, each pointing at a single-stage primitive, with bindings between them. YAML frontmatter declares `mode: pipeline`.

## Single-stage primitives

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

Template for a new primitive: `_template.md`.

## Multi-stage pipelines

| Pipeline | File | Stage sequence | Best for |
| --- | --- | --- | --- |
| rfc-pipeline | `rfc-pipeline.md` | committee → rfc → committee | Drafting a spec, distributed comment, finalize |
| design-review | `design-review.md` | oracle → committee → (peer-review ‖ red-team) → committee | Technical designs needing breadth + adversarial pressure |
| bill-to-law | `bill-to-law.md` | committee → rfc → parliament → committee | Policy-shaped decisions with many stakeholders |
| incident-post-mortem | `incident-post-mortem.md` | oracle → red-team → committee | Blameless post-mortem: reconstruct → root cause → remediate |

Each pipeline file declares `mode: pipeline` in frontmatter, plus stages, bindings, checkpoints, and a default roster.

## Common schema (single-stage primitives)

Every primitive format file documents these sections in order:

1. **Summary** — one paragraph on when to pick this format.
2. **Roles** — named slots, each with a short brief. The planner maps CLIs from the roster to roles.
3. **Phases** — ordered list. Each phase declares:
   - sequential or parallel,
   - which roles speak,
   - what prompt each role gets (role brief + transcript slice + turn instruction),
   - the output contract for that turn.
4. **Termination** — when the debate ends (fixed rounds, convergence check, judge ruling).
5. **Synthesis** — which role produces the synthesis content (the basis of `verdict.md`) and the prompt template for it. The moderator writes the synthesis to `stages/<N>/verdict.md` in multi-stage runs; `meeting-note` writes the canonical top-level `verdict.md` after the run.
6. **Defaults** — recommended rounds, minimum / maximum roster size, fallback behavior on agent failure.

## Common schema (multi-stage pipelines)

Every pipeline file declares:

- `name`, `description`, `mode: pipeline`, `default_roster`, `default_budget` in frontmatter.
- A "Why this pipeline" prose section.
- An "Expanded shape" YAML block listing each stage (format, roster, bindings, checkpoint).
- Failure modes and verdict shape sections.

## Picking a format

If the user didn't specify one, the planner walks the decision tree in `../references/format-selection.md`. As a quick heuristic for callers reading this file directly:

| User says... | Pick |
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
| "Draft, then comment, then finalize" | **rfc-pipeline** |
| "Design something carefully with reviews" | **design-review** |
| "Decide a policy with public input and a vote" | **bill-to-law** |
| "Run a blameless post-mortem on this incident" | **incident-post-mortem** |

If none fits cleanly, ask the user.

## Adding a new entry

- **New primitive:** copy `_template.md` to `<name>.md`, fill in the six sections, and add a row to the primitives table above.
- **New pipeline:** copy any of the four shipped pipelines (`rfc-pipeline.md` is the smallest), edit stages and bindings, and add a row to the pipelines table above.

## Related skills

- `..` (parent: `debate-agenda`) — reads files here when planning an agenda.
- `../../moderate-debate/` — reads single-stage primitive files when running each stage.
- `../../meeting-note/` — writes the verdict and meeting notes after the moderator finishes.
- `../../senate/` — top-level orchestrator that chains the three above.
