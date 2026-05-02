# Multi-stage agendas

Most real decisions are pipelines, not single debates. A spec becomes canonical by `draft → peer review → revision → editorial acceptance`. An incident is closed by `detection → investigation → postmortem → remediation`. The planner expresses these as multi-stage agendas: an ordered list of stages, each a format invocation, with named **bindings** flowing between them.

This used to live in a separate `workflow` skill. It is now part of agenda planning because the moderator runs whatever the agenda says — single-stage or multi-stage — through the same loop.

## When to plan multiple stages

Strong signals from the user task:

- **Pipeline language:** "draft, then review, then merge", "first explore, then design, then critique".
- **Two distinct deliverables:** "produce a spec **and** validate it", "decide approach **and** write up the rationale".
- **Time-spanning intent:** "RFC over the next week", "open it for comments and revisit Friday".
- **Explicit naming of a multi-stage pipeline:** `rfc-pipeline`, `design-review`, `bill-to-law`, `incident-post-mortem` — use the canonical recipes below. Pipeline recipes are stage sequences, not separate files in `../formats/`.

If the user asks for a single debate, do not invent stages.

## Bindings — the narrow interface between stages

Each stage declares **output bindings** (named values extracted from its verdict) and **input bindings** (named values it consumes from prior stages).

Bindings are the only data that flows between stages. The transcript and full verdict of stage N are still on disk and the moderator may reference them, but downstream stages **see only the bound values plus the original task**. This forces the planner to decide explicitly what each stage's deliverable is.

### Output binding sources

A binding is extracted from one of:

