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

This installs three skills into your agent's skill directory (`.claude/skills/`, `.agents/skills/`, etc.):

| Skill | Purpose |
| --- | --- |
| `senate` | Entry point. Picks format, manages the run, drives turns, writes the verdict. |
| `invoke-agent` | Reference playbook for invoking each supported CLI. |
| `debate-format` | Reference playbook for each debate format. |

## Usage

In your coding agent, ask something like:

- *"Run a **parliament** between codex, gemini, and kimi on whether to migrate this service to Rust."*
- *"Hold a **court** debate — codex prosecutes my refactor, claude defends, gemini judges."*
- *"Drive **consensus** between three models on this API design."*

The `senate` skill triggers, reads the chosen format and the agent list, and runs the debate. All run artifacts land in `.senate/runs/<timestamp>-<format>/` in your current workspace — not in this skill repo.

## Adding a format or a CLI

- New CLI: drop `skills/invoke-agent/<name>.md` following the schema in `_template.md` (coming soon — copy one of the existing files as a starting point).
- New format: drop `skills/debate-format/<name>.md` following `skills/debate-format/_template.md`.

No code to write. No package to publish. Markdown all the way down.

## Requirements

- A host agent that supports the [Agent Skills spec](https://agentskills.io) (Claude Code, Codex, Cursor, OpenCode, etc.).
- The CLIs you want to include in debates installed and authenticated on your system. Each `skills/invoke-agent/<cli>.md` file has an install check you can copy-paste.

## License

MIT
