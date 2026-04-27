# Multi-stage agendas

Most real decisions are pipelines, not single debates. A spec becomes canonical by `draft → peer review → revision → editorial acceptance`. An incident is closed by `detection → investigation → postmortem → remediation`. The planner expresses these as multi-stage agendas: an ordered list of stages, each a format invocation, with named **bindings** flowing between them.

This used to live in a separate `workflow` skill. It is now part of agenda planning because the moderator runs whatever the agenda says — single-stage or multi-stage — through the same loop.

## When to plan multiple stages

Strong signals from the user task:

- **Pipeline language:** "draft, then review, then merge", "first explore, then design, then critique".
- **Two distinct deliverables:** "produce a spec **and** validate it", "decide approach **and** write up the rationale".
- **Time-spanning intent:** "RFC over the next week", "open it for comments and revisit Friday".
- **Explicit naming of a multi-stage pipeline:** `rfc-pipeline`, `design-review`, `bill-to-law`, `incident-post-mortem` — see `../formats/` (multi-stage pipelines live alongside single-stage formats; pipeline files have `mode: pipeline` in their frontmatter).

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

### Worked example: rfc-pipeline

```yaml
stages:
  - index: 1
    name: draft
    format: committee
    roster:
      - { role: member, cli: claude }
      - { role: editor, cli: claude }
    output_bindings:
      - { name: draft_doc, source: "verdict.md body" }

  - index: 2
    name: review
    format: rfc
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
    format: committee
    roster:
      - { role: member, cli: claude }
      - { role: editor, cli: claude }
    input_bindings: [annotated_doc, draft_doc]
    output_bindings:
      - { name: final_doc, source: "verdict.md body" }
    checkpoint: required
```

Each later stage sees its `input_bindings` plus the original task. Nothing else.

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
1. oracle (explore the terrain)
2. parliament (vote on a direction informed by the oracle's synthesis)
```

### Draft → review → finalize

```
1. committee (draft)
2. peer-review or rfc (review)
3. committee (synthesize)
```

### Investigate → diagnose → remediate

```
1. oracle (timeline reconstruction)
2. red-team (find root causes)
3. committee (write remediations)
```

### Design → critique → revise

```
1. consensus (converge on a design)
2. red-team (attack it)
3. consensus (revise informed by the attacks)
```

See `../formats/<name>.md` (the pipeline-flavor entries: `rfc-pipeline`, `design-review`, `bill-to-law`, `incident-post-mortem`) for fully fleshed-out templates.

## Re-planning mid-run

When the moderator calls `debate-agenda` mid-run for a re-plan (a stage failed, the user changed direction, a checkpoint rejected), the planner may:

- **Insert** a stage (e.g., add a `committee` stage to synthesize a stalled `rfc`).
- **Delete** a remaining stage (e.g., user decided not to publish, drop the final `committee`).
- **Modify** a roster (e.g., replace a CLI that kept refusing).

Every re-plan appends a `## Revisions` entry. Stages that have already completed are immutable.

## Failure modes

- **Stage fails** (budget, contracts, all agents refused) → mark stage `stalled` and surface to user. Do not auto-skip.
- **Invalid binding** (a referenced binding doesn't exist) → planner caught this in validation; if it slipped through, moderator pauses immediately.
- **Checkpoint reject** → user may revise the prior stage's verdict (manually edit `verdict.md`); re-extract bindings on resume.

## Single-stage is not a special case

A single-stage agenda is a multi-stage agenda with one stage. The moderator does not have two code paths. This is intentional — it keeps the moderator simple and uniformly testable.
