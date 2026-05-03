# committee

## Defining commitment

Members deliberate; an editor drives drafting and closes on final text. Cross-talk is expected; **at least one round where members react to revised text and to prior critiques** — not just a single review cycle. The artifact-under-revision is the centerpiece; turns are evaluated by how they improve it, not by who "wins."

## Boundary conditions

- All participants are peers acting in good faith. No adversarial roles, no judges, no isolated reviewers.
- Exactly one editor, who drives drafting. The editor advocates for coherence, not a position.
- Terminates on internal closure (members vote `approve` / `approve_with_dissent` / `block`); editor publishes with dissent recorded.
- The artifact (memo, ADR, spec, plan) IS the deliverable, not a decision about it.

## Anti-drift fence

| If the task is… | The right primitive is… |
| --- | --- |
| "Many people independently critique a draft" | peer-review |
| "Two sides argue about whether to do this" | court |
| "Find ways this could fail" | red-team |
| "Generate options without converging" | brainstorm |
| "Cast a vote to decide a policy question" | parliament |

## Summary

Best when a single coherent voice matters — organizational documents, ADRs with a clear owner, position papers, briefs.

## Roles

| Role | Brief |
| --- | --- |
| `member` | Contributes to deliberation, critiques drafts, votes on final text. Typically 3–5 members. |
| `editor` | Drives drafting. Reads the discussion, produces successive drafts, closes on final text. Does not vote against their own drafts — they advocate for coherence, not a position. |
| `chair` *(optional)* | Runs the meeting: calls on members, cuts off unproductive threads, declares closure. Only needed for committees of ≥4 members. |

Minimum: 1 member + editor = 2 (the pipeline-collapse shape — single-author drafting where the editor closes on the same content the member writes). Typical for standalone committee debates: 3 members + editor = 4. Max: 5 members + editor + chair = 7.

## Phases

### 1. Framing — **sequential**, single turn

Role: `editor`.

```
You are the editor of a committee deliberating: {task}

Write a one-paragraph framing of the task. What question is the committee answering, and in what scope? What is out of scope? What shape should the final document take (memo, ADR, brief, list)?

Members will discuss based on your framing. Be neutral.
```

Output contract: free text, ≤300 words.

### 2. Member input — **parallel**

Roles: all `member`s.

```
You are a committee member. The task and framing are below.

{framing}

Contribute your view in 200–400 words. Focus on:
- the most important point you think must be in the final document,
- any consideration that might be overlooked,
- any objection to the framing itself.

Do not attempt to write the full document. The editor will draft.
```

Output contract: free text.

### 3. Draft — **sequential**, single turn

Role: `editor`.

```
You are the editor. All member input is below.

{transcript_slice: member input}

Write draft 1 of the committee's document. Shape: {shape from framing}. Length: whatever the task requires.

At the end of your turn, list the points where members disagreed or where you made a judgment call.
```

Output contract: free text + a trailing "Open points" section.

### 4. Review rounds — **sequential**, repeated for `rounds` iterations (default 2)

Each round: all members comment on the current draft (parallel), then editor revises (sequential). Members react to the revised text in subsequent rounds — this is what distinguishes committee from peer-review.

Member prompt:

```
You are a committee member. The current draft and the editor's notes on open points are below.

{current_draft}

In 100–250 words:
- what in the draft you support,
- what you disagree with (cite section/line),
- one concrete change you propose.

Do not rewrite the document. Propose.
```

Editor prompt (after all members):

```
You are the editor. Member comments on the current draft are below.

{current_draft}
{member_comments}

Produce the next draft. For each member comment, briefly indicate: accepted / declined (with reason) / deferred. End with an updated "Open points" list.
```

Output contract: free text on both turns.

### 5. Closure vote — **parallel**

Roles: all `member`s.

```
You are a committee member. The final draft is below.

{final_draft}

Vote on whether to approve this document for publication.

Reply with a single fenced json block and nothing else:

```json
{"vote": "approve" | "approve_with_dissent" | "block", "confidence": 0.0-1.0, "dissent_point": "..."}
```

`dissent_point` is required only if vote is `approve_with_dissent` or `block`.
```

Output contract: format-specific fenced JSON with the schema shown above (a committee-local override of the canonical `vote` shape, with `approve` / `approve_with_dissent` / `block` values and a `dissent_point` field). On contract failure, the per-turn subagent re-prompts once if the turn's retry budget is still available; fallback is `approve_with_dissent` with `dissent_point: "vote failed contract"`.

#### Contract: `committee-final-vote`

The moderator passes this contract to the per-turn subagent for the final vote turn (see `../../moderate-debate/references/contracts.md` and `../../moderate-debate/SKILL.md` §4a):

- **Schema** — fenced JSON object: `{"vote": "approve" | "approve_with_dissent" | "block", "confidence": 0.0-1.0, "dissent_point": "..."}`. `dissent_point` is required when `vote` is `approve_with_dissent` or `block`; otherwise it may be an empty string.
- **Example** — `{"vote": "approve_with_dissent", "confidence": 0.74, "dissent_point": "Operational rollout still needs an explicit owner."}`
- **Extraction rule** — parse the last fenced `json` block in the reply.
- **Re-prompt template** — `Your previous reply did not match the committee final-vote contract. Reply now with ONLY one fenced json block matching: {"vote": "approve" | "approve_with_dissent" | "block", "confidence": 0.0-1.0, "dissent_point": "..."}. No prose.`

### 6. Publication — **sequential**, single turn

Role: `editor` (or `chair` if present). Produces the synthesis (which IS the deliverable). The reply is a markdown body **followed by** a trailing fenced `json` block summarizing the closure-vote tally:

````markdown
# {document title}

{final draft body}

---

## Committee disposition

- Approved by: ...
- Dissent: ...
- Rounds: N

```json
{"outcome": "approved" | "approved_with_dissent" | "blocked", "vote_tally": {"approve": N, "approve_with_dissent": N, "block": N}, "rounds": N, "dissent_points": ["..."]}
```
````

The editor's publication becomes the synthesis content. The moderator writes it to `stages/<N>-<name>/verdict.md` (schema in `../../meeting-note/references/verdict-schema.md`); the scribe folds it into the run-wide `notes.md`. Downstream stages may bind `fenced-json.outcome` and `fenced-json.vote_tally`.

## Termination

- After phase 5 completes, phase 6 runs regardless of vote outcome.
- If a `block` vote is cast, editor must either revise once more (extra round) or publish with the dissent recorded as a blocking minority opinion. Default: publish with dissent.
- Early exit: if all members approve with high confidence after round 1, skip remaining review rounds.

## Defaults

- **Rounds** (review): 2. Cap at 4.
- **Roster size**: 2–7 (2 = single member + editor, used in pipeline stages where committee is acting as a single-author drafting step).
- **Agent failure**: missing member input or comment = that member abstains from that phase; editor continues. Missing closure vote = `approve_with_dissent`.
