---
name: incident-post-mortem
description: Reconstruct timeline, find root causes adversarially, draft remediations.
mode: pipeline
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

## Expanded shape

```yaml
mode: pipeline
stages:
  - index: 1
    name: reconstruct
    format: panel
    preset: oracle
    roster:
      - { role: questioner, cli: "{lead}" }
      - { role: expert, cli: "{witnesses[0]}" }
      - { role: expert, cli: "{witnesses[1]}" }
      - { role: expert, cli: "{witnesses[2]}" }
      - { role: synthesizer, cli: "{lead}" }
    output_bindings:
      - { name: timeline, source: "verdict.md section Key answers" }
      - { name: known_gaps, source: "verdict.md section What we still don't know" }
    checkpoint: optional

  - index: 2
    name: root-causes
    format: court
    preset: red-team
    roster:
      - { role: attacker, cli: "{attackers[0]}" }
      - { role: attacker, cli: "{attackers[1]}" }
      - { role: defender, cli: "{defender}" }
      - { role: judge, cli: "{judge}" }
    input_bindings: [timeline, known_gaps]
    output_bindings:
      - { name: root_causes, source: "verdict.md section Strongest attacks" }
      - { name: contributing_factors, source: "verdict.md section Effective defenses" }
      - { name: ruling, source: "fenced-json.ruling" }
    checkpoint: required

  - index: 3
    name: remediations
    format: workshop
    preset: committee
    roster:
      - { role: member, cli: "{lead}" }
      - { role: editor, cli: "{lead}" }
    input_bindings: [root_causes, contributing_factors, timeline]
    output_bindings:
      - { name: remediation_plan, source: "verdict.md body" }
    checkpoint: none
```

## Failure modes

- **Stage 1 has many `known_gaps`** — stage 2's red-team prompt is explicitly told to flag findings contingent on the gaps.
- **Stage 2 ruling is `fails`** — unusual for a post-mortem; record it verbatim and let stage 3 decide how to frame it.
- **Any stage fails** — post-mortems are historical reconstructions, not decisions; partial output is still valuable. Write what we have and flag the gap.

## Verdict shape

The top-level `verdict.md` follows the canonical multi-stage shape in `../../meeting-note/references/verdict-schema.md`. Inside its `## Final deliverable` section, this pipeline produces:

- **Timeline Summary** — what happened, in order.
- **Root Causes** — the systemic causes the red-team labelled as load-bearing.
- **Contributing Factors** — non-root causes the red-team surfaced.
- **Remediation Plan** — at minimum one action per root cause.
- **Known Gaps** — what we still don't know, propagated from stage 1.

## Notes

- **Blameless framing is enforced by the format briefs.** The oracle experts are asked about systems and dynamics, not individuals. The red-team attackers look for systemic causes (mechanism failures, missing safeguards), not human error.
- **The judge in stage 2 plays an unusual role**: their ruling here is less about adversarial adjudication and more about distinguishing root from contributing causes. Phrase the prompt accordingly when customizing.
