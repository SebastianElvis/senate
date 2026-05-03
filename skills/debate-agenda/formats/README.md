# Format playbook library

A reference library, not a skill. The `debate-agenda` planner picks a format from this directory and expands it into a concrete `agenda.md`; the `moderate-debate` runner reads each stage's format file to drive its turns.

Only runtime format files live here. Each is a flat primitive — there are no presets, no closed families. The agenda specifies `format: <name>`.

Multi-stage pipelines are not separate format files. They are named stage sequences in `../references/stages.md`, and each stage points back to one of the format files here.

## The six formats

| Format | File | Owns this axis |
| --- | --- | --- |
| **parliament** | `parliament.md` | Collective decision by aggregation (vote tally with recorded dissent). |
| **court** | `court.md` | Adversarial argument resolved by an arbiter (one prosecution, one defense, one judge). |
| **red-team** | `red-team.md` | Asymmetric failure-mode hunt (N parallel attackers, one defender, one judge). |
| **peer-review** | `peer-review.md` | Independent isolated reviewer judgments combined by a non-participating editor. |
| **committee** | `committee.md` | Iterative co-authorship of a shared draft, editor-led, closed by a member vote. |
| **brainstorm** | `brainstorm.md` | Divergent generation under a no-criticism rule, then convergent selection (options, not decisions). |

Each format documents these sections in order:

1. **Defining commitment** — the load-bearing invariant that makes this a primitive.
2. **Boundary conditions** — invariants the runtime enforces.
3. **Anti-drift fence** — a table mapping adjacent shapes to other formats.
4. **Roles** — named slots, each with a short brief.
5. **Phases** — ordered list. Each phase declares parallel/sequential, which roles speak, prompt template, output contract.
6. **Termination** — when the debate ends.
7. **Defaults** — recommended rounds, roster size limits, fallback behavior.

Synthesis is named per-format (speaker / judge / editor), and that role's reply becomes the stage's verdict. The moderator writes the synthesis content to `stages/<N>-<name>/verdict.md` (the bindings target); the scribe (`meeting-note`) folds it into the run-wide `notes.md` after the run.

## Multi-stage pipeline recipes

| Pipeline | Stage sequence | Best for |
| --- | --- | --- |
| draft-review-finalize | committee → peer-review → committee | Drafting a spec, distributed review, finalize |
| design-review | committee → (peer-review ‖ red-team) → committee | Technical designs needing breadth + adversarial pressure |
| bill-to-law | committee → peer-review → parliament → committee | Policy-shaped decisions with many stakeholders |
| incident-post-mortem | red-team → committee | Blameless post-mortem: root cause → remediate |

The concrete stage lists, bindings, checkpoints, defaults, and verdict shapes live in `../references/stages.md`.

## Picking a format

If the user didn't specify, the planner walks the decision tree in `../references/format-selection.md`. Quick heuristic:

| User says... | Pick |
| --- | --- |
| "Should we do X?" / "Is Y a good idea?" | **parliament** |
| "Is my refactor safe?" / "Review this PR adversarially" | **court** |
| "Attack this plan" / "Find failure modes" / "Pre-mortem" | **red-team** |
| "Review this design doc / spec" | **peer-review** |
| "Draft a memo / ADR / position paper" / "Help us agree on a design for Z" | **committee** |
| "Give me ideas for X" / "Brainstorm Y" | **brainstorm** |
| "Draft, then comment, then finalize" | **draft-review-finalize** |
| "Design something carefully with reviews" | **design-review** |
| "Decide a policy with public input and a vote" | **bill-to-law** |
| "Run a blameless post-mortem on this incident" | **incident-post-mortem** |

If none fits cleanly, ask the user.

## Adding a new format

Create `<name>.md`, fill in the sections above, add a row to the formats table here. The new format must own an interaction-contract axis no existing format owns — different prompts, turn rules, output schemas, not just decoration.

For a new pipeline recipe: add it to `../references/stages.md`, then add a row to the pipeline table above.

## Related skills

- `..` (parent: `debate-agenda`) — reads files here when planning an agenda.
- `../../moderate-debate/` — reads the format file when running each stage.
- `../../meeting-note/` — writes the run-wide `notes.md` after the moderator finishes.
- `../../senate/` — top-level orchestrator that chains the three above.
