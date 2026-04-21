# senate

Multi-agent debate skills for coding CLIs. Orchestrates codex, gemini, cursor, kimi, and claude through structured debate formats (parliament, court, consensus) to reach more robust answers than any single model.

## Install

```bash
npx skills add elvisage941102/senate
```

Or from a local clone:

```bash
npx skills add ./senate
```

This installs seven skills into your agent's skill directory (`.claude/skills/`, `.agents/skills/`, etc.):

| Skill | Purpose |
| --- | --- |
| `senate` | Entry point. Picks format, manages the run, drives turns, writes the verdict. |
| `invoke-agent` | Reference playbook for invoking each supported CLI. |
| `debate-format` | 11 debate formats: parliament, court, consensus, committee, peer-review, brainstorm, oracle, socratic, appeals-court, rfc, red-team. |
| `invoke-format` | Composition primitive: run one format as a sub-debate inside another's role. |
| `format-selector` | Recommends a format given a task description. |
| `workflow` | Multi-stage pipelines that chain formats (RFC → review → vote). Ships 4 canonical pipelines. |
| `senate-eval` | Evaluation harness — measures per-CLI contract compliance across fixture debates. |

## Usage

In your coding agent, ask something like:

- *"Run a **parliament** between codex, gemini, and kimi on whether to migrate this service to Rust."*
- *"Hold a **court** debate — codex prosecutes my refactor, claude defends, gemini judges."*
- *"Drive **consensus** between three models on this API design."*
- *"**Red-team** this deployment plan — find failure modes."*
- *"**Peer-review** this design doc."*
- *"Run the **rfc-pipeline** workflow on this spec."*
- *"Which format should I use for this?"* (invokes `format-selector`)
- *"Run **senate-eval** on all fixtures and report contract compliance per CLI."*

The `senate` skill triggers for single debates; the `workflow` skill for multi-stage pipelines. All run artifacts land in `.senate/` (runs) or `.senate/workflows/` (pipelines) in your current workspace — never in this skill repo.

## Adding a format, CLI, or workflow

- **New CLI**: drop `skills/invoke-agent/<name>.md` following one of the existing CLI files as a template.
- **New format**: drop `skills/debate-format/<name>.md` following `skills/debate-format/_template.md`, add a row to `debate-format/SKILL.md`.
- **New workflow**: drop a markdown file under `.senate/workflows/` in your workspace (user-local) or under `skills/workflow/canonical/` (to contribute upstream).
- **New eval fixture**: drop `skills/senate-eval/fixtures/<name>.md` following one of the shipped fixtures.

No code to write. No package to publish. Markdown all the way down.

## Roadmap

See [`dev/PRODUCT.md`](dev/PRODUCT.md) for the full vision and horizon plan. Summary of what's implemented:

- **H0 Foundation** — `senate`, `invoke-agent`, `debate-format` with parliament / court / consensus.
- **H1 Reliability** — contract discipline (`CONTRACTS.md`), failure taxonomy (`FAILURES.md`), budget guardrails (`BUDGET.md`), replay (`REPLAY.md`), and the `senate-eval` harness with 3 fixtures.
- **H2 Expanded society** — 8 new formats (committee, peer-review, brainstorm, oracle, socratic, appeals-court, rfc, red-team), the `invoke-format` composition primitive, and the `format-selector` recommender.
- **H3 Workflows** — the `workflow` skill with checkpoints, branching, and timeline-spanning, plus 4 canonical pipelines (rfc-pipeline, design-review, bill-to-law, incident-post-mortem).

H4–H7 (nested hierarchies, persistent actors, incentives, standing orgs) are described in `dev/PRODUCT.md` and not yet implemented.

## Requirements

- A host agent that supports the [Agent Skills spec](https://agentskills.io) (Claude Code, Codex, Cursor, OpenCode, etc.).
- The CLIs you want to include in debates installed and authenticated on your system. Each `skills/invoke-agent/<cli>.md` file has an install check you can copy-paste.

## License

MIT
