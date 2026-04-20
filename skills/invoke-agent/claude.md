# claude — Anthropic Claude Code CLI

## Install check

```bash
command -v claude && claude --version
```

Install docs: https://code.claude.com/docs

## Invoke

Non-interactive one-shot:

```bash
claude -p --model "{model}" <<'PROMPT'
{prompt}
PROMPT
```

Placeholders:

- `{model}` — e.g. `claude-opus-4-7`, `claude-sonnet-4-6`, `claude-haiku-4-5`. Omit to use the user's configured default.
- `{prompt}` — full prompt body via stdin.

For structured output, prefer JSON mode:

```bash
claude -p --model "{model}" --output-format json <<'PROMPT'
{prompt}
PROMPT
```

## Input

- `-p`/`--print` enters headless mode and reads stdin.
- Long prompts work fine on stdin; no need for a tempfile unless the shell complains about heredoc size.

## Output

- Default: plain text to stdout.
- `--output-format json` emits a structured record with the final reply and a tool-use trace:
  ```bash
  claude -p --output-format json < prompt.txt | jq -r '.result'
  ```
- `--output-format stream-json` for incremental output when you want to show progress.

## Budget flags

- `--max-turns N` caps internal tool-use iterations (default is generous).
- No token cap flag — constrain via prompt and `timeout`.

## Auth

- Logged in via `claude login`, or `ANTHROPIC_API_KEY` in the environment.
- If neither is set, `claude -p` exits with an auth error.

## Known quirks

- Headless `claude` may try to read project files when it sees path-like strings. For debate turns, pass `--permission-mode plan` or explicitly instruct **"Do not use Read, Edit, or Bash tools. Reply in text only."** to keep it a pure reasoner.
- If the calling process is also Claude Code, you are nesting the CLI. Set `CLAUDE_CODE_NESTED=1` to avoid session-file collisions, or run in a temp cwd.
- Streaming JSON emits one event per line; parse incrementally or join before jq.
