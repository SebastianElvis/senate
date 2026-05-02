# Format selection — decision tree

When the user did not specify a primitive (and preset, where applicable), the planner picks. Walk the tree below in order; first match wins. Surface the rationale in the agenda's `## Why this format` section.

This file is the planner-side complement to `../formats/README.md`. The library is organized around **5 primitives**, several of which are closed families with named **presets**.

## Decision tree (primary)

### 1. Reviewing a prior court verdict?

**→ court / preset `appeals-court`.** Triggers: reference to a prior `run_id`, "second opinion on that ruling", "was that decided correctly".

### 2. Single specific claim being stress-tested?

**→ court / preset `socratic`.** Triggers: "is X really true", "test this claim", "is this reasoning sound", "debug this line of thought".

### 3. Security / reliability / failure-mode review?

**→ court / preset `red-team`.** Triggers: "attack", "find failure modes", "is this safe", "pre-mortem", "what breaks", "security review", "threat model".

### 4. Decision with a clear for/against, especially adversarial?

**→ court / preset `court`.** Triggers: "is my refactor safe", "should we merge this", "review this PR adversarially", "prosecute / defend".

### 5. "What do we need to know" rather than "what should we do"?

**→ panel / preset `oracle`.** Triggers: "what should we know about", "what are the considerations", "survey the terrain", "what does expert X think about".

### 6. Reviewing a design doc or spec produced by someone else?

**→ panel / preset `peer-review`** (default for ≤ 4 reviewers) **or panel / preset `rfc`** (≥ 5 contributors, async, paragraph-anchored). Triggers for peer-review: "review this design doc", "critique this spec", "evaluate this proposal". Triggers for rfc: roster size ≥ 5, "distributed review", "async comments", "get feedback from a lot of people", a draft that wants paragraph-level annotation.

### 7. Deliverable is a document (memo, ADR, position paper, brief)?

**→ workshop / preset `committee`.** Triggers: "write a memo", "draft an ADR", "position paper", "brief the team on".

### 8. Converging on a shared plan / design / spec (small group, peer-egalitarian)?

**→ workshop / preset `consensus`.** Triggers: "agree on a design", "design an API together", "converge on a plan", "produce a spec we all accept".

### 9. Ideation / early exploration / "give me options"?

**→ brainstorm.** Triggers: "brainstorm", "give me ideas", "explore options", "what could we do about".

### 10. Open question, diverse perspectives wanted, no single right answer?

**→ parliament** (default for ambiguous decision-shaped tasks). Triggers: "should we", "is it a good idea", "debate this", "what do you think", or nothing specific.

## Primitive summary (for the rationale paragraph)

One-line reminders. Use these when writing `## Why this format`.

| Primitive | Optimizes for |
| --- | --- |
| parliament | Diversity of perspective, surfacing dissent via vote tally |
| court | Adversarial argument resolved by an arbiter (umbrella for court / appeals-court / red-team / socratic) |
| panel | Independent isolated judgments combined by a non-participating synthesizer (umbrella for oracle / peer-review / rfc) |
| workshop | Iterative co-authorship of a shared deliverable (umbrella for committee / consensus) |
| brainstorm | Breadth of options, optionality preserved |

## Choosing the preset (within a primitive)

Once the primitive is chosen, the preset follows from the task shape:

- **court**:
  - input is a prior verdict → `appeals-court`
  - the task is "test this single claim" → `socratic`
  - the task is "what breaks" / failure modes → `red-team`
  - else → `court`
- **panel**:
  - input is a question (no draft) → `oracle`
  - input is a draft and roster ≤ 4 → `peer-review`
  - input is a draft and roster ≥ 5 (or paragraph-anchored annotations are useful) → `rfc`
- **workshop**:
  - one coherent voice / clear ownership / organizational document → `committee`
  - multiple genuine perspectives that must converge without one dominating → `consensus`

## Multi-stage hint

If the user's task contains **two distinct questions** ("first decide X, then design Y") or **explicit pipeline language** ("draft → review → revise"), don't pick a single primitive — switch to multi-stage planning per `stages.md`. The shipped pipelines reference primitives + presets directly:

- `rfc-pipeline` = workshop:committee → panel:rfc → workshop:committee
- `design-review` = panel:oracle → workshop:committee → (panel:peer-review ‖ court:red-team) → workshop:committee
- `bill-to-law` = workshop:committee → panel:rfc → parliament → workshop:committee
- `incident-post-mortem` = panel:oracle → court:red-team → workshop:committee

## Edge cases

- **User task is a request for one model's answer** (e.g., "explain X") → senate is the wrong skill. Tell the user to call the CLI directly.
- **User specifies a roster that doesn't fit the recommendation** (e.g., asks for `red-team` with 1 attacker vs. recommended 2–3) → recommend the primitive + preset but note the roster concern in `## Open questions`.
- **None of rules 1–10 fit cleanly** → ask one clarifying question per `clarification.md`. Don't guess for a task you don't understand.
