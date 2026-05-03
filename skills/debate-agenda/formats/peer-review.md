# peer-review

## Defining commitment

**Multiple isolated judgments combined by a non-participating editor.** An author submits work; reviewers critique blindly and in parallel — they **must not see each other's reviews while producing them**; the author revises once; the editor adjudicates. Independence-of-error is the point — two reviewers agreeing is signal only if they couldn't have been influenced by each other.

## Boundary conditions

- Reviewers work in parallel without cross-talk. The moderator enforces transcript-slice scoping so each reviewer sees only the submission, never other reviewers' responses.
- At least 2 reviewers. Independence is meaningful only with multiples.
- The editor is a separate role and never reviews content during the parallel phase.
- Output is the editor's decision (accept / minor_revision / major_revision / reject).
- **No-re-engagement rule**: only the original `author` revises; reviewers do not re-engage in the revision round. Reviewer outputs are one-shot.

## Anti-drift fence

| If the task is… | The right primitive is… |
| --- | --- |
| "Peers iterate on a shared draft" | committee |
| "Sides argue with an arbiter" | court |
| "Find ways this could fail" | red-team |
| "Cast a vote" | parliament |
| "Generate options" | brainstorm |

## Summary

Best for structured independent critique of a submission — design docs, specs, RFCs, draft proposals. Modeled on academic peer review.

## Roles

| Role | Brief |
| --- | --- |
| `author` | Presents the work. Responds to reviewer comments. Revises. |
| `reviewer` | Reads the submission and produces a structured review. 2–4 reviewers, working independently; must not see each other's reviews until after revision. |
| `editor` | Reads all reviews + revision, issues the final decision. |

Minimum: 1 author + 2 reviewers + editor = 4. Typical: 1 + 3 + 1 = 5.

## Phases

### 1. Submission — **sequential**, single turn

Role: `author`.

```
You are the author submitting for peer review. The task is:

{task}

Produce your initial submission. Include whatever sections the task requires. Be complete — this is what reviewers will critique.

At the end, add an "Author's notes" section flagging any parts you are least confident about.
```

Output contract: free text.

### 2. Review — **parallel** (strict isolation)

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

Output contract: free text (review body) + fenced json block (machine-readable recommendation). The json block is the contract. On contract failure, the per-turn subagent re-prompts once if the turn's retry budget is still available; fallback recommendation is `major_revision`.

### 3. Revision — **sequential**, single turn

Role: `author`. **No-re-engagement applies**: only the author revises; reviewers do not re-engage in this round.

```
You are the author. All reviewer comments are now visible.

{transcript_slice: reviews}

Produce the revised submission. For each major concern from each reviewer, explicitly indicate: addressed (cite where), declined (with reason), or deferred (with rationale).

If ≥2 reviewers agree on a major concern, you should either address it or offer a strong-evidence rebuttal.
```

Output contract: revised submission + explicit response-to-reviewers section.

### 4. Editor's decision — **sequential**, single turn

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

On contract failure, fallback to `major_revision`. The editor's decision becomes the synthesis content. The moderator writes it to `stages/<N>-<name>/verdict.md` (schema in `../../meeting-note/references/verdict-schema.md`); the scribe folds it into the run-wide `notes.md`.

## Termination

- After phase 4. No extended revision loop — if `major_revision` or `reject`, that terminates the run.
- The user may manually re-invoke peer-review on the revised submission as a new run.

## Defaults

- **Rounds**: 1 (submission + reviews + revision + decision).
- **Roster size**: 4–5.
- **Agent failure**: missing review = that reviewer does not contribute; if ≥2 reviewers are missing, editor issues `major_revision` with a "remanded due to insufficient review coverage" note. The missing reviewers' turns are recorded in `transcript.jsonl` with their respective `error` codes; the scribe surfaces a failure rollup in `notes.md`.
- **Blind review**: reviewers must not see each other's turns in phase 2 (moderator enforces via transcript scoping).
