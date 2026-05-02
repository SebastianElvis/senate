# Format selection — decision tree

When the user did not specify a format, the planner picks. Walk the tree below in order; first match wins. Surface the rationale in the agenda's `## Why this format` section.

This file is the planner-side complement to `../formats/README.md`. The library is six flat formats — no presets, no closed families.

## Decision tree (primary)

### 1. Security / reliability / failure-mode review?

**→ red-team.** Triggers: "attack", "find failure modes", "is this safe", "pre-mortem", "what breaks", "security review", "threat model".

### 2. Decision with a clear for/against, especially adversarial?

**→ court.** Triggers: "is my refactor safe", "should we merge this", "review this PR adversarially", "prosecute / defend". For "second opinion on a prior court verdict", run a fresh `court` with the prior verdict pasted into the task and a different roster.

### 3. Reviewing a design doc, spec, or proposal produced by someone else?

**→ peer-review.** Triggers: "review this design doc", "critique this spec", "evaluate this proposal", "blind review", "RFC".

### 4. Deliverable is a document (memo, ADR, position paper, brief, agreed spec)?

**→ committee.** Triggers: "write a memo", "draft an ADR", "position paper", "brief the team on", "agree on a design", "produce a spec we all accept".

### 5. Ideation / early exploration / "give me options"?

**→ brainstorm.** Triggers: "brainstorm", "give me ideas", "explore options", "what could we do about".

### 6. Open question, diverse perspectives wanted, no single right answer?

**→ parliament** (default for ambiguous decision-shaped tasks). Triggers: "should we", "is it a good idea", "debate this", "what do you think", or nothing specific.

## Format summary (for the rationale paragraph)

One-line reminders. Use these when writing `## Why this format`.

| Format | Optimizes for |
| --- | --- |
| parliament | Diversity of perspective, surfacing dissent via vote tally |
| court | Adversarial argument resolved by an arbiter |
| red-team | Asymmetric failure-mode hunt — many attackers, one defender, judge rules |
| peer-review | Independent isolated reviewer judgments combined by a non-participating editor |
| committee | Iterative editor-led drafting of a shared deliverable |
| brainstorm | Breadth of options, optionality preserved |

## Multi-stage hint

If the user's task contains **two distinct questions** ("first decide X, then design Y") or **explicit pipeline language** ("draft → review → revise"), don't pick a single format — switch to multi-stage planning per `stages.md`. The shipped pipelines reference formats directly:

- `draft-review-finalize` = committee → peer-review → committee
- `design-review` = committee → (peer-review ‖ red-team) → committee
- `bill-to-law` = committee → peer-review → parliament → committee
- `incident-post-mortem` = red-team → committee

## Edge cases

- **User task is a request for one model's answer** (e.g., "explain X") → senate is the wrong skill. Tell the user to call the CLI directly.
- **User specifies a roster that doesn't fit the recommendation** (e.g., asks for `red-team` with 1 attacker vs. recommended 2–3) → recommend the format but note the roster concern in `## Open questions`.
- **None of rules 1–6 fit cleanly** → ask one clarifying question per `clarification.md`. Don't guess for a task you don't understand.
