---
name: design-review
description: Explore what we need to know, draft a design, critique it in parallel, synthesize final.
mode: pipeline
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

## Expanded shape

```yaml
mode: pipeline
stages:
  - index: 1
    name: explore
    format: oracle
    roster:
      - { role: questioner, cli: "{lead}" }
      - { role: expert, cli: "{experts[0]}" }
      - { role: expert, cli: "{experts[1]}" }
      - { role: expert, cli: "{experts[2]}" }
      - { role: synthesizer, cli: "{lead}" }
    output_bindings:
      - { name: considerations, source: "verdict.md section What we now know" }
      - { name: open_questions, source: "verdict.md section What we still don't know" }
    checkpoint: optional

  - index: 2
    name: draft
    format: committee
    roster:
      - { role: member, cli: "{lead}" }
      - { role: editor, cli: "{lead}" }
    input_bindings: [considerations, open_questions]
    output_bindings:
      - { name: design_doc, source: "verdict.md body" }
    checkpoint: none

  - index: 3
    name: parallel-reviews
    parallel: true
    branches:
      - name: peer-review
        format: peer-review
        roster:
          - { role: author, cli: "{lead}" }
          - { role: reviewer, cli: "{reviewers[0]}" }
          - { role: reviewer, cli: "{reviewers[1]}" }
          - { role: reviewer, cli: "{reviewers[2]}" }
          - { role: editor, cli: "{lead}" }
        input_bindings: [design_doc]
        output_bindings:
          - { name: pr_verdict, source: "verdict.md body" }
          - { name: pr_decision, source: "fenced-json.decision" }
      - name: red-team
        format: red-team
        roster:
          - { role: attacker, cli: "{reviewers[0]}" }
          - { role: attacker, cli: "{reviewers[1]}" }
          - { role: defender, cli: "{lead}" }
          - { role: judge, cli: "{reviewers[2]}" }
        input_bindings: [design_doc]
        output_bindings:
          - { name: rt_verdict, source: "verdict.md body" }
          - { name: rt_ruling, source: "fenced-json.ruling" }
    merge_policy: wait_all
    checkpoint: conditional
    condition: "stage.bindings.pr_decision == \"reject\" || stage.bindings.rt_ruling == \"fails\""

  - index: 4
    name: synthesize
    format: committee
    roster:
      - { role: member, cli: "{lead}" }
      - { role: editor, cli: "{lead}" }
    input_bindings: [design_doc, pr_verdict, rt_verdict]
    output_bindings:
      - { name: final_design, source: "verdict.md body" }
    checkpoint: required
```

## Failure modes

- **Stage 1 reports low confidence** — pipeline continues but stage 2's prompt includes the low-confidence flag.
- **Stage 3 either branch fails entirely** — stage marked `partial`; stage 4 sees only the surviving branch's verdict.
- **Stage 3 both branches reject** — hits the conditional checkpoint; user decides whether to continue to synthesis (documenting dissent) or abort.

## Verdict shape

The top-level `verdict.md` follows the canonical multi-stage shape in `../../meeting-note/references/verdict-schema.md`. Inside its `## Final deliverable` section, this pipeline produces:

- **Final design** — the consolidated design doc from stage 4.
- **Review summaries** — links to both review branches' verdicts.
- **Review dissent** — populated only when a branch rejected; lists the rejecting branch's key points.
