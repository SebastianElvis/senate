# panel

## Defining commitment (load-bearing invariant)

**Multiple isolated judgments combined by a non-participating synthesizer.** Contributors work in parallel and **must not see each other's outputs while producing them**; a separate synthesizer reads all contributor outputs and produces the synthesis. Independence-of-error is the point — two contributors agreeing is signal only if they couldn't have been influenced by each other.

## Boundary conditions

- Contributors work in parallel without cross-talk. The moderator enforces transcript-slice scoping so each contributor sees only the input artifact (question or draft), never other contributors' responses.
- At least 2 contributors. Independence is meaningful only with multiples.
- The synthesizer is a separate role and never contributes content during the parallel phase.
- Output is a synthesized artifact (information brief, merged comment doc, editor decision). **Not a vote tally. Not a co-authored draft.**
- **No-re-engagement rule**: if a preset has a revision round, only the original `author` revises; contributors do not re-engage. Contributor outputs are one-shot. (Without this rule, panel drifts into workshop.)

## Anti-drift fence

| If the task is… | The right primitive is… |
| --- | --- |
| "Peers iterate on a shared draft" | workshop |
| "Sides argue with an arbiter" | court |
| "Cast a vote" | parliament |
| "Generate options" | brainstorm |

## Presets

| Preset | input_type | review_protocol | revision_round | When to pick |
| --- | --- | --- | --- | --- |
| `oracle` | question | freeform | disabled | "What do we need to know before deciding X?" |
| `peer-review` | draft | freeform | enabled | Structured independent critique of a submission. |
| `rfc` | draft | anchored_annotations | enabled | Asynchronous distributed review at scale (≥ 5 contributors). |

The agenda's stage declares `format: panel` plus `preset: <name>`.

---

## Preset: `oracle` (question, freeform, no revision)

A questioner consults a panel of domain experts. Experts answer independently and without cross-talk; a synthesizer combines their answers. Best for *"what do we need to know before deciding X?"* — surface relevant considerations, not reach a decision.

### Roles

| Role | Brief |
| --- | --- |
| `questioner` | Frames the question for the panel; may refine after seeing initial answers. |
| `expert` | Answers from a specific perspective / discipline. The moderator assigns each expert a named domain (e.g., "security expert", "performance expert", "pragmatist"). |
| `synthesizer` | Reads all expert answers, produces the combined response. |

Minimum: questioner + 2 experts + synthesizer = 4. Typical: questioner + 3–4 experts + synthesizer = 5–6.

### Phases

#### 1. Frame — **sequential**, single turn

Role: `questioner`.

```
You are the questioner consulting a panel of experts on: {task}

Produce the question(s) for the panel. Be specific. For each question, state:
- what you want to know,
- what it would change in your decision,
- any assumptions you want the expert to challenge.

The panel's composition is:
{list of expert_role + assigned domain}

End with the question(s) clearly numbered.
```

Output contract: free text, must contain a numbered question list.

#### 2. Expert answers — **parallel**

Roles: all `expert`s. **Strict isolation**: each expert's `transcript_slice` contains only phase 1 (the framing), never other experts' answers.

```
You are the {expert_domain} expert on a panel consulted on: {task}

The questioner's framing and questions are below.

{framing}

Answer from your domain perspective. For each numbered question:
- your answer, in 100–300 words,
- the evidence or reasoning,
- what you are NOT qualified to say (where this question extends beyond your domain).

Do not try to cover the ground other experts would cover. Stay in your lane.
```

Output contract: free text, one numbered section per question.

#### 3. Refinement (optional) — **sequential**, one turn

Role: `questioner`. Triggered only if the moderator detects divergent answers (experts fundamentally disagree on a factual point).

```
You are the questioner. The experts' answers are below.

{transcript_slice: expert answers}

Experts gave conflicting answers on:
{auto-detected divergence points}

Produce at most 3 narrower follow-up questions that would resolve the disagreement. Do not take sides.
```

If the moderator cannot auto-detect divergence reliably, skip this phase.

#### 3b. Follow-up expert answers — **parallel**

If phase 3 fired. Experts answer the follow-ups under the same isolation rule.

#### 4. Synthesis — **sequential**, single turn

Role: `synthesizer`.

```
You are the synthesizer. All expert answers are below.

{transcript_slice: full}

Produce the oracle verdict as a markdown document:

- **Question** — the original task, restated crisply.
- **Panel composition** — who the experts were (domains only).
- **Key answers** — for each numbered question, what the experts said. Note where they agreed and where they diverged.
- **What we now know** — the synthesized answer, written as if briefing a decision-maker.
- **What we still don't know** — open points, named explicitly.
- **Confidence** — high / medium / low, with reasoning.
```

