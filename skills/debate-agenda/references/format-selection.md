# Format selection — decision tree

When the user did not specify a format, the planner picks one. This file is the decision tree. Walk it in order; first match wins. If multiple match, the **earlier** rule takes priority. Surface the rationale in the agenda's `## Why this format` section.

This is the logic that used to live in the standalone `format-selector` skill. It now lives here because format selection is part of agenda planning, not a separate concern.

## Decision tree

### 1. Security / reliability / failure-mode review?

**→ red-team.** Triggers: "attack", "find failure modes", "is this safe", "pre-mortem", "what breaks", "security review", "threat model".

### 2. Reviewing a prior court verdict?

**→ appeals-court.** Triggers: reference to a prior `run_id`, "second opinion on that ruling", "was that decided correctly".

### 3. Single specific claim being stress-tested?

**→ socratic.** Triggers: "is X really true", "test this claim", "is this reasoning sound", "debug this line of thought".

### 4. "What do we need to know" rather than "what should we do"?

**→ oracle.** Triggers: "what should we know about", "what are the considerations", "survey the terrain", "what does expert X think about".

### 5. Deliverable is a document (memo, ADR, position paper, brief)?

**→ committee.** Triggers: "write a memo", "draft an ADR", "position paper", "brief the team on".

### 6. Reviewing a design doc or spec produced by someone else?

**→ peer-review.** Triggers: "review this design doc", "critique this spec", "evaluate this proposal".

### 7. Ideation / early exploration / "give me options"?

**→ brainstorm.** Triggers: "brainstorm", "give me ideas", "explore options", "what could we do about".

### 8. Decision with a clear for/against, especially adversarial?

**→ court.** Triggers: "is my refactor safe", "should we merge this", "review this PR adversarially", "prosecute / defend".

### 9. Complex spec or long-form with many stakeholders (≥ 5)?

**→ rfc.** Triggers: roster size ≥ 5, "distributed review", "async comments", "get feedback from a lot of people".

### 10. Converging on a shared plan / design / spec (small group)?

**→ consensus.** Triggers: "agree on a design", "design an API together", "converge on a plan", "produce a spec we all accept".

### 11. Open question, diverse perspectives wanted, no single right answer?

**→ parliament** (default). Triggers: "should we", "is it a good idea", "debate this", "what do you think", or nothing specific.

## Format summary (for the rationale paragraph)

One-line reminders of what each format optimizes for. Use these when writing `## Why this format`.

| Format | Optimizes for |
| --- | --- |
| parliament | Diversity of perspective, surfacing dissent |
| court | Adversarial stress on a specific proposition |
| consensus | Convergence on a shared deliverable |
| committee | Polished document from small-group deliberation |
| peer-review | Structured independent critique of submitted work |
| brainstorm | Breadth of options, optionality preserved |
| oracle | Informing a decision, not making it |
| socratic | Stress-testing one claim or reasoning chain |
| appeals-court | Auditing a prior ruling for error |
| rfc | Scaling review beyond ~5 participants |
| red-team | Finding failure modes / adversarial audit |

## Multi-stage hint

If the user's task contains **two distinct questions** ("first decide X, then design Y") or **explicit pipeline language** ("draft → review → revise"), don't pick a single format — switch to multi-stage planning per `stages.md`.

## Edge cases

- **User task is a request for one model's answer** (e.g., "explain X") → senate is the wrong skill. Tell the user to call the CLI directly.
- **User specifies a roster that doesn't fit the recommendation** (e.g., asks for red-team with 1 attacker vs. recommended 2–3) → recommend the format but note the roster concern in `## Open questions`.
- **None of rules 1–11 fit cleanly** → ask one clarifying question per `clarification.md`. Don't guess a format for a task you don't understand.
