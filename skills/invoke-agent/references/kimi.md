# kimi — Moonshot Kimi CLI

## Install check

```bash
command -v kimi && kimi --version
```

Install docs: https://moonshotai.github.io/kimi-cli/

## Invoke

Non-interactive one-shot (clean final-message-only output, stdin prompt):

```bash
kimi --quiet --input-format text --model "{model}" <<'PROMPT'
{prompt}
PROMPT
```

`--quiet` is an alias for `--print --output-format text --final-message-only`. Without it, default `--print --output-format text` emits a verbose trace of `StepBegin` / `ThinkPart` / `TextPart` / `StatusUpdate` / `TurnEnd` records to stdout.

Placeholders:

- `{model}` — e.g. `kimi-k2`, `kimi-latest`. Omit to use the default set in `~/.kimi/config.toml`.
- `{prompt}` — full prompt body via stdin.

## Input

- `--print` enters non-interactive mode (and implicitly enables `--yolo`). Stdin is only read when paired with `--input-format text` (or `stream-json`).
- `-p` / `--prompt` accepts the prompt as a CLI **string argument**, not a stdin signal. Don't combine `-p` with a heredoc — the heredoc body would be ignored.
- For very long prompts, prefer a tempfile:
  ```bash
  PROMPT_FILE=$(mktemp)
  cat > "$PROMPT_FILE" <<'PROMPT'
  {prompt}
  PROMPT
  kimi --quiet --input-format text --model "{model}" < "$PROMPT_FILE"
  ```

## Output

- `--quiet` emits the final assistant message as plain text to stdout — use this for debate turns.
- `--output-format stream-json` emits one JSON record per line (assistant content with `think` / `text` parts). Use when you need to inspect tool calls or the thinking trace.
- Request JSON explicitly in-prompt when needed. Extract a fenced block from the captured per-turn `stdout.log`:
  ```bash
  awk '/^```json/{flag=1;next}/^```/{flag=0}flag' < "$TURN_DIR/stdout.log" | jq .
  ```

## Budget flags

- `--max-steps-per-turn N` caps the number of internal tool-use steps.
- `--max-retries-per-step N` caps per-step retries.
- No token-cap flag — constrain via prompt wording and the portable timeout wrapper from `../../moderate-debate/references/budget.md`.

## Auth

- `kimi login` (OAuth), or `MOONSHOT_API_KEY` in the environment.
- On auth error, exits non-zero with a clear message; do not retry.

## Known quirks

- `--print` implicitly turns on `--yolo` (auto-approves all actions). For pure-reasoner debate turns, instruct in the prompt: **"Do not use any tools. Reply in text only."**
- Default `--output-format text` is human-friendly only — it interleaves `ThinkPart` / `StatusUpdate` lines with the actual reply. Always use `--quiet` (or `--final-message-only`) for capture, otherwise `reply.md` will contain telemetry.
- Chinese and English both work; if the debate is English, include "Reply in English." in the role brief to prevent drift.
- Long multi-turn context occasionally triggers server-side summarization — Kimi may compress earlier turns in its reply. Keep per-turn replies focused to limit drift.
- Rate-limit errors surface as non-zero exit with "rate limit" in stderr; back off 30s.
