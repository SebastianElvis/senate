---
name: design-review
description: Explore what we need to know, draft a design, critique it in parallel, synthesize final.
default_roster:
  lead: claude
  experts: [codex, gemini, kimi]
  reviewers: [codex, gemini, kimi]
default_budget:
  wall_clock_sec: 5400
  total_tokens: 800000
---

# design-review

A fuller process than `rfc-pipeline`: starts with an oracle phase to surface considerations the design lead may not have considered, then drafts, then parallel peer review + red-team, then synthesizes. Use for technical designs where getting the scope wrong at the start is expensive.

Takes ~2–3 hours wall-clock.

## Stages

### 1. explore

- **Format:** `oracle`
- **Roster:**
  - `questioner`: `{lead}`
  - `expert`: each of `{experts}` (domains: security, performance, maintainability)
  - `synthesizer`: `{lead}`
- **Input:** original user task.
- **Output bindings:**
  - `considerations` ← `verdict.md section "What we now know"`
  - `open_questions` ← `verdict.md section "What we still don't know"`
- **Checkpoint:** `optional` — user may inject additional considerations.

### 2. draft

- **Format:** `committee`
- **Roster:**
  - `member`: `{lead}`
  - `editor`: `{lead}`
- **Input:** `considerations`, `open_questions`, original task.
- **Output bindings:**
  - `design_doc` ← `verdict.md body`
- **Checkpoint:** none.

### 3. parallel reviews

- **Parallel:** `true`
- **Branches:**

  - **peer-review**
    - Format: `peer-review`
    - Roster: `author={lead}`, `reviewer`=each of `{reviewers}`, `editor={lead}`
    - Input: `design_doc`
    - Output bindings: `pr_verdict` ← `verdict.md body`, `pr_decision` ← `fenced-json.decision`

  - **red-team**
    - Format: `red-team`
    - Roster: `attacker`=first 2 of `{reviewers}`, `defender={lead}`, `judge`=last of `{reviewers}`
    - Input: `design_doc`
    - Output bindings: `rt_verdict` ← `verdict.md body`, `rt_ruling` ← `fenced-json.ruling`

- **Merge policy:** `wait_all`
- **Checkpoint:** `conditional` on `pr_decision == "reject" || rt_ruling == "fails"` — pause if either review rejected the design.

### 4. synthesize

- **Format:** `committee`
- **Roster:**
  - `member`: `{lead}`
  - `editor`: `{lead}`
- **Input:** `design_doc`, `pr_verdict`, `rt_verdict`.
- **Output bindings:**
  - `final_design` ← `verdict.md body`
- **Checkpoint:** `required` — user confirms final design.

## Failure modes

- **Stage 1 reports low confidence**: workflow continues but stage 2 prompt includes the low-confidence flag.
- **Stage 3 either branch fails entirely**: stage marked `partial`; stage 4 sees only the surviving branch's verdict.
- **Stage 3 both branches reject**: hit the conditional checkpoint; user decides whether to continue to synthesis anyway (documenting dissent) or abort.

## Verdict shape

- `workflow_verdict.md` summarizes the final design and references both review branches' verdicts.
- If either branch rejected, `workflow_verdict.md` contains a "Review dissent" section with the rejecting branch's key points.
