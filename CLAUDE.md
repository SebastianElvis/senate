# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A bundle of **Agent Skills** ([agentskills.io spec](https://agentskills.io/specification)) — no compiled code, no test runner, no package manifest. Everything is Markdown. The "build" is the directory layout itself; agents consume it via `npx skills add SebastianElvis/senate` or by symlinking into their skills directory.

There are no lint/test/build commands. Validation is conformance to the Agent Skills spec — use [`skills-ref validate ./skills/<name>`](https://github.com/agentskills/agentskills/tree/main/skills-ref) on any skill you change.

For background on skill design, see [The Complete Guide to Building Skills for Claude](https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf). For background on designing or extending the eval harness in `evals/`, see [Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) — the harness's two-tier (deterministic + LLM-judge) structure, capability vs. regression sets, pairwise counterbalancing, and provenance fields all map to that methodology.

## Architecture

Five skills compose a debate lifecycle. Reading any one skill in isolation is misleading — the lifecycle is the architecture.

```
senate (orchestrator)
  → debate-agenda  (planner)   — writes agenda.md
  → moderate-debate (moderator) — dispatches per-turn subagents, writes transcript.jsonl
  → meeting-note   (scribe)    — writes verdict.md + meeting-notes.md
invoke-agent (primitive)       — per-CLI invocation playbooks; read inside per-turn subagents
```

Canonical role names (used everywhere — keep them consistent):

- **Orchestrator** = `senate` skill. Lifecycle conductor.
- **Planner** = `debate-agenda` skill. Produces `agenda.md`.
- **Moderator** = `moderate-debate` skill. Builds turn prompts, dispatches standalone per-turn subagents, and commits their structured results.
- **Scribe** = `meeting-note` skill. Writes the user-facing summary.
- **Synthesizer** = the in-format role (judge/speaker/editor/arbiter) for one stage's synthesis. **Distinct from the scribe.**
- **Format** = a debate playbook in `skills/debate-agenda/formats/`. Single-stage = "primitive"; multi-stage = "pipeline" (`mode: pipeline`).
- **Playbook** = a per-CLI invocation reference in `skills/invoke-agent/references/`, loaded by the per-turn subagent rather than the moderator's long-lived context.
- **Run** = one execution; lives at `<cwd>/.senate/runs/<id>/`.

### Run-dir contract (load-bearing)

All runtime state lives at `<cwd>/.senate/runs/<id>/` — **never** inside the skill repo. The skill directory is read-only at runtime. Files: `agenda.md`, `context.md` (shared scratchpad), `agents/<cli>.md` (per-CLI private memory), `agents/<cli>.<turn>.log` / `.stderr` (raw CLI artifacts written by per-turn subagents), `transcript.jsonl`, `verdict.md`, `meeting-notes.md`, `state.json`, optional `stages/<N>-<name>/` for pipelines, optional `failures.md`. The schema is normative — all five skills read/write against it. See `skills/senate/references/workspace.md`.

### Cross-skill references

Skills reference each other with relative paths like `../moderate-debate/references/budget.md`. This is intentional: the bundle ships and installs together, so cross-skill paths are stable. Keep them.

### Progressive disclosure

The spec recommends `SKILL.md` stay under 500 lines / 5000 tokens. Detail lives in `references/` (loaded on demand) and `formats/` (loaded when the planner picks that format). When you add reference content, also add a contextual pointer from `SKILL.md` that tells the agent **when** to load it (e.g., "see `references/checkpoints.md` when resuming a paused run") — not just "see references/".

## Conventions when editing skills

- **Frontmatter**: `name` must equal the parent directory name; lowercase + hyphens only; `description` ≤ 1024 chars and should describe both *what* and *when*. `license: MIT` is set on every skill.
- **Format files** go under `skills/debate-agenda/formats/`. New single-stage formats follow `_template.md`; new pipelines follow one of `rfc-pipeline.md`, `design-review.md`, `bill-to-law.md`, or `incident-post-mortem.md`. Add a row to `formats/README.md`.
- **CLI playbooks** go under `skills/invoke-agent/references/<name>.md`. Schema (install-check, invoke, input, output, budget, quirks) is shared across all CLI files — preserve it.
- **No imperative code in skills.** If you find yourself wanting to add a script under `skills/`, first check whether the same effect can be encoded as a Markdown procedure the agent follows. The one explicit exception is `evals/scripts/` — the eval harness needs deterministic graders, scorecard accounting, and CLI invocation that an agent cannot reliably perform mid-loop. Keep new code there, not in skills.

## Adjacent directories

- `dev/PRODUCT.md` — product vision and horizon plan. Read before making structural changes.
- `evals/` — evaluation harness for the senate skills (separate from the shipped bundle). Two-tier grading: deterministic checks against the run-dir contract + LLM judges via `claude -p` (uses your Claude Code OAuth — no API key). Run with `evals/run.sh [fixture-glob]`. Full design in `evals/SKILL.md`. When you change a skill, run a fixture or two before merging.
- `.context/` — workspace-local scratch (gitignored), used to coordinate with parallel Conductor agents.

## Evaluating skill changes

When you edit a skill, the eval harness is how you check you didn't regress. Quick loop:

```bash
evals/run.sh evals/fixtures/_smoke-parliament.md   # cheapest fixture; ~5 min
python3 evals/scripts/report.py                    # markdown rollup of evals/.evals/scorecard.jsonl
```

The harness loads the skills from this repo via `--plugin-dir`, so your edits are picked up without any install step. Scorecard rows include `repo_commit` + `fixture_sha256` + `claude_cli_version` so you can correlate runs to your changes. A fail in `state_terminal`, `transcript_schema`, or `fixture_assertions` usually means the skill diverged from `skills/senate/references/workspace.md`. A judge fail is a quality signal; read `judgement.reasoning` before changing the skill — sometimes the rubric is wrong.

## Branching / PRs

Target branch is `origin/main`. Branch names use `SebastianElvis/<concise-name>`.
