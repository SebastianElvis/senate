# consensus

## Summary

Iterative format where all agents propose, critique, and refine a shared artifact until they converge or hit a round cap. No adversarial roles — every participant is trying to produce the best answer jointly. Best for API designs, spec drafts, plans, or any task where the output is a document rather than a decision.

## Roles

| Role | Brief |
| --- | --- |
| `contributor` | One per participating CLI. Proposes, critiques, and refines. All contributors are peers. |
| `arbiter` | Orchestration role. Decides when consensus is reached, produces the synthesis. Does not contribute content in normal phases. |

Minimum roster: 2 contributors + arbiter. Typical: 3–4 contributors + arbiter. Max: 5 contributors.

## Phases

### 1. Initial proposals — **parallel**

Roles: all contributors.

Prompt:

```
You are one of several contributors collaborating on: {task}

Propose your answer in full. Be complete and specific — this is your first draft and others will critique it. Length: whatever the task requires, but be concrete.
```

Output contract: free text. Each proposal becomes a candidate draft.

### 2. Critique — **parallel**

Roles: all contributors. Each contributor critiques the **other** proposals (not their own).

Prompt:

```
You are contributor {role}. The other contributors' proposals are below.

{transcript_slice: other proposals from phase 1}

For each, in 50–150 words:

- What is strongest about it?
- What is the most important flaw or gap?
- One concrete suggestion to improve it.

Do not defend your own proposal here.
```

Output contract: free text, one block per other contributor's proposal.

### 3. Refine — **parallel**, repeated until convergence or `max_rounds` (default 3)

Roles: all contributors.

Prompt:

```
You are contributor {role}. Below is the current best-draft (from the arbiter) plus all critiques from the last round.

Current draft: {current_draft}
Critiques: {transcript_slice: last critique phase}

Produce a refined draft. You may:
- adopt changes you agree with,
- reject changes with a one-line reason,
- add new content you think is missing.

End your turn with a fenced json block:

```json
{"changed": true | false, "confidence": 0.0-1.0, "remaining_concerns": ["..."]}
```
```

Output contract: a refined draft followed by the fenced json block.

### 4. Convergence check — **arbiter**, after each refine round

The arbiter reads all refined drafts and decides:

- **Converged** if: all contributors report `"changed": false` OR the mean semantic similarity between drafts is high AND no contributor lists substantive `remaining_concerns`.
- **Not converged**: continue to the next refine round, using the draft with highest mean confidence as the new `current_draft`.
- **Stalled**: if `max_rounds` reached without convergence, arbiter picks the draft with the strongest support and notes outstanding concerns in the verdict.

The arbiter is usually a designated CLI (e.g., `claude`); if unspecified, use the first contributor.

### 5. Synthesis — **sequential**, single turn

Role: `arbiter`.

Prompt:

```
You are the arbiter of a consensus process on: {task}

All refined drafts and critiques are below.

{transcript_slice: full}

Produce the final artifact as a markdown document with sections:

- **Artifact** — the agreed deliverable (the answer, spec, plan).
- **Confidence** — converged / partial / stalled.
- **Remaining concerns** — anything contributors flagged that was not resolved.
- **Process notes** — number of rounds, which contributor's draft became the base, one-line rationale.
```

Output contract: markdown with those four sections. The arbiter's reply becomes the synthesis content; `meeting-note` writes the canonical `verdict.md` from it (see `../../meeting-note/references/verdict-schema.md`).

## Termination

- Converges when all contributors report `"changed": false` and `remaining_concerns` is empty.
- Hard cap at `max_rounds` refine iterations (default 3, max 6).

## Defaults

- **max_rounds**: 3.
- **Roster size**: 2–5 contributors + arbiter.
- **Agent failure**: a missing proposal in phase 1 drops that contributor from the process; missing refine turns reuse the contributor's last draft.
- **Tie-breaking**: if two drafts are equally supported at stall, arbiter picks the one with fewer `remaining_concerns`.
