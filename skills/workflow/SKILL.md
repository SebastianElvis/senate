---
name: workflow
description: Orchestrates multi-stage debate pipelines — sequences of debate formats chained together with handoff rules, optional human checkpoints, and resumability across time. Use when a decision requires more than one debate (e.g., RFC → review → vote → synthesis), or when the user names a canonical workflow like "rfc-pipeline", "design-review", "bill-to-law", "incident-post-mortem".
---

# workflow — multi-stage governance

Most real decisions are pipelines. A PR becomes merged by: proposal → security review → code review → approval → merge. A spec becomes canonical by: draft → peer review → revision → editorial acceptance. An incident is closed by: detection → investigation → postmortem → remediation.

The `workflow` skill chains debate formats into named pipelines. Each **stage** is a format invocation; each **handoff** specifies how one stage's verdict becomes the next stage's input. Stages can pause for user approval, branch in parallel, and merge back.

A workflow is itself just a markdown file describing its stages. Orchestrator reads it and runs each stage in order.

## When to trigger

Activate when:

- The user names a canonical workflow (`rfc-pipeline`, `design-review`, `bill-to-law`, `incident-post-mortem`).
- The user describes a multi-step decision process (*"draft an RFC, have it reviewed, then vote on it"*).
- The user asks to chain two or more debates (*"run a brainstorm, then take the top option to a parliament"*).
- A `senate` run completes and the user asks for the "next step" (e.g., after an oracle, a committee to draft the actual doc).

If the user wants a single debate, use `senate` directly — not workflow.

## Workflow file structure

A workflow lives in `canonical/<name>.md` (shipped) or the user's workspace at `.senate/workflows/<name>.md` (custom).

Frontmatter + a `## Stages` section:

```markdown
---
name: rfc-pipeline
description: Draft → review → revise → accept
default_roster:
  author: claude
  reviewers: [codex, gemini, kimi]
  editor: claude
---

## Stages

### 1. draft

- **Format:** committee (single member + editor)
- **Roster:** author only (`member: {author}`, `editor: {author}`)
- **Input:** task from user
- **Output binding:** `draft_doc` ← `verdict.md` body
- **Checkpoint:** optional — `draft_approved`, user may revise before continuing

### 2. review

- **Format:** rfc
- **Roster:** `author: {author}`, `commenters: {reviewers}`, `editor: {editor}`
- **Input:** `draft_doc`
- **Output binding:** `annotated_doc` ← `verdict.md` body, `resolution_rate` ← fenced-json.resolution_rate
- **Checkpoint:** none

### 3. synthesize

- **Format:** committee (author revises based on annotated_doc)
- **Roster:** `member: {author}`, `editor: {editor}`
- **Input:** `annotated_doc`
- **Output binding:** `final_doc` ← `verdict.md` body
- **Checkpoint:** required — `final_doc_accepted` before publication
```

## Concepts

### Bindings

Each stage declares **output bindings**: named values extracted from its verdict. Later stages reference these by name (`{draft_doc}`). Bindings are the narrow interface between stages — richer than "just pass the whole verdict".

Binding sources:

- `verdict.md body` — the full markdown verdict.
- `verdict.md section <name>` — extract a named section.
- `fenced-json.<field>` — the trailing structured contract (votes, dispositions, etc.).
- `transcript.<role>.last` — the last turn of a named role.

### Handoffs

A stage's input is constructed from the workflow's binding table plus the original user task. Build the input prompt for stage N as:

```
You are executing stage {N}: {stage_name} of the {workflow_name} workflow.

Original task: {user_task}

Bindings available from prior stages:
{for each binding: name, source stage, value}

Run your {format} process using the bindings as your working material.
```

### Checkpoints

A stage with `checkpoint: required` pauses after completion. The orchestrator writes a checkpoint state file (see `CHECKPOINTS.md`) and surfaces the current verdict to the user. User confirms continue / revise / abort.

### Branches

A workflow may fan out into parallel sub-pipelines. See `BRANCHING.md`.

### Time-spanning

A workflow may pause and resume days later. See `TIMELINE.md`.

## Steps to run a workflow

1. **Read the workflow file.** Canonical workflows under `canonical/` or user's `.senate/workflows/`.
2. **Bind the roster.** Combine workflow defaults, user overrides, and per-stage roster specs. Validate all CLIs exist and are authenticated.
3. **Mint the run dir.** `.senate/workflows/<workflow-name>-<ts>/` with subdirectories `stages/<N>-<stage-name>/`. Each stage's debate run lives in its stage subdir (full senate run layout).
4. **Write `workflow_state.json`** (see `TIMELINE.md`): stage index, bindings so far, status.
5. **For each stage**: build the input, invoke the format (re-using senate's machinery), record the verdict, extract bindings, update `workflow_state.json`.
6. **If a stage is a checkpoint**, pause and return control. User resumes with `senate resume-workflow <workflow-run-id>`.
7. **On last stage**, write `workflow_verdict.md` — a top-level summary that stitches the stage verdicts into a coherent narrative.

## Workspace layout

```
<cwd>/.senate/workflows/
  rfc-pipeline-2026-04-20-1500/
    workflow.md                       # copy of the workflow spec used
    workflow_state.json               # current state (see TIMELINE.md)
    bindings.json                     # current binding table
    workflow_verdict.md               # final summary (after last stage)
    stages/
      1-draft/
        ...full senate run layout...
      2-review/
        ...
      3-synthesize/
        ...
```

Sub-stage debate runs follow the workspace spec in `../senate/WORKSPACE.md`.

## Failure handling

- **Stage fails** (budget exhaustion, all contracts violated, etc.): write partial stage verdict, mark workflow as `stalled`, surface to user. User can resume with overrides.
- **Invalid binding** (a referenced binding doesn't exist): stop at the failing stage, don't guess.
- **Checkpoint reject**: user may revise the prior stage's verdict (edit `verdict.md` manually) and resume, or abort.

## Budget

Per-stage budget is declared in the workflow file (or defaults apply per `../senate/BUDGET.md`). The sum should not exceed a global workflow cap — enforced at stage entry.

## Canonical workflows shipped

| Workflow | File | Pipeline |
| --- | --- | --- |
| `rfc-pipeline` | `canonical/rfc-pipeline.md` | committee → rfc → committee (finalize) |
| `design-review` | `canonical/design-review.md` | oracle (explore) → committee (draft) → peer-review (critique) → committee (finalize) |
| `bill-to-law` | `canonical/bill-to-law.md` | committee (draft) → rfc (public comment) → parliament (vote) → committee (final form) |
| `incident-post-mortem` | `canonical/incident-post-mortem.md` | oracle (timeline) → red-team (find root causes) → committee (remediations) |

## Files in this skill

- `SKILL.md` — this file.
- `CHECKPOINTS.md` — human-in-the-loop pause/resume.
- `BRANCHING.md` — parallel sub-pipelines.
- `TIMELINE.md` — time-spanning runs and resumability.
- `canonical/<name>.md` — the four shipped pipelines.

## Adding a workflow

Copy `canonical/rfc-pipeline.md` as a template, edit stages and bindings, drop into `.senate/workflows/` (user-local) or under `canonical/` (to contribute upstream). No code changes needed.

## Relation to other skills

- **`senate`** runs a single debate. `workflow` runs many.
- **`invoke-format`** composes debates within a single format's turn (micro). `workflow` composes debates across stages (macro).
- **`senate-eval`** can run fixture workflows by treating a workflow as a giant fixture — same scoring machinery.
