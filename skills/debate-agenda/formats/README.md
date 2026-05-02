# Format playbook library

A reference library, not a skill. The `debate-agenda` planner picks primitive playbooks from this directory and expands them into a concrete `agenda.md`; the `moderate-debate` runner reads each stage's primitive file (and its preset) to drive its turns.

Only runtime primitive files live here:

- **Single-stage primitives** — five files, each owning one interaction-contract axis. Some primitives are closed families with named **presets** (e.g., `court` has presets `court`, `appeals-court`, `red-team`, `socratic`). The agenda specifies `format: <primitive>` plus `preset: <name>`.
- **Pipeline recipes** are not separate format files. They are named stage sequences in `../references/stages.md`, and each stage points back to one of the five primitive files here.

## The five primitives

| Primitive | File | Owns this axis | Presets |
| --- | --- | --- | --- |
| **parliament** | `parliament.md` | Collective decision by aggregation (vote tally with recorded dissent). | (none) |
| **court** | `court.md` | Adversarial argument resolved by an arbiter. | `court`, `appeals-court`, `red-team`, `socratic` |
| **panel** | `panel.md` | Independent isolated judgments combined by a non-participating synthesizer. | `oracle`, `peer-review`, `rfc` |
| **workshop** | `workshop.md` | Iterative co-authorship of a shared draft by peers. | `committee`, `consensus` |
| **brainstorm** | `brainstorm.md` | Divergent generation under a no-criticism rule, then convergent selection (options, not decisions). | (none) |

Each primitive owns exactly one interaction-contract axis. The presets within a primitive are configuration of that contract — not co-equal new primitives. **Closed families: arbitrary parameter combinations are undefined — pick a named preset.**

New primitives should follow the common schema below. Add one only when the new file owns an interaction-contract axis that none of the five primitives owns.

### Preset cheatsheet

| Preset | Lives under | Replaces the old format | Best for |
| --- | --- | --- | --- |
| `court` | court | court | Decisions with a clear for/against, adversarial review |
| `appeals-court` | court | appeals-court | Second opinion on a controversial ruling |
| `red-team` | court | red-team | Security, reliability, pre-mortems — finding failure modes |
| `socratic` | court | socratic | Stress-testing a single claim or reasoning chain |
| `oracle` | panel | oracle | "What do we need to know before deciding X?" |
| `peer-review` | panel | peer-review | Structured independent critique of a submission |
| `rfc` | panel | rfc | Asynchronous distributed review at scale (≥ 5 contributors) |
| `committee` | workshop | committee | Memos, ADRs, position papers — a single coherent voice matters |
| `consensus` | workshop | consensus | Multiple genuine perspectives must converge without one dominating |

## Multi-stage pipeline recipes

| Pipeline | Stage sequence | Best for |
| --- | --- | --- |
| rfc-pipeline | workshop:committee → panel:rfc → workshop:committee | Drafting a spec, distributed comment, finalize |
| design-review | panel:oracle → workshop:committee → (panel:peer-review ‖ court:red-team) → workshop:committee | Technical designs needing breadth + adversarial pressure |
| bill-to-law | workshop:committee → panel:rfc → parliament → workshop:committee | Policy-shaped decisions with many stakeholders |
| incident-post-mortem | panel:oracle → court:red-team → workshop:committee | Blameless post-mortem: reconstruct → root cause → remediate |

The concrete stage lists, bindings, checkpoints, defaults, and verdict shapes live in `../references/stages.md`.

## Common schema (single-stage primitives)

Every primitive file documents these sections in order:

1. **Defining commitment** — the load-bearing invariant that makes this a primitive.
2. **Boundary conditions** — invariants the runtime enforces.
3. **Anti-drift fence** — a table mapping adjacent shapes to other primitives.
4. **Presets** (if a closed family) — table + per-preset section, each containing:
   1. **Roles** — named slots, each with a short brief.
   2. **Phases** — ordered list. Each phase declares parallel/sequential, which roles speak, prompt template, output contract.
   3. **Termination** — when the debate ends.
   4. **Synthesis** — which role produces the synthesis content.
   5. **Defaults** — recommended rounds, roster size limits, fallback behavior.

## Common schema (multi-stage pipeline recipes)

Every pipeline recipe in `../references/stages.md` declares:

- When to choose the recipe.
- Default roster and budget.
- Expanded stage shape: format, preset if applicable, roster, bindings, checkpoint.
- Failure modes and verdict shape.

## Picking a primitive

If the user didn't specify, the planner walks the decision tree in `../references/format-selection.md`. Quick heuristic:

| User says... | Pick |
| --- | --- |
| "Should we do X?" / "Is Y a good idea?" | **parliament** |
| "Is my refactor safe?" / "Review this adversarially" | **court** (preset: court) |
| "Get a second opinion on the verdict in run Z" | **court** (preset: appeals-court) |
| "Attack this plan" / "Find failure modes" / "Pre-mortem" | **court** (preset: red-team) |
| "Is X really true?" / "Test this reasoning" | **court** (preset: socratic) |
| "What do we need to know about X?" | **panel** (preset: oracle) |
| "Review this design doc / spec" | **panel** (preset: peer-review) |
| "Distribute this spec for async comments" | **panel** (preset: rfc) |
| "Draft a memo / ADR / position paper" | **workshop** (preset: committee) |
| "Help us agree on a design for Z" | **workshop** (preset: consensus) |
| "Give me ideas for X" / "Brainstorm Y" | **brainstorm** |
| "Draft, then comment, then finalize" | **rfc-pipeline** |
| "Design something carefully with reviews" | **design-review** |
| "Decide a policy with public input and a vote" | **bill-to-law** |
| "Run a blameless post-mortem on this incident" | **incident-post-mortem** |

If none fits cleanly, ask the user.

## Adding a new entry

- **New preset** under an existing primitive: open the primitive's file, add a row to its preset table, append a preset section. Verify the parameters are contract-defining (different prompts, turn rules, output schemas) — not decorative.
- **New primitive:** create `<name>.md`, fill in the common primitive sections, and add a row to the primitives table above. The new primitive must own an axis no existing primitive owns.
- **New pipeline recipe:** add it to `../references/stages.md`, then add a row to the pipeline recipe table above.

## Related skills

- `..` (parent: `debate-agenda`) — reads files here when planning an agenda.
- `../../moderate-debate/` — reads primitive files when running each stage; consults the active preset.
- `../../meeting-note/` — writes the verdict and meeting notes after the moderator finishes.
- `../../senate/` — top-level orchestrator that chains the three above.
