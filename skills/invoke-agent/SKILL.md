---
name: invoke-agent
description: Playbook for invoking non-interactive coding-agent CLIs (codex, gemini, cursor, kimi, claude) as subprocesses. Use this skill inside a moderate-debate per-turn subagent, or when any skill needs to shell out to another AI CLI with a prompt and capture the reply — covers install checks, exact non-interactive invocation, input/output conventions, budget flags, and known per-CLI quirks.
license: MIT
compatibility: Requires the relevant CLI binaries (codex, gemini, cursor-agent, kimi, claude) on PATH for any participating agent.
---

# invoke-agent — CLI invocation playbook

This skill is a **reference library**, not a flow. When you need to call another AI CLI, read the relevant file below for the exact command, flags, input conventions, output parsing rules, and known quirks.

**Where this is read from:** `moderate-debate` does not call CLIs from its own context. Each turn is dispatched into a fresh subagent (Agent / Task tool, isolated context) that loads the playbook for one CLI, runs the call, validates the contract, and returns a small structured result. See `../moderate-debate/SKILL.md` § "Per-turn subagent" for the contract between moderator and subagent. If you find yourself reading these playbooks from a long-lived debate context, you are in the wrong place — dispatch a subagent.

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
- **Capture stdout to a log file** under `.senate/runs/<id>/agents/<cli>.<turn>.log`. Always create this file even if stdout is empty — the moderator records `log_path` on the transcript line and that path must resolve. Redirect stderr to a sibling `<cli>.<turn>.stderr`; delete the `.stderr` if it ends up empty (`[ -s file ] || rm -f file`). Never delete the `.log`.
- **Read exit code.** Classify failures with `../moderate-debate/references/failures.md`; retry only for that file's retryable cases (`rate_limit`, `timeout`, and the documented exit-0 empty-stdout `unknown` case), sharing the same single `r1` retry budget as contract re-prompts.
- **Strip ANSI.** Pipe through `sed 's/\x1b\[[0-9;]*m//g'` if the CLI emits color codes even when stdout is a pipe.
- **Timeout.** Wrap every invocation with the portable timeout command defined in `../moderate-debate/references/budget.md` (use GNU `timeout` when available, `gtimeout` on Homebrew/Coreutils macOS installs, otherwise the Perl fallback). Do not assume bare `timeout` exists on macOS.
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
