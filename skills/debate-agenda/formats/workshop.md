# workshop

## Defining commitment

Participants engage as **co-authors of a shared draft, not merely as independent evaluators.** A small group of peers iteratively produces a shared written artifact through propose → critique → refine cycles. The output IS the deliverable (memo, ADR, spec, plan), not a decision about it.

## Boundary conditions

- All participants are peers acting in good faith. No adversarial roles, no judges, no isolated reviewers.
- Cross-talk is expected; **at least one round where contributors react to revised text and to prior critiques** — not just a single review cycle.
- Terminates on internal closure (agreement or vote among the same peers), not external arbitration.
- The artifact-under-revision is the centerpiece; turns are evaluated by how they improve it, not by who "wins."

## Anti-drift fence

| If the task is… | The right primitive is… |
| --- | --- |
| "Many people independently critique a draft" | panel |
| "Two sides argue about whether to do this" | court |
| "Generate options without converging" | brainstorm |
| "Cast a vote to decide a policy question" | parliament |

## Presets

| Preset | mode | Initial draft | Closure | When to pick |
| --- | --- | --- | --- | --- |
| `committee` | editor_led | Editor frames + writes draft 1 from member input. | Members vote `approve` / `approve_with_dissent` / `block`; editor publishes with dissent recorded. | A single coherent voice matters (organizational document, ADR with a clear owner). |
| `consensus` | peer_egalitarian | All contributors propose in parallel; arbiter picks current best draft each round (process-only, never content). | No unresolved blocking concerns (residual non-blocking concerns captured in summary). | Multiple genuine perspectives must converge without one party dominating (cross-team API design, joint specs). |

The agenda's stage declares `format: workshop` plus `preset: <name>`.

The two presets share the same phase shape (propose → critique → refine ×N rounds → close) but differ in **who may synthesize, how draft ownership works, and what counts as closure** — these are contract-defining differences, not labels.

---

## Preset: `committee` (editor_led)

Members deliberate; an editor drives drafting and closes on final text. Distinct from `consensus` (peer_egalitarian) because authority is centralized in the editor, and dissent can persist at close.

### Roles

| Role | Brief |
| --- | --- |
| `member` | Contributes to deliberation, critiques drafts, votes on final text. Typically 3–5 members. |
| `editor` | Drives drafting. Reads the discussion, produces successive drafts, closes on final text. Does not vote against their own drafts — they advocate for coherence, not a position. |
| `chair` *(optional)* | Runs the meeting: calls on members, cuts off unproductive threads, declares closure. Only needed for committees of ≥4 members. |

Minimum: 2 members + editor = 3. Typical: 3 members + editor = 4. Max: 5 members + editor + chair = 7.

### Phases

#### 1. Framing — **sequential**, single turn

Role: `editor`.

```
You are the editor of a committee deliberating: {task}

Write a one-paragraph framing of the task. What question is the committee answering, and in what scope? What is out of scope? What shape should the final document take (memo, ADR, brief, list)?

Members will discuss based on your framing. Be neutral.
```

Output contract: free text, ≤300 words.

#### 2. Member input — **parallel**

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

#### 3. Draft — **sequential**, single turn

Role: `editor`.

```
You are the editor. All member input is below.

{transcript_slice: member input}

Write draft 1 of the committee's document. Shape: {shape from framing}. Length: whatever the task requires.

At the end of your turn, list the points where members disagreed or where you made a judgment call.
```

Output contract: free text + a trailing "Open points" section.

#### 4. Review rounds — **sequential**, repeated for `rounds` iterations (default 2)

Each round: all members comment on the current draft (parallel), then editor revises (sequential). Members react to the revised text in subsequent rounds — this is what distinguishes workshop from panel.

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

#### 5. Closure vote — **parallel**

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

##### Contract: `committee-final-vote`

The moderator passes this contract to the per-turn subagent for the final vote turn (see `../../moderate-debate/references/contracts.md` and `../../moderate-debate/SKILL.md` §4a):

- **Schema** — fenced JSON object: `{"vote": "approve" | "approve_with_dissent" | "block", "confidence": 0.0-1.0, "dissent_point": "..."}`. `dissent_point` is required when `vote` is `approve_with_dissent` or `block`; otherwise it may be an empty string.
- **Example** — `{"vote": "approve_with_dissent", "confidence": 0.74, "dissent_point": "Operational rollout still needs an explicit owner."}`
- **Extraction rule** — parse the last fenced `json` block in the reply.
- **Re-prompt template** — `Your previous reply did not match the committee final-vote contract. Reply now with ONLY one fenced json block matching: {"vote": "approve" | "approve_with_dissent" | "block", "confidence": 0.0-1.0, "dissent_point": "..."}. No prose.`