Output contract: markdown with those six sections.

### Termination

- After phase 4. Oracle does not produce a decision — it produces information.
- Common follow-up: feed the verdict into a `court`, `parliament`, or `workshop` for the actual decision.

### Defaults

- **Experts**: 3–4.
- **Follow-up round**: enabled by default; disable with `--no-followup`.
- **Agent failure**: a missing expert answer = that domain is absent from the synthesis; flag in "What we still don't know".
- **Isolation is non-negotiable.** If the moderator cannot guarantee that experts do not see each other's turns, do not claim this preset produces independent answers.

---

## Preset: `peer-review` (draft, freeform, revision enabled)

Author submits work; reviewers critique blindly and in parallel; author revises; editor adjudicates and produces a final ruling. Modeled on academic peer review.

### Roles

| Role | Brief |
| --- | --- |
| `author` | Presents the work. Responds to reviewer comments. Revises. |
| `reviewer` | Reads the submission and produces a structured review. 2–4 reviewers, working independently; must not see each other's reviews until after revision. |
| `editor` | Reads all reviews + revision, issues the final decision. |

Minimum: 1 author + 2 reviewers + editor = 4. Typical: 1 + 3 + 1 = 5.

### Phases

#### 1. Submission — **sequential**, single turn

Role: `author`.

```
You are the author submitting for peer review. The task is:

{task}

Produce your initial submission. Include whatever sections the task requires. Be complete — this is what reviewers will critique.

At the end, add an "Author's notes" section flagging any parts you are least confident about.
```

Output contract: free text.

#### 2. Review — **parallel** (strict isolation)

Roles: all `reviewer`s. The moderator enforces blind review by scoping each reviewer's `transcript_slice` to just the submission.

```
You are a peer reviewer. The submission is below. You have not seen other reviewers' comments.

{submission}

Produce a structured review:

1. **Summary** — one paragraph: what is the submission arguing / proposing?
2. **Strengths** — bullet list.
3. **Major concerns** — bullet list. For each: cite specific section, state the issue, suggest a fix.
4. **Minor concerns** — bullet list.
5. **Recommendation** — accept / minor_revision / major_revision / reject.

End with a fenced json block:

```json
{"recommendation": "accept" | "minor_revision" | "major_revision" | "reject", "confidence": 0.0-1.0, "blocking_concerns": ["..."]}
```
```

Output contract: free text (review body) + fenced json block (machine-readable recommendation). Re-prompt once on failure; fallback recommendation is `major_revision`.

#### 3. Revision — **sequential**, single turn

Role: `author`. **No-re-engagement applies**: only the author revises; reviewers do not re-engage in this round.

```
You are the author. All reviewer comments are now visible.

{transcript_slice: reviews}

Produce the revised submission. For each major concern from each reviewer, explicitly indicate: addressed (cite where), declined (with reason), or deferred (with rationale).

If ≥2 reviewers agree on a major concern, you should either address it or offer a strong-evidence rebuttal.
```

Output contract: revised submission + explicit response-to-reviewers section.

#### 4. Editor's decision — **sequential**, single turn

Role: `editor`.

```
You are the editor. The original submission, reviews, and author's revision are all below.

{transcript_slice: full}

Issue your decision. Consider:
- how seriously the author engaged with major concerns,
- whether any reviewer's blocking concerns went unaddressed,
- whether reviewers agreed or diverged.

Produce the verdict as a markdown document with sections:

- **Decision** — one of: accept / minor_revision / major_revision / reject.
- **Summary of reviews** — one line per reviewer.
- **Author's response** — one paragraph assessing the revision.
- **Reasoning** — cite turn numbers.
- **Next steps** — what the author should do now.
```

Output contract: markdown + trailing fenced json:

```json
{"decision": "accept" | "minor_revision" | "major_revision" | "reject", "revision_deadline_days": 30}
```

On contract failure, fallback to `major_revision`.

### Termination

- After phase 4. No extended revision loop — if `major_revision` or `reject`, that terminates the run.
- The user may manually re-invoke peer-review on the revised submission as a new run.

### Defaults

- **Rounds**: 1 (submission + reviews + revision + decision).
- **Roster size**: 4–5.
- **Agent failure**: missing review = that reviewer does not contribute; if ≥2 reviewers are missing, editor issues `major_revision` with a "remanded due to insufficient review coverage" note, and the run is flagged in `failures.md`.
- **Blind review**: reviewers must not see each other's turns in phase 2 (moderator enforces via transcript scoping).

---

## Preset: `rfc` (draft, anchored_annotations, revision enabled)

