# committee

## Summary

Small group deliberates in private, produces a written recommendation. Unlike parliament (which votes) or court (which rules), a committee **drafts a document** — the output is the deliverable itself, not a decision about it. Best for memos, design briefs, ADRs, position papers, or any task where the value is in the prose, not the verdict.

## Roles

| Role | Brief |
| --- | --- |
| `member` | Contributes to deliberation, critiques drafts, votes on final text. Typically 3–5 members. |
| `editor` | Drives drafting. Reads the discussion, produces successive drafts, closes on final text. Does not vote against their own drafts — they advocate for coherence, not a position. |
| `chair` *(optional)* | Runs the meeting: calls on members, cuts off unproductive threads, declares closure. Only needed for committees of ≥4 members. |

Minimum: 2 members + editor = 3. Typical: 3 members + editor = 4. Max: 5 members + editor + chair = 7.

## Phases

### 1. Framing — **sequential**, single turn

Role: `editor`.

Prompt:

```
You are the editor of a committee deliberating: {task}

Write a one-paragraph framing of the task. What question is the committee answering, and in what scope? What is out of scope? What shape should the final document take (memo, ADR, brief, list)?

Members will discuss based on your framing. Be neutral.
```

Output contract: free text, ≤300 words.

### 2. Member input — **parallel**

Roles: all `member`s.

Prompt:

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

Prompt:

```
You are the editor. All member input is below.

{transcript_slice: member input}

Write draft 1 of the committee's document. Shape: {shape from framing}. Length: whatever the task requires.

At the end of your turn, list the points where members disagreed or where you made a judgment call.
```

Output contract: free text + a trailing "Open points" section.

### 4. Review rounds — **sequential**, repeated for `rounds` iterations (default 2)

Each round: all members comment on the current draft (parallel), then editor revises (sequential).

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

Prompt:

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

Output contract: canonical `vote` (see `../senate/CONTRACTS.md`), with the vote values above. Re-prompt once on failure; fallback is `approve_with_dissent` with `dissent_point: "vote failed contract"`.

### 6. Publication — **sequential**, single turn

Role: `editor` (or `chair` if present).

Produces `verdict.md` (which, for a committee, *is* the deliverable):

```markdown
# {document title}

{final draft body}

---

## Committee disposition

- Approved by: ...
- Dissent: ...
- Rounds: N
```

## Termination

- After phase 5 completes, phase 6 runs regardless of vote outcome.
- If a `block` vote is cast, the editor must either revise once more (extra round) or publish with the dissent recorded as a blocking minority opinion. Default: publish with dissent.
- Early exit: if all members approve with high confidence after round 1, skip the remaining review rounds.

## Defaults

- **Rounds** (review): 2. Cap at 4.
- **Roster size**: 3–7.
- **Agent failure**: missing member input or comment = that member abstains from that phase; editor continues. Missing closure vote = `approve_with_dissent`.
- **Tie-breaking**: not applicable (committee publishes, doesn't rule).
