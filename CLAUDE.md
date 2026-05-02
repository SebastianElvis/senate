# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A bundle of **Agent Skills** ([agentskills.io spec](https://agentskills.io/specification)) — no compiled code, no test runner, no package manifest. Everything is Markdown. The "build" is the directory layout itself; agents consume it via `npx skills add SebastianElvis/senate` or by symlinking into their skills directory.

There are no lint/test/build commands. Validation is conformance to the Agent Skills spec — use [`skills-ref validate ./skills/<name>`](https://github.com/agentskills/agentskills/tree/main/skills-ref) on any skill you change.

For background on skill design, see [The Complete Guide to Building Skills for Claude](https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf).

## Architecture

Five skills compose a debate lifecycle. Reading any one skill in isolation is misleading — the lifecycle is the architecture.

```
senate (orchestrator)
  → debate-agenda  (planner)   — writes agenda.md
  → moderate-debate (moderator) — runs turns from agenda.md, writes transcript.jsonl
  → meeting-note   (scribe)    — writes verdict.md + meeting-notes.md
invoke-agent (primitive)       — per-CLI invocation playbooks; called by moderate-debate
```

Canonical role names (used everywhere — keep them consistent):

- **Orchestrator** = `senate` skill. Lifecycle conductor.
- **Planner** = `debate-agenda` skill. Produces `agenda.md`.
- **Moderator** = `moderate-debate` skill. Runs turns.
- **Scribe** = `meeting-note` skill. Writes the user-facing summary.
- **Synthesizer** = the in-format role (judge/speaker/editor/arbiter) for one stage's synthesis. **Distinct from the scribe.**
- **Format** = a debate playbook in `skills/debate-agenda/formats/`. Single-stage = "primitive"; multi-stage = "pipeline" (`mode: pipeline`).
- **Playbook** = a per-CLI invocation reference in `skills/invoke-agent/references/`.
- **Run** = one execution; lives at `<cwd>/.senate/runs/<id>/`.

### Run-dir contract (load-bearing)

All runtime state lives at `<cwd>/.senate/runs/<id>/` — **never** inside the skill repo. The skill directory is read-only at runtime. Files: `agenda.md`, `context.md` (shared scratchpad), `agents/<cli>.md` (per-CLI private memory), `transcript.jsonl`, `verdict.md`, `meeting-notes.md`, `state.json`, optional `stages/<N>-<name>/` for pipelines, optional `failures.md`. The schema is normative — all five skills read/write against it. See `skills/senate/references/workspace.md`.

### Cross-skill references

Skills reference each other with relative paths like `../moderate-debate/references/budget.md`. This is intentional: the bundle ships and installs together, so cross-skill paths are stable. Keep them.

### Progressive disclosure

The spec recommends `SKILL.md` stay under 500 lines / 5000 tokens. Detail lives in `references/` (loaded on demand) and `formats/` (loaded when the planner picks that format). When you add reference content, also add a contextual pointer from `SKILL.md` that tells the agent **when** to load it (e.g., "see `references/checkpoints.md` when resuming a paused run") — not just "see references/".

## Conventions when editing skills

- **Frontmatter**: `name` must equal the parent directory name; lowercase + hyphens only; `description` ≤ 1024 chars and should describe both *what* and *when*. `license: MIT` is set on every skill.
- **Format files** go under `skills/debate-agenda/formats/`. New single-stage formats follow `_template.md`; new pipelines follow one of `rfc-pipeline.md`, `design-review.md`, `bill-to-law.md`, or `incident-post-mortem.md`. Add a row to `formats/README.md`.
- **CLI playbooks** go under `skills/invoke-agent/references/<name>.md`. Schema (install-check, invoke, input, output, budget, quirks) is shared across all CLI files — preserve it.
- **No imperative code.** If you find yourself wanting to add a script, first check whether the same effect can be encoded as a Markdown procedure the agent follows. Scripts go in `scripts/` only when truly needed.

## Adjacent directories

- `dev/PRODUCT.md` — product vision and horizon plan. Read before making structural changes.
- `senate-eval/` — evaluation harness (in flux; revisit later — not part of the shipped skill set).
- `.context/` — workspace-local scratch (gitignored), used to coordinate with parallel Conductor agents.

## Branching / PRs

Target branch is `origin/main`. Branch names use `SebastianElvis/<concise-name>`.
