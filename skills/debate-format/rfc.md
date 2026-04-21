# rfc

## Summary

An author posts a draft; participants annotate **independently and asynchronously**; an editor merges comments into a single revision. Modeled on IETF and public-sector RFC processes. Best for:

- longer-form specifications where inline comments outweigh plenary debate,
- decisions with many stakeholders whose attention is bursty,
- proposals where the right unit of feedback is a margin annotation, not a debate turn.

Scales beyond parliament's ~5-agent practical limit. RFC is the format for **asynchronous distributed review**.

## Roles

| Role | Brief |
| --- | --- |
| `author` | Posts the initial RFC. Reads merged comments and revises. |
| `commenter` | Reads the RFC and annotates it. Comments are inline, each attached to a specific quote from the RFC. |
| `editor` | Merges all comments into a single annotated RFC. Does not opine — their job is to organize, de-duplicate, and surface themes. |

Minimum: 1 author + 2 commenters + editor = 4. Typical: 1 + 3–6 + 1 = 5–8. Max: no hard cap, but past ~10 commenters the editor's workload grows superlinearly.

## Phases

### 1. Draft — **sequential**, single turn

Role: `author`.

Prompt:

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

Output contract: free text, proposal section paragraphs are numbered `¶N`.

### 2. Comment — **parallel**

Roles: all `commenter`s.

Prompt:

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

### 3. Merge — **sequential**, single turn

Role: `editor`.

Prompt:

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

### 4. Revision — **sequential**, single turn

Role: `author`.

Prompt:

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

### 5. Finalization — **sequential**, single turn

Role: `editor`.

Prompt:

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

## Termination

- After phase 5.
- If disposition is `revise_and_repost`, user may re-invoke the RFC format on the new draft.

## Defaults

- **Rounds**: 1. Multiple comment rounds are expensive; if needed, explicit `revise_and_repost` is the clean path.
- **Roster size**: 4–10.
- **Agent failure**: missing commenters simply reduce feedback volume; RFC continues. Missing author revision = `revise_and_repost`.
- **Blind commenting**: commenters must not see each other's comments in phase 2 (same rule as peer-review).
- **Paragraph numbering**: if the author doesn't number paragraphs, the orchestrator re-prompts once before accepting the draft.
