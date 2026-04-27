---
name: bill-to-law
description: Draft a proposal, solicit public comments, put it to a parliamentary vote, finalize.
mode: pipeline
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

Longer than other multi-stage formats (~3 hours wall-clock) because of the public comment phase.

## Expanded shape

```yaml
mode: pipeline
stages:
  - index: 1
    name: draft-bill
    format: committee
    roster:
      - { role: member, cli: "{sponsor}" }
      - { role: editor, cli: "{sponsor}" }
    output_bindings:
      - { name: bill_text, source: "verdict.md body" }
      - { name: bill_title, source: "verdict.md section title" }
    checkpoint: optional

  - index: 2
    name: public-comment
    format: rfc
    roster:
      - { role: author, cli: "{sponsor}" }
      - { role: commenter, cli: "{public[0]}" }
      - { role: commenter, cli: "{public[1]}" }
      - { role: commenter, cli: "{public[2]}" }
      - { role: editor, cli: "{sponsor}" }
    input_bindings: [bill_text]
    output_bindings:
      - { name: public_feedback, source: "verdict.md body" }
      - { name: revised_bill, source: "verdict.md section Final RFC" }
      - { name: concerns, source: "verdict.md section Outstanding concerns" }
      - { name: resolution_rate, source: "fenced-json.resolution_rate" }
    checkpoint: conditional
    condition: "stage.bindings.resolution_rate < 0.5"

  - index: 3
    name: parliamentary-vote
    format: parliament
    roster:
      - { role: mp_pro, cli: "{parliament_mps[0]}" }
      - { role: mp_con, cli: "{parliament_mps[1]}" }
      - { role: mp_neutral, cli: "{parliament_mps[2]}" }
      - { role: speaker, cli: "{speaker}" }
    input_bindings: [revised_bill, concerns]
    output_bindings:
      - { name: vote_tally, source: "fenced-json.tally" }
      - { name: vote_outcome, source: "fenced-json.outcome" }
      - { name: parliament_dissent, source: "verdict.md section Dissent" }
    checkpoint: required

  - index: 4
    name: final-form
    format: committee
    roster:
      - { role: member, cli: "{sponsor}" }
      - { role: editor, cli: "{sponsor}" }
    input_bindings: [revised_bill, parliament_dissent, vote_outcome]
    output_bindings:
      - { name: final_law, source: "verdict.md body" }
    checkpoint: none
```

## Failure modes

- **Vote fails (stage 3)** — user at the checkpoint decides whether to archive the failed bill or send it back to stage 1 for redrafting. Pipeline aborts either way; re-running is a fresh invocation.
- **Public comment `resolution_rate` very low** — pipeline continues but parliament is explicitly told the bill had poor public reception.

## Verdict shape

The top-level `verdict.md` follows the canonical multi-stage shape in `../../meeting-note/references/verdict-schema.md`. Inside its `## Final deliverable` section, this pipeline produces:

- **On a passed vote:** Final Law Text, Vote Record, Dissent, Public Comment Summary.
- **On a failed vote:** Failed Bill, Reasons for Failure, Recommendations for Re-draft.

## Notes

This is a more ceremonial template — it spends more tokens than it strictly needs to for many decisions. Use when the decision is high-stakes and the social legitimacy of "this went through process X" matters.
