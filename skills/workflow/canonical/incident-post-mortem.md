---
name: incident-post-mortem
description: Reconstruct timeline, find root causes adversarially, draft remediations.
default_roster:
  lead: claude
  witnesses: [codex, gemini, kimi]
  attackers: [codex, kimi]
  defender: claude
  judge: gemini
default_budget:
  wall_clock_sec: 3600
  total_tokens: 500000
---

# incident-post-mortem

A blameless post-mortem structured in three acts: understand what happened, find systemic causes, propose fixes. Each act uses a different format because each answers a different question.

Appropriate when you have logs, user reports, or a narrative of an incident and want a structured review that does not fingerpoint but does extract durable learnings.

## Stages

### 1. reconstruct

- **Format:** `oracle`
- **Roster:**
  - `questioner`: `{lead}` (poses what-actually-happened questions)
  - `expert`: each of `{witnesses}` (domains: timeline, impact, detection — each expert reads the same incident report but answers from one angle)
  - `synthesizer`: `{lead}`
- **Input:** original user task — usually an incident report or raw logs.
- **Output bindings:**
  - `timeline` ← `verdict.md section "Key answers"`
  - `known_gaps` ← `verdict.md section "What we still don't know"`
- **Checkpoint:** `optional`.

### 2. find root causes

- **Format:** `red-team`
- **Roster:**
  - `attacker`: each of `{attackers}` (each attacker finds *different* systemic causes, not just immediate triggers)
  - `defender`: `{defender}` (responds by identifying which were root causes vs. contributing factors)
  - `judge`: `{judge}`
- **Input:** `timeline`, `known_gaps`.
- **Output bindings:**
  - `root_causes` ← `verdict.md section "Strongest attacks"` (attacks that the defender labeled as root causes)
  - `contributing_factors` ← `verdict.md section "Effective defenses"` (attacks judged non-root)
  - `ruling` ← `fenced-json.ruling`
- **Checkpoint:** `required` — team reviews the root-cause analysis before committing to remediations.

### 3. remediations

- **Format:** `committee`
- **Roster:**
  - `member`: `{lead}`
  - `editor`: `{lead}`
- **Input:** `root_causes`, `contributing_factors`, `timeline`.
- **Output bindings:**
  - `remediation_plan` ← `verdict.md body`
- **Checkpoint:** none — user reviews the final plan themselves.

## Branching

None.

## Failure modes

- **Stage 1 has many known_gaps**: stage 2's red-team prompt is explicitly told to flag findings contingent on the gaps.
- **Stage 2 ruling is `fails`**: this is unusual for a post-mortem; record it verbatim and let stage 3 decide how to frame it.
- **Any stage fails**: post-mortems are historical reconstructions, not decisions — partial output is still valuable. Write what we have and flag the gap.

## Verdict shape

- `workflow_verdict.md` has sections: Timeline Summary, Root Causes, Contributing Factors, Remediation Plan, Known Gaps.
- The remediation plan has at minimum one action per root cause.

## Notes

- **Blameless framing is enforced by the format briefs.** The oracle experts are asked about systems and dynamics, not individuals. The red-team attackers look for systemic causes (mechanism failures, missing safeguards), not human error.
- **The judge in stage 2 plays an unusual role**: their ruling here is less about adversarial adjudication and more about distinguishing root from contributing causes. Phrase the prompt accordingly when customizing.