Same independence-and-synthesis shape as peer-review, but with paragraph-anchored annotations as the review protocol. Modeled on IETF and public-sector RFC processes. Scales beyond ~5 contributors better than freeform reviews.

### Roles

| Role | Brief |
| --- | --- |
| `author` | Posts the initial RFC with numbered paragraphs. Reads merged comments and revises. |
| `commenter` | Reads the RFC and annotates it. Comments are inline, each attached to a specific quote from the RFC. |
| `editor` | Merges all comments into a single annotated RFC. Does not opine — organizes, de-duplicates, surfaces themes. |

Minimum: 1 author + 2 commenters + editor = 4. Typical: 1 + 3–6 + 1 = 5–8. Past ~10 commenters the editor's workload grows superlinearly.

### Phases

#### 1. Draft — **sequential**, single turn

Role: `author`.

```
You are the author posting an RFC on: {task}

Write the RFC as a markdown document. Include:
- Title.
- Summary (≤ 150 words).
- Motivation — why now, what problem.
- Proposal — the substantive content.
- Open questions (author's own list of things they're uncertain about).

Length: whatever the task requires, but err toward complete.

Number every paragraph in the proposal section — `¶1`, `¶2`, etc. Commenters reference these.
```

Output contract: free text, proposal section paragraphs are numbered `¶N`. If the author doesn't number paragraphs, the moderator re-prompts once before accepting the draft.

#### 2. Comment — **parallel** (strict isolation)

Roles: all `commenter`s. Moderator enforces that commenters do not see each other's comments.

```
You are a commenter reviewing the RFC below. You have not seen other commenters' feedback.

{rfc_draft}

Produce comments. Each comment must cite a specific paragraph (`¶N`) from the proposal and one of:

- **Question** — something unclear.
- **Objection** — something you believe is wrong or missing.
- **Suggestion** — a concrete change.
- **Support** — explicit endorsement (these help the editor weight consensus).

Format each comment:

> **¶N [kind]:** <comment body, 1–4 sentences>

Produce between 3 and 15 comments. Do not try to rewrite the RFC. You are annotating.
```

Output contract: free text, must contain at least one line starting with `> **¶`.

#### 3. Merge — **sequential**, single turn

Role: `editor`.

```
You are the editor of this RFC. All commenters' annotations are below.

{transcript_slice: comment phase}

Produce the merged comment document. For each proposal paragraph that received comments:

- Quote the paragraph.
- Group comments by type (questions, objections, suggestions, support) and deduplicate near-identical comments.
- For each group, note how many commenters (not names) raised it. Single comments are noted as singletons.

End with a section "Themes" summarizing the 3–5 most significant patterns across commenters.

Do NOT opine. Do NOT suggest changes of your own. You are organizing.
```

Output contract: free text, structured per above.

#### 4. Revision — **sequential**, single turn

Role: `author`. **No-re-engagement applies**: commenters do not annotate the revision.

```
You are the author. The merged comments are below.

{merged_comments}

Revise the RFC. For each theme and each grouped comment:

- **Addressed** — quote the change you made, cite the paragraph.
- **Declined** — state briefly why.
- **Deferred** — state what would be needed to address it later.

Produce the revised RFC with these author responses inline or in a closing section.
```

Output contract: revised RFC + explicit disposition per theme.

#### 5. Finalization — **sequential**, single turn

Role: `editor`.

```
You are the editor. The original RFC, merged comments, and author's revision are below.

{transcript_slice: full}

Produce the RFC verdict as a markdown document:

- **Final RFC** — the revised version, clean.
- **Disposition** — one of: finalized / revise_and_repost / withdrawn.
- **Summary of process** — rounds, number of commenters, themes, resolution rate (themes addressed / total).
- **Outstanding concerns** — anything declined or deferred by the author that received support from ≥ 2 commenters.
```

Output contract: markdown + trailing fenced json:

```json
{"disposition": "finalized" | "revise_and_repost" | "withdrawn", "resolution_rate": 0.0-1.0}
```

### Termination

- After phase 5.
- If disposition is `revise_and_repost`, user may re-invoke the rfc preset on the new draft.

### Defaults

- **Rounds**: 1. Multiple comment rounds are expensive; if needed, explicit `revise_and_repost` is the clean path.
- **Roster size**: 4–10.
- **Agent failure**: missing commenters simply reduce feedback volume; rfc continues. Missing author revision = `revise_and_repost`.
- **Blind commenting**: same rule as peer-review — commenters must not see each other's comments in phase 2.
- **Paragraph numbering**: enforced in phase 1 (re-prompt once if missing).
