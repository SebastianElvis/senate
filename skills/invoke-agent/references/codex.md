# codex — OpenAI Codex CLI

## Install check

```bash
command -v codex && codex --version
```

Install docs: https://developers.openai.com/codex/cli

## Invoke

Non-interactive one-shot:

```bash
codex exec --model "{model}" - <<'PROMPT'
{prompt}
PROMPT
```

Placeholders:

- `{model}` — e.g. `gpt-5-codex`, `gpt-5`, `o4-mini`. Omit `--model` to use the user's default.
- `{prompt}` — full prompt body, including any role brief and transcript slice.

If the installed version doesn't accept stdin via `-`, fall back to a tempfile:

```bash
PROMPT_FILE=$(mktemp) && cat > "$PROMPT_FILE" <<'PROMPT'
{prompt}
PROMPT
codex exec --model "{model}" "$(cat "$PROMPT_FILE")"
rm -f "$PROMPT_FILE"
```

## Input

- Preferred: stdin via `-` argument.
- Fallback: tempfile, pass contents as positional argument.
- Do **not** pass long prompts directly on the command line.

## Output

- Plain text to stdout by default.
- If you need structured output, ask for a fenced `json` block in the prompt and parse it after.
- Banner/progress lines may appear on stderr — redirect stderr separately. Always keep the `.log` file, even when stdout is empty, because the moderator records `log_path` and that path must resolve. Prune only an empty `.stderr`:
  ```bash
  codex exec ... 2>"$RUN_DIR/agents/codex.1.stderr" >"$RUN_DIR/agents/codex.1.log"
  [ -s "$RUN_DIR/agents/codex.1.stderr" ] || rm -f "$RUN_DIR/agents/codex.1.stderr"
  ```

## Budget flags

- No first-class token cap flag. Enforce budget in the prompt ("Respond in at most N words.") and with the portable timeout wrapper from `../../moderate-debate/references/budget.md` (`timeout`, `gtimeout`, then Perl fallback).

## Auth

- `OPENAI_API_KEY` in the environment, or the user is logged in via `codex login`.
- If neither is present, `codex exec` exits non-zero with a clear error — surface that to the user rather than retrying.

## Known quirks

- First run after install may prompt for login; not suitable for debates. Run `codex exec "hello"` manually once first.
- Exit code 0 with empty stdout has been seen on some model overload errors — classify it as `unknown` per `../../moderate-debate/references/failures.md`. This is the one `unknown` case that gets the shared single retry for the turn; if the retry also returns empty stdout, return `error.kind = "unknown"`.
- ANSI color codes may leak even to pipes. Filter with `sed 's/\x1b\[[0-9;]*m//g'` before writing to the transcript.
