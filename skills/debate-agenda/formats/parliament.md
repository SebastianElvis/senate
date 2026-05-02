# parliament

## Defining commitment

Outcome is determined by **aggregation of individual votes**, not by an arbiter's judgment. Participants optimize for coalition-building, persuasion under known aggregation, and explicit dissent accounting. Each agent represents a viewpoint (pro, con, neutral, or custom parties), exchanges opening statements and rebuttals, then votes. A designated **speaker** tallies votes and writes the verdict.

Parliament is the only primitive that closes by tally. (Vote-vs-ruling is a behavioral axis, not just a terminal mechanism — folding it into court would lose the coalition dynamic.)

## Boundary conditions

- At least 2 MPs (typically 3+); each MP represents a viewpoint and is committed to vote.
- Exactly one speaker, who tallies and synthesizes but does not argue or vote (except as tiebreaker).
- Output is a verdict-with-tally and explicit dissent.

## Anti-drift fence

| If the task is… | The right primitive is… |
| --- | --- |
| "Sides argue with an arbiter" | court |
| "Independent panel of experts" | panel |
| "Peers co-author a draft" | workshop |
| "Generate options" | brainstorm |

## Summary

Best for open questions where you want diversity of perspective rather than a single winning argument.

## Roles

| Role | Brief |
| --- | --- |
| `mp_pro` | Arguing **for** the proposition. Steelman the best case. Must cite concrete reasoning, not just assert. |
| `mp_con` | Arguing **against** the proposition. Steelman the strongest objection. |
| `mp_neutral` | Weighs both sides, introduces considerations neither side raised, flags false dichotomies. Does not have to pick a side in rebuttals. |
| `speaker` | Orchestration role. Does not argue. Tallies votes, resolves ties, produces the synthesis. |

A minimal parliament has 2 MPs (one pro, one con) + speaker. Typical is 3 MPs + speaker. Additional parties ("mp_pragmatic", "mp_radical", etc.) can be added in the roster — give each a named brief in the agenda's stage roster.

## Phases

### 1. Opening statements — **parallel**

Roles: all MPs.

Prompt:

```
You are {role} in a parliamentary debate on: {task}

Your brief: {role_brief}

Give your opening statement in 150–300 words. State your position, your top 3 reasons, and the evidence or reasoning behind each.

Do not respond to other MPs — you are speaking first.
```

Output contract: free text.

### 2. Rebuttal rounds — **sequential**, repeated for `rounds` iterations (default 2)

Roles: all MPs, in roster order.

Prompt:

```
You are {role}. The opening statements and prior rebuttals are below.

{transcript_slice: all prior mp turns}

Give your rebuttal in 100–200 words. Address the strongest point made by another MP. You may concede, refine, or counter — but identify which turn(s) you are responding to by number.
```

Output contract: free text, must reference at least one prior turn by its number (e.g., "T2").

### 3. Final vote — **parallel**

Roles: all MPs.

Prompt:

```
You are {role}. Based on the full debate transcript, cast your final vote on: {task}

{transcript_slice: full}

Respond with a single fenced json block and nothing else:

```json
{"vote": "yes" | "no" | "abstain", "confidence": 0.0-1.0, "reason": "one-sentence rationale"}
```
```

Output contract: a fenced `json` block parseable as above. On contract failure, the per-turn subagent re-prompts once if the turn's retry budget is still available; if validation still fails, record as `abstain`.

### 4. Verdict — **sequential**, single turn

Role: `speaker`.

Prompt:

```
You are the speaker of this parliament. Write the verdict for: {task}

Vote tally: {tally}
Full transcript: {transcript_slice: full}

Produce a markdown document with three top-level sections, **named exactly** `## Decision`, `## Rationale`, and `## Dissent` (no parenthetical suffixes in the heading line). Cite turn numbers as `T<n>` in the Rationale body.

Then append a fenced json block with the structured outcome, no other prose after it:

```json
{"outcome": "pass" | "fail" | "tied", "tally": {"yes": N, "no": N, "abstain": N}, "speaker_tiebreak": "yes" | "no" | null}
```
```

Output contract: markdown with the three sections above, **followed by** a fenced `json` block matching the schema. The speaker's reply becomes the synthesis content. The moderator writes it to `stages/<N>/verdict.md` (the bindings target — schema in `../../meeting-note/references/verdict-schema.md`); the scribe (`meeting-note`) then folds it into the run-wide `notes.md`. Downstream stages may bind `fenced-json.outcome` and `fenced-json.tally`.

## Termination

- Fires after phase 4 completes.
- No early-exit: parliament always plays out the full round count even if one side concedes, because recording dissent is the point.

## Defaults

- **Rounds** (rebuttals): 2. Cap at 4.
- **Roster size**: 2–5 MPs, plus speaker.
- **Agent failure**: a missing vote counts as `abstain`; missing rebuttals are skipped and noted in the speaker's synthesis.
- **Vote-counting rule**: plurality wins. Tie → speaker casts deciding vote in the verdict, labeled clearly.
