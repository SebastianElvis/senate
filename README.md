# senate

![The Senate — multi-agent debate between coding CLIs](assets/banner.png)

Multi-agent debate skills for coding CLIs. Orchestrates codex, gemini, cursor, kimi, and claude through structured debate formats — parliament, court, red-team, peer-review, committee, brainstorm — to reach more robust answers than any single model.

## Background

[**Multi-agent debate**](#references) is a well-studied technique for improving LLM reasoning: independent agents propose, critique, and revise answers under a structured protocol. Results are protocol-dependent — strong single-agent prompting can match it on some benchmarks — but a substantial body of work reports gains in factuality, divergent thinking, evaluation quality, and truthfulness.

`senate` ports the *protocols* humans already use to coordinate disagreement — parliaments, courts, peer review, RFCs — and packages them as agent skills you can run across heterogeneous CLIs. See [`dev/PRODUCT.md`](dev/PRODUCT.md) for the full thesis.

## Install

**Prerequisite:** the CLIs you want to put in debates must be installed and authenticated locally — `senate` shells out to them. Each [`skills/invoke-agent/references/<cli>.md`](skills/invoke-agent/references/) has a paste-ready install check for `codex`, `gemini`, `cursor`, `kimi`, and `claude`.

This repo ships as a [Claude Code plugin](https://code.claude.com/docs/en/discover-plugins) and as a cross-agent bundle via the [skills CLI](https://github.com/vercel-labs/skills) (works with most coding agents that load skills — Claude Code, Codex, Cursor, OpenCode, Gemini CLI, …).

```bash
# Claude Code plugin
/plugin marketplace add SebastianElvis/senate
/plugin install senate@senate

# Any host agent
npx skills add SebastianElvis/senate
```

Useful flags for the skills CLI:

| Option | Description |
| --- | --- |
| `-g, --global` | Install globally (`~/<agent>/skills/`) instead of the current project |
| `-a, --agent <name...>` | Target specific agents (`claude-code`, `codex`, `cursor`, `opencode`, …) |
| `-s, --skill <name...>` | Install a subset (`--skill senate`) |
| `-l, --list` | List skills without installing |
| `-y, --yes` | Skip prompts |

Other commands: `npx skills list | find <q> | update senate | remove senate`. Source forms accept GitHub shorthand, full URLs, git URLs, or local paths.

## Usage

Ask your host agent for a debate in plain language:

- *"Run a **parliament** between codex, gemini, and kimi on whether to migrate this service to Rust."*
- *"Hold a **court** debate — codex prosecutes my refactor, claude defends, gemini judges."*
- *"**Committee** of three models drafts this API design."*
- *"**Red-team** this deployment plan."*
- *"**Peer-review** this design doc."*
- *"Run a **draft-review-finalize** pipeline on this spec."* (multi-stage)
- *"Which format should I use?"* (the planner recommends one without running)

Run artifacts land in `<cwd>/.senate/runs/<id>/` — never in this skill repo. End-to-end walk-throughs of the headline cases live in [`examples/`](examples/README.md).

## Architecture

Five skills compose one debate lifecycle:

```
              user request
                   │
                   ▼
         ┌───────────────────┐
         │      senate       │   mints .senate/runs/<id>/
         │   (orchestrator)  │
         └─────────┬─────────┘
                   ▼
         ┌───────────────────┐
         │   debate-agenda   │ ──▶ agenda.md
         │     (planner)     │
         └─────────┬─────────┘
                   ▼
         ┌───────────────────┐  dispatches   ┌──────────────────┐
         │  moderate-debate  │ ─────────────▶│ per-turn subagent│
         │    (moderator)    │ ◀─────────────│ + invoke-agent   │
         └─────────┬─────────┘  result       └────────┬─────────┘
                   │ appends                          │ shells out
                   │   ▶ transcript.jsonl             ▼
                   │   ▶ context.md          codex · gemini · cursor
                   │   ▶ agents/<cli>.md     kimi  · claude
                   ▼
         ┌───────────────────┐ ──▶ notes.md
         │   meeting-note    │
         │     (scribe)      │
         └───────────────────┘
```

`moderate-debate` dispatches every turn into a fresh per-turn subagent that loads the relevant `invoke-agent` playbook, shells out to the CLI, validates the contract, and returns only a structured result. Multi-stage pipelines are expanded once by the planner into a single `agenda.md`; the moderator then runs each stage under `stages/<N>-<name>/`, calling back to the planner only for clarification or mid-run re-planning. `meeting-note` consolidates after the final stage.

| Skill | Purpose |
| --- | --- |
| `senate` | Top-level entry. Mints the run dir; routes through the lifecycle. |
| `debate-agenda` | Picks the format and roster, sequences pipeline stages, asks for clarification. Hosts formats at `formats/` and pipelines in `references/stages.md`. |
| `moderate-debate` | Drives turns by dispatching per-turn subagents; commits transcript/context; handles failures and checkpoints. |
| `meeting-note` | Reads agenda + transcript + context + verdicts; writes the user-facing `notes.md`. |
| `invoke-agent` | Per-CLI playbooks (codex, gemini, cursor, kimi, claude) loaded inside per-turn subagents. |

Every skill follows the [Agent Skills spec](https://agentskills.io/specification): a `SKILL.md` plus on-demand `references/`. The `evals/` directory is a sibling harness, not a shipped skill.

## Run-dir layout

```
.senate/runs/<id>/
  agenda.md            # the plan
  context.md           # shared scratchpad (delta-only)
  transcript.jsonl     # canonical per-turn record (errors live here as codes)
  state.json           # status, used for resume
  notes.md             # single user-facing summary
  bindings.json        # multi-stage only
  agents/
    moderator.md       # governance log
    <cli>.md           # per-CLI private memory
  stages/<n>-<name>/
    verdict.md
    turns/<NNN>-<cli>-<role>/
      prompt.derived.md
      stdout.log       # always present (may be empty on failure)
      stderr.log       # only if non-empty
      reply.md
```

Single-stage runs get exactly one `stages/` entry. Full schema in [`skills/senate/references/workspace.md`](skills/senate/references/workspace.md).

## Evaluating

`evals/` runs fixture debates end-to-end and grades them on two tiers: deterministic schema/contract checks against the run-dir, plus LLM judges (notes, agenda, transcript-quality) invoked via `claude -p`. A separate `pairwise` judge does A/B comparisons between two completed runs of the same fixture (counterbalanced for position bias) — used explicitly when comparing skill edits, not as a default fixture rubric. No API key needed — judges use your Claude Code OAuth.

```bash
evals/run.sh                                          # all fixtures
evals/run.sh evals/fixtures/_smoke-parliament.md      # cheapest fixture
python3 evals/scripts/report.py                       # rollup
```

Scorecard rows record `repo_commit`, `fixture_sha256`, and `claude_cli_version` for reproducibility. Stub-CLI replay is available for fast CI; methodology follows [Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents).

## Extending

- **New CLI** — drop `skills/invoke-agent/references/<name>.md` modeled on an existing file.
- **New format** — add `skills/debate-agenda/formats/<name>.md` *only* when it owns an interaction-contract axis no existing format owns; then add a row to `formats/README.md`.
- **New pipeline** — add a recipe to `skills/debate-agenda/references/stages.md` referencing existing formats, and a row to `formats/README.md`.

No code to write. Markdown all the way down.

## Roadmap

See [`dev/PRODUCT.md`](dev/PRODUCT.md) for the vision, design principles, and H0–H7 horizon plan.

## References

Theoretical foundations this skill bundle builds on.

Multi-agent debate as an LLM technique:

- Du et al. 2023, *Improving Factuality and Reasoning in Language Models through Multiagent Debate* — [arXiv:2305.14325](https://arxiv.org/abs/2305.14325)
- Liang et al. 2023, *Encouraging Divergent Thinking in Large Language Models through Multi-Agent Debate* — [arXiv:2305.19118](https://arxiv.org/abs/2305.19118)
- Chan et al. 2023, *ChatEval: Towards Better LLM-based Evaluators through Multi-Agent Debate* — [arXiv:2308.07201](https://arxiv.org/abs/2308.07201)
- Khan et al. 2024, *Debating with More Persuasive LLMs Leads to More Truthful Answers* — [arXiv:2402.06782](https://arxiv.org/abs/2402.06782)

Single-agent precursors and limits of debate:

- Wang et al. 2022, *Self-Consistency Improves Chain of Thought Reasoning in Language Models* — [arXiv:2203.11171](https://arxiv.org/abs/2203.11171). The single-agent precursor — sampling multiple reasoning paths from one model — that debate generalizes across models.
- Wang et al. 2024, on the limits of multi-agent discussion vs. strong single-agent prompting — [arXiv:2402.18272](https://arxiv.org/abs/2402.18272). Frames when debate is worth the cost.

Adjacent foundations for multi-agent LLM systems:

- Park et al. 2023, *Generative Agents: Interactive Simulacra of Human Behavior* — [arXiv:2304.03442](https://arxiv.org/abs/2304.03442). Role-playing agents under structured protocols.

## License

MIT