| Source | Meaning |
| --- | --- |
| `verdict.md body` | The full markdown verdict of this stage. |
| `verdict.md section <name>` | A named section of the verdict (e.g., "Decision", "Rationale"). |
| `fenced-json.<field>` | The trailing structured contract (votes, dispositions, confidence, etc.). |
| `transcript.<role>.last` | The last turn of a named role (e.g., the editor's final draft). |

## Canonical pipeline recipes

Pipeline recipes expand into `agenda.md` with `mode: pipeline`. They do not have standalone format files; every stage's `format` points to one of the five primitive files in `../formats/`.

### rfc-pipeline

Use for documents that need draft → distributed comment → revision → acceptance.

Defaults: `author: claude`, `reviewers: [codex, gemini, kimi]`, `editor: claude`; budget `wall_clock_sec: 3600`, `total_tokens: 500000`.

```yaml
stages:
  - index: 1
    name: draft
    format: workshop
    preset: committee
    roster:
      - { role: member, cli: claude }
      - { role: editor, cli: claude }
    output_bindings:
      - { name: draft_doc, source: "verdict.md body" }

  - index: 2
    name: review
    format: panel
    preset: rfc
    roster:
      - { role: author, cli: claude }
      - { role: commenter, cli: codex }
      - { role: commenter, cli: gemini }
      - { role: commenter, cli: kimi }
      - { role: editor, cli: claude }
    input_bindings: [draft_doc]
    output_bindings:
      - { name: annotated_doc, source: "verdict.md body" }
      - { name: resolution_rate, source: "fenced-json.resolution_rate" }

  - index: 3
    name: synthesize
    format: workshop
    preset: committee
    roster:
      - { role: member, cli: claude }
      - { role: editor, cli: claude }
    input_bindings: [annotated_doc, draft_doc]
    output_bindings:
      - { name: final_doc, source: "verdict.md body" }
    checkpoint: required
```

Each later stage sees its `input_bindings` plus the original task. Nothing else.

Verdict shape inside `## Final deliverable`: Final Document, Process summary, Resolution rate.

Failure notes: if review disposition is `withdrawn`, pause at the conditional checkpoint; if `resolution_rate < 0.5`, continue but warn the synthesize stage.

### design-review

Use for technical designs where missing the problem shape is expensive and the draft needs both independent review and adversarial pressure.

Defaults: `lead: claude`, `experts: [codex, gemini, kimi]`, `reviewers: [codex, gemini, kimi]`; budget `wall_clock_sec: 5400`, `total_tokens: 800000`.

```yaml
stages:
  - index: 1
    name: explore
    format: panel
    preset: oracle
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
    format: workshop
    preset: committee
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
        format: panel
        preset: peer-review
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
        format: court
        preset: red-team
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
    format: workshop
    preset: committee
    roster:
      - { role: member, cli: "{lead}" }
      - { role: editor, cli: "{lead}" }
    input_bindings: [design_doc, pr_verdict, rt_verdict]
    output_bindings:
      - { name: final_design, source: "verdict.md body" }
    checkpoint: required
```

Verdict shape inside `## Final deliverable`: Final design, Review summaries, Review dissent if any branch rejected.

Failure notes: if either review branch fails, mark stage 3 `partial` and let synthesis consume the surviving branch; if both branches reject, pause at the conditional checkpoint.

### bill-to-law

Use for policy-shaped decisions where legitimacy of process matters: draft, public comment, parliamentary vote, final form.

Defaults: `sponsor: claude`, `public: [codex, gemini, kimi]`, `parliament_mps: [codex, gemini, kimi]`, `speaker: claude`; budget `wall_clock_sec: 7200`, `total_tokens: 1000000`.

```yaml
stages:
  - index: 1
    name: draft-bill
    format: workshop
    preset: committee
    roster:
      - { role: member, cli: "{sponsor}" }
      - { role: editor, cli: "{sponsor}" }
    output_bindings:
      - { name: bill_text, source: "verdict.md body" }
      - { name: bill_title, source: "verdict.md section title" }
    checkpoint: optional

  - index: 2
    name: public-comment
    format: panel
    preset: rfc
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
    format: workshop
    preset: committee
    roster:
      - { role: member, cli: "{sponsor}" }
      - { role: editor, cli: "{sponsor}" }
    input_bindings: [revised_bill, parliament_dissent, vote_outcome]
    output_bindings:
      - { name: final_law, source: "verdict.md body" }
    checkpoint: none
```

Verdict shape inside `## Final deliverable`: on passed vote, Final Law Text, Vote Record, Dissent, Public Comment Summary; on failed vote, Failed Bill, Reasons for Failure, Recommendations for Re-draft.

Failure notes: if vote fails, the checkpoint decides whether to archive or redraft; if public comment resolution is low, parliament sees that warning.

### incident-post-mortem

Use for blameless incident review: reconstruct timeline, identify systemic causes, draft remediations.

Defaults: `lead: claude`, `witnesses: [codex, gemini, kimi]`, `attackers: [codex, kimi]`, `defender: claude`, `judge: gemini`; budget `wall_clock_sec: 3600`, `total_tokens: 500000`.

```yaml
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

Verdict shape inside `## Final deliverable`: Timeline Summary, Root Causes, Contributing Factors, Remediation Plan, Known Gaps.

Failure notes: preserve partial output if a stage fails; post-mortems are historical reconstruction, so incomplete but cited findings can still be useful.

## Handoff prompt template

The moderator builds each stage's input prompt as:

```
You are executing stage {N}: {stage_name} of the {agenda.run_id} pipeline.

Original task: {agenda.task}

Bindings available from prior stages:
{for each input binding: name, source stage, value}

Run your {stage.format} process using the bindings as your working material.
```

The `## Why this format` and `## Why this roster` paragraphs from the agenda body are also pasted in, so the participating agents share the planner's intent.

## Common multi-stage shapes

### Explore → decide

```
1. panel:oracle (explore the terrain)
2. parliament (vote on a direction informed by the oracle's synthesis)
```

### Draft → review → finalize

```
1. workshop:committee (draft)
2. panel:peer-review or panel:rfc (review)
3. workshop:committee (synthesize)
```

### Investigate → diagnose → remediate

```
1. panel:oracle (timeline reconstruction)
2. court:red-team (find root causes)
3. workshop:committee (write remediations)
```

### Design → critique → revise

```
1. workshop:consensus (converge on a design)
2. court:red-team (attack it)
3. workshop:consensus (revise informed by the attacks)
```

Use the canonical recipes above when the user names a pipeline directly. For unnamed pipelines, compose the common shapes into an explicit stage list rather than inventing a new format file.

## Re-planning mid-run

When the moderator calls `debate-agenda` mid-run for a re-plan (a stage failed, the user changed direction, a checkpoint rejected), the planner may:

- **Insert** a stage (e.g., add a `workshop:committee` stage to synthesize a stalled `panel:rfc`).
- **Delete** a remaining stage (e.g., user decided not to publish, drop the final `workshop:committee`).
- **Modify** a roster (e.g., replace a CLI that kept refusing).

Every re-plan appends a `## Revisions` entry. Stages that have already completed are immutable.

## Failure modes

- **Stage fails** (budget, contracts, all agents refused) → mark stage `stalled` and surface to user. Do not auto-skip.
- **Invalid binding** (a referenced binding doesn't exist) → planner caught this in validation; if it slipped through, moderator pauses immediately.
- **Checkpoint reject** → user may revise the prior stage's verdict (manually edit `verdict.md`); re-extract bindings on resume.

## Single-stage is not a special case

A single-stage agenda is a multi-stage agenda with one stage. The moderator does not have two code paths. This is intentional — it keeps the moderator simple and uniformly testable.
