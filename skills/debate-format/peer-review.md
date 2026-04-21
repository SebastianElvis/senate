# peer-review

## Summary

Author submits work; reviewers critique blindly and in parallel; author revises; editor adjudicates and produces a final ruling. Modeled directly on academic peer review. Best for design docs, specs, research proposals, or anything where you want independent expert critique before accepting or revising.

Unlike court (adversarial) or parliament (voting), peer review assumes the author is acting in good faith and the reviewers are helping them make it better — or, failing that, explaining clearly why the current version isn't ready.

## Roles

| Role | Brief |
| --- | --- |
| `author` | Presents the work. Responds to reviewer comments. Revises. |
| `reviewer` | Reads the submission and produces a structured review. 2–4 reviewers, working independently; must not see each other's reviews until revision. |
| `editor` | Assigns reviewers (implicit via roster), reads all reviews + revision, issues the final decision. |

Minimum: 1 author + 2 reviewers + editor = 4. Typical: 1 + 3 + 1 = 5.

## Phases

### 1. Submission — **sequential**, single turn

Role: `author`.

Prompt:

```
You are the author submitting for peer review. The task is:

{task}

Produce your initial submission. Include whatever sections the task requires. Be complete — this is what reviewers will critique.

At the end, add an "Author's notes" section flagging any parts you are least confident about.
```

Output contract: free text.

### 2. Review — **parallel**

Roles: all `reviewer`s.

Prompt:

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

Output contract: free text (review body) + fenced json block (machine-readable recommendation). The json block is the contract. Re-prompt once on failure; fallback recommendation is `major_revision`.

### 3. Revision — **sequential**, single turn

Role: `author`.

Prompt:

```
You are the author. All reviewer comments are now visible.

{transcript_slice: reviews}

Produce the revised submission. For each major concern from each reviewer, explicitly indicate: addressed (cite where), declined (with reason), or deferred (with rationale).

If ≥2 reviewers agree on a major concern, you should either address it or offer a strong-evidence rebuttal.
```

Output contract: revised submission + explicit response-to-reviewers section.

### 4. Editor's decision — **sequential**, single turn

Role: `editor`.

Prompt:

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

Output contract: markdown with those five sections + trailing fenced json:

```json
{"decision": "accept" | "minor_revision" | "major_revision" | "reject", "revision_deadline_days": 30}
```

On contract failure, fallback to `major_revision`.

## Termination

- After phase 4. No extended revision loop — if major_revision or reject, that terminates the run with that outcome.
- The user may manually re-invoke peer-review on the revised submission as a new run.

## Defaults

- **Rounds**: 1 (submission + reviews + revision + decision). No multi-round peer review unless user explicitly asks.
- **Roster size**: 4–5.
- **Agent failure**: missing review = that reviewer does not contribute; if ≥2 reviewers are missing, editor issues `remand` and the run is flagged.
- **Blind review**: reviewers must not see each other's turns in phase 2 — orchestrator enforces this by scoping the `transcript_slice` for each reviewer to just the submission.
