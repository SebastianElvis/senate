---
name: format-selector
description: Recommends a debate format for a given task. Use when the user asks the senate skill to run a debate but doesn't specify which format, or when they ask which format would be best-suited to their question. Returns one recommended format, one alternative, and a one-paragraph rationale.
---

# format-selector — recommend a format for a task

A quick-lookup skill. Takes a task description in natural language, returns:

1. **Primary recommendation** — the best-fit format from the `debate-format` library.
2. **Alternative** — a second reasonable choice, in case the primary feels too heavyweight or too narrow.
3. **Rationale** — one paragraph explaining the choice.

This is invoked by `senate` when a user initiates a debate without specifying a format, or directly when a user asks *"which format should I use for X?"*.

## How to decide

Walk this decision tree in order. First match wins. If multiple match, the **earlier** rule takes priority.

### 1. Is this a security / reliability / failure-mode review?

**→ red-team.** Triggers: "attack", "find failure modes", "is this safe", "pre-mortem", "what breaks", "security review", "threat model".

### 2. Is the user explicitly reviewing a prior court verdict?

**→ appeals-court.** Triggers: reference to a prior `run_id`, "second opinion on that ruling", "was that decided correctly".

### 3. Is this a single specific claim being stress-tested?

**→ socratic.** Triggers: "is X really true", "test this claim", "is this reasoning sound", "debug this line of thought".

### 4. Is this "what do we need to know" rather than "what should we do"?

**→ oracle.** Triggers: "what should we know about", "what are the considerations", "survey the terrain", "what does expert X think about".

### 5. Is the deliverable a document (memo, ADR, position paper, brief)?

**→ committee.** Triggers: "write a memo", "draft an ADR", "position paper", "brief the team on".

### 6. Is the user reviewing a design doc or spec produced by someone else?

**→ peer-review.** Triggers: "review this design doc", "critique this spec", "evaluate this proposal".

### 7. Is this ideation / early exploration / "give me options"?

**→ brainstorm.** Triggers: "brainstorm", "give me ideas", "explore options", "what could we do about".

### 8. Is this a decision with a clear for/against, especially adversarial?

**→ court.** Triggers: "is my refactor safe", "should we merge this", "review this PR adversarially", "prosecute / defend".

### 9. Is this a complex spec or long-form with many stakeholders (≥ 5)?

**→ rfc.** Triggers: roster size ≥ 5, "distributed review", "async comments", "get feedback from a lot of people".

### 10. Is this converging on a shared plan / design / spec (small group)?

**→ consensus.** Triggers: "agree on a design", "design an API together", "converge on a plan", "produce a spec we all accept".

### 11. Open question, diverse perspectives wanted, no single right answer?

**→ parliament.** (default). Triggers: "should we", "is it a good idea", "debate this", "what do you think", or nothing specific.

## Output shape

Return to the caller as a structured block:

```markdown
**Recommended format:** <format-name>

**Alternative:** <other-format-name>

**Why:** <1-paragraph rationale, naming what about the task pointed to this format and why the alternative would also be reasonable but different>
```

## Edge cases

- **User task contains two questions** → recommend running two debates sequentially. If the user confirms, suggest using `workflow` (H3) to chain them.
- **User task is actually a request for one model's answer** (e.g., "explain X") → do not recommend a format; suggest calling the CLI directly and mention that the senate skill is for multi-agent debate.
- **User task is unclear** → ask one clarifying question (target, stakes, output shape) before recommending.
- **User specifies a roster that doesn't fit the recommendation** (e.g., asks for red-team with 1 attacker vs. recommended 2–3) → recommend the format but note the roster concern.

## Format summary for the rationale

For the rationale paragraph, one-line reminders of what each format optimizes for:

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

## Files in this skill

- `SKILL.md` — this file. Selector is decision-tree logic, no sub-files needed.