#### 6. Publication — **sequential**, single turn

Role: `editor` (or `chair` if present). Produces the synthesis (which IS the deliverable):

```markdown
# {document title}

{final draft body}

---

## Committee disposition

- Approved by: ...
- Dissent: ...
- Rounds: N
```

The editor's publication becomes the synthesis content. The moderator writes it to `stages/<N>/verdict.md` (schema in `../../meeting-note/references/verdict-schema.md`); the scribe folds it into the run-wide `notes.md`.

### Termination

- After phase 5 completes, phase 6 runs regardless of vote outcome.
- If a `block` vote is cast, editor must either revise once more (extra round) or publish with the dissent recorded as a blocking minority opinion. Default: publish with dissent.
- Early exit: if all members approve with high confidence after round 1, skip remaining review rounds.

### Defaults

- **Rounds** (review): 2. Cap at 4.
- **Roster size**: 3–7.
- **Agent failure**: missing member input or comment = that member abstains from that phase; editor continues. Missing closure vote = `approve_with_dissent`.

---

## Preset: `consensus` (peer_egalitarian)

All contributors are peers; an arbiter declares convergence but never contributes content. Distinct from `committee` because authority is flat — no editor, no dissent at close (closure requires explicit exhaustion of blocking concerns).

### Roles

| Role | Brief |
| --- | --- |
| `contributor` | One per participating CLI. Proposes, critiques, and refines. All contributors are peers. |
| `arbiter` | Orchestration role. Decides when consensus is reached, produces the synthesis. **Does not contribute content** in any phase. |

Minimum roster: 2 contributors + arbiter = 3. Typical: 3–4 contributors + arbiter. Max: 5 contributors.

### Phases

#### 1. Initial proposals — **parallel**

Roles: all contributors.

```
You are one of several contributors collaborating on: {task}

Propose your answer in full. Be complete and specific — this is your first draft and others will critique it. Length: whatever the task requires, but be concrete.
```

Output contract: free text. Each proposal becomes a candidate draft.

#### 2. Critique — **parallel**

Roles: all contributors. Each contributor critiques the **other** proposals (not their own).

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

#### 3. Refine — **parallel**, repeated until convergence or `max_rounds` (default 3)

Roles: all contributors. Workshop's defining cross-talk: contributors react to revised text and to others' critiques across rounds.

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
{"changed": true | false, "confidence": 0.0-1.0, "remaining_concerns": ["..."], "blocking": true | false}
```

`blocking` is true if any item in `remaining_concerns` is something you would not accept in the final artifact.
```

Output contract: a refined draft followed by the fenced json block.

#### 4. Convergence check — **arbiter**, after each refine round

The arbiter reads all refined drafts and decides:

- **Converged** if: no contributor reports any `remaining_concerns` with `blocking: true`. (Residual non-blocking concerns are recorded in the synthesis but do not block closure.)
- **Not converged**: continue to the next refine round, using the draft with highest mean confidence as the new `current_draft`.
- **Stalled**: if `max_rounds` reached without convergence, arbiter picks the draft with the strongest support and notes outstanding blocking concerns in the verdict.

#### 5. Synthesis — **sequential**, single turn

Role: `arbiter`.

```
You are the arbiter of a consensus process on: {task}

All refined drafts and critiques are below.

{transcript_slice: full}

Produce the final artifact as a markdown document with sections:

- **Artifact** — the agreed deliverable (the answer, spec, plan).
- **Confidence** — converged / partial / stalled.
- **Remaining concerns** — anything contributors flagged that was not resolved (separate blocking from non-blocking).
- **Process notes** — number of rounds, which contributor's draft became the base, one-line rationale.
```

Output contract: markdown with those four sections. The arbiter's reply becomes the synthesis content. The moderator writes it to `stages/<N>/verdict.md` (schema in `../../meeting-note/references/verdict-schema.md`); the scribe folds it into the run-wide `notes.md`.

### Termination

- Converges when no contributor reports a blocking remaining concern.
- Hard cap at `max_rounds` refine iterations (default 3, max 6).

### Defaults

- **max_rounds**: 3.
- **Roster size**: 2–5 contributors + arbiter.
- **Agent failure**: a missing proposal in phase 1 drops that contributor from the process; missing refine turns reuse the contributor's last draft.
- **Tie-breaking**: if two drafts are equally supported at stall, arbiter picks the one with fewer blocking remaining concerns.
