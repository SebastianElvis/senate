---
name: bill-to-law
description: Draft a proposal, solicit public comments, put it to a parliamentary vote, finalize.
default_roster:
  sponsor: claude
  public: [codex, gemini, kimi]
  parliament_mps: [codex, gemini, kimi]
  speaker: claude
default_budget:
  wall_clock_sec: 7200
  total_tokens: 1000000
---

# bill-to-law

Models legislative process: a sponsor drafts a bill, public comments are collected, parliament votes, and a final form is produced. Appropriate for policy-shaped decisions with many stakeholders — company-wide engineering standards, cross-team conventions, principles for a codebase.

Longer than other canonical workflows (~3 hours wall-clock) because of the public comment phase.

## Stages

### 1. draft bill

- **Format:** `committee`
- **Roster:**
  - `member`: `{sponsor}`
  - `editor`: `{sponsor}`
- **Input:** original user task.
- **Output bindings:**
  - `bill_text` ← `verdict.md body`
  - `bill_title` ← `verdict.md` first `# ` header
- **Checkpoint:** `optional`.

### 2. public comment

- **Format:** `rfc`
- **Roster:**
  - `author`: `{sponsor}`
  - `commenter`: each of `{public}`
  - `editor`: `{sponsor}`
- **Input:** `bill_text`.
- **Output bindings:**
  - `public_feedback` ← `verdict.md body`
  - `revised_bill` ← `verdict.md section "Final RFC"`
  - `concerns` ← `verdict.md section "Outstanding concerns"`
- **Checkpoint:** `conditional` on `resolution_rate < 0.5` — many outstanding concerns, surface before voting.

### 3. parliamentary vote

- **Format:** `parliament`
- **Roster:**
  - `mp_pro`: first of `{parliament_mps}`
  - `mp_con`: second of `{parliament_mps}`
  - `mp_neutral`: third of `{parliament_mps}`
  - `speaker`: `{speaker}`
- **Input:** `revised_bill`, `concerns`.
- **Output bindings:**
  - `vote_tally` ← `verdict.md` section containing vote counts
  - `vote_outcome` ← extracted from verdict (pass / fail)
  - `parliament_dissent` ← `verdict.md section "Dissent"`
- **Checkpoint:** `required` — user must confirm whether to enact the passed bill or archive a failed one.

### 4. final form

- **Format:** `committee`
- **Roster:**
  - `member`: `{sponsor}`
  - `editor`: `{sponsor}`
- **Input:** `revised_bill`, `parliament_dissent`, `vote_outcome`.
- **Output bindings:**
  - `final_law` ← `verdict.md body`
- **Checkpoint:** none.

## Failure modes

- **Vote fails (phase 3)**: user at the checkpoint decides whether to archive the failed bill or send it back to stage 1 for redrafting. Workflow aborts either way; re-running is a fresh invocation.
- **Public comment resolution_rate very low**: workflow continues but parliament is explicitly told the bill had poor public reception.

## Branching

None. Legislative process is strictly sequential.

## Verdict shape

- `workflow_verdict.md` has sections: Final Law Text, Vote Record, Dissent, Public Comment Summary.
- If vote failed, `workflow_verdict.md` has sections: Failed Bill, Reasons for Failure, Recommendations for Re-draft.

## Notes

This is a more ceremonial workflow — it spends more tokens than it strictly needs to for many decisions. Use when the decision is high-stakes and the social legitimacy of "this went through process X" matters.
