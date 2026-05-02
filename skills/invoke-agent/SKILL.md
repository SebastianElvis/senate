---
name: invoke-agent
description: Playbook for invoking non-interactive coding-agent CLIs (codex, gemini, cursor, kimi, claude) as subprocesses. Use this skill when moderate-debate needs to run one turn of a debate, or when any skill needs to shell out to another AI CLI with a prompt and capture the reply — covers install checks, exact non-interactive invocation, input/output conventions, budget flags, and known per-CLI quirks.
license: MIT
compatibility: Requires the relevant CLI binaries (codex, gemini, cursor-agent, kimi, claude) on PATH for any participating agent.
---

# invoke-agent — CLI invocation playbook

This skill is a **reference library**, not a flow. When you need to call another AI CLI, read the relevant file below for the exact command, flags, input conventions, output parsing rules, and known quirks.

## Supported CLIs

| CLI | File | Typical use |
| --- | --- | --- |
| codex | `references/codex.md` | OpenAI Codex CLI |
| gemini | `references/gemini.md` | Google Gemini CLI |
| cursor | `references/cursor.md` | Cursor Agent CLI (`cursor-agent`) |
| kimi | `references/kimi.md` | Moonshot Kimi CLI |
| claude | `references/claude.md` | Anthropic Claude Code CLI |

## Common invocation shape

Every CLI playbook follows the same schema so you can read them interchangeably:

1. **Install check** — one shell command that proves the CLI is on PATH.
2. **Invoke** — the exact non-interactive command template with placeholders for `{prompt}`, `{model}`, `{system}`.
3. **Input** — stdin vs. flag vs. file. How to pass long prompts (usually: heredoc to stdin, or a tempfile).
4. **Output** — stdout shape (plain text, JSON, streaming). Any banner/ANSI stripping rules.
5. **Budget flags** — token/time caps if the CLI supports them.
6. **Known quirks** — auth env vars, rate limits, non-zero exits that are benign, output truncation.

## General rules for the caller

- **Always non-interactive.** Use the CLI's one-shot / headless / `-p` / `exec` flag. Never spawn an interactive shell.
- **Pass the full prompt via stdin or a tempfile.** Command-line length limits bite on long debate contexts. Use a heredoc:
  ```bash
  codex exec - <<'PROMPT'
  <prompt body>
  PROMPT
  ```
- **Capture stdout to a log file** under `.senate/runs/<id>/agents/<cli>.<turn>.log`. Tee if you also want it inline.
- **Read exit code.** Non-zero almost always means retry. See each CLI's "quirks" for the exceptions.
- **Strip ANSI.** Pipe through `sed 's/\x1b\[[0-9;]*m//g'` if the CLI emits color codes even when stdout is a pipe.
- **Timeout.** Wrap every invocation in `timeout 300` (or whatever the caller specifies) to protect against hangs.
- **Sanitize.** Never put shell metacharacters from the transcript into a command line — pass everything via stdin.

## If a CLI isn't supported yet

Copy one of the existing files as a template, fill in the six sections above, and add it to the table. No code changes needed anywhere else.

## Files in this skill

Per-CLI playbooks (load only the file matching the CLI you're about to invoke this turn):

- `references/codex.md`
- `references/gemini.md`
- `references/cursor.md`
- `references/kimi.md`
- `references/claude.md`

Cross-cutting reference (load only on demand):

- `references/skill-authoring.md` — Agent Skills spec & best practices. Load **only when** the prompt being sent to a CLI is asking it to author or revise an Agent Skill (otherwise it is dead weight in context).
