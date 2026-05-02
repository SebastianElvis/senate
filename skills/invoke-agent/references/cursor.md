# cursor — Cursor Agent CLI

The binary is named `cursor-agent`, not `cursor` (which is the editor).

## Install check

```bash
command -v cursor-agent && cursor-agent --version
```

Install docs: https://cursor.com/docs/cli

## Invoke

Non-interactive one-shot:

```bash
cursor-agent --print --trust --model "{model}" <<'PROMPT'
{prompt}
PROMPT
```

Or with the prompt as a positional argument:

```bash
cursor-agent --print --trust --model "{model}" "{prompt}"
```

Placeholders:

- `{model}` — e.g. `auto`, `sonnet-4`, `sonnet-4-thinking`, `gpt-5`. Run `cursor-agent models` to list models available to the signed-in account. Omit `--model` to use the user's default.
- `{prompt}` — full prompt body via stdin or as the trailing positional argument.

`--trust` is required for headless invocation (otherwise cursor-agent halts with `Workspace Trust Required` before reading the prompt). `--yolo` / `-f` are equivalent but also force-allow tool actions; for pure-reasoner debate turns prefer `--trust` plus `--mode ask`.

## Input

- `-p` / `--print` enables non-interactive mode and prints the final reply to stdout.
- The prompt may be passed as the trailing positional argument **or** piped on stdin. Both work; stdin is preferred for long prompts.
- For very long contexts, use a tempfile:
  ```bash
  PROMPT_FILE=$(mktemp)
  cat > "$PROMPT_FILE" <<'PROMPT'
  {prompt}
  PROMPT
  cursor-agent --print --trust --model "{model}" < "$PROMPT_FILE"
  ```

Note: there is **no** `-m` short flag for `--model`. Older notes that used `-m` are wrong — Commander parses it as an unknown option and the run fails.

## Output

- Plain text by default (`--output-format text`).
- `--output-format json` emits a single JSON record. The reply lives in `.result` (not `.reply`):
  ```bash
  cursor-agent --print --trust --model "{model}" --output-format json < "$PROMPT_FILE" | jq -r '.result'
  ```
  Other useful fields: `.is_error`, `.session_id`, `.usage.{inputTokens,outputTokens,cacheReadTokens}`.
- `--output-format stream-json` for incremental events; pair with `--stream-partial-output` for token deltas.

## Budget flags

- No token cap flag. Cap via prompt wording and the portable timeout wrapper from `../../moderate-debate/references/budget.md`.
- `--mode plan` and `--mode ask` are read-only (no edits, no shell). Use `--mode ask` for pure-reasoner debate turns to prevent file mutation.

## Auth

- Signed in via `cursor-agent login` (uses the user's Cursor subscription) or `CURSOR_API_KEY` in the environment.
- `cursor-agent status` / `whoami` shows the active account.
- If not signed in, stderr says so clearly; do not retry.

## Known quirks

- Without `--trust`, headless runs in any unfamiliar directory exit early with `Workspace Trust Required` and the prompt is never sent. Always include `--trust` in debate invocations.
- In default mode `cursor-agent` will attempt to read files and edit them when it sees path-like strings. For debate turns, either pass `--mode ask` **or** explicitly instruct: **"Do not edit files or run commands. Reply in text only."**
- Tool-call diagnostics are written to stderr. Redirect stderr to `stderr.log` separately so `stdout.log` stays clean. Prune `stderr.log` if empty (mirror the codex pattern).
- The first invocation after a model switch can be slow (cold start); don't set `timeout` below 120s.
- JSON output uses `result`, not `reply`. Older parsers keyed on `.reply` will silently produce empty strings.
