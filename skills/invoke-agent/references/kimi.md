# kimi — Moonshot Kimi CLI

## Install check

```bash
command -v kimi && kimi --version
```

Install docs: https://moonshotai.github.io/kimi-cli/

## Invoke

Non-interactive one-shot:

```bash
kimi -p --model "{model}" <<'PROMPT'
{prompt}
PROMPT
```

Placeholders:

- `{model}` — e.g. `kimi-k2`, `kimi-latest`. Omit to use CLI default.
- `{prompt}` — full prompt body via stdin.

## Input

- `-p` / `--print` reads stdin and returns the final reply.
- For very long prompts, prefer a tempfile:
  ```bash
  PROMPT_FILE=$(mktemp)
  cat > "$PROMPT_FILE" <<'PROMPT'
  {prompt}
  PROMPT
  kimi -p --model "{model}" < "$PROMPT_FILE"
  ```

## Output

- Plain text to stdout.
- Request JSON explicitly in-prompt when needed. Kimi tends to honor fenced-block contracts well — extract from the captured per-turn `stdout.log`:
  ```bash
  awk '/^```json/{flag=1;next}/^```/{flag=0}flag' < "$TURN_DIR/stdout.log" | jq .
  ```

## Budget flags

- `--max-tokens N` on recent versions.
- No built-in wall-clock timeout — wrap in `timeout 300`.

## Auth

- `MOONSHOT_API_KEY` env var, or signed in via `kimi login`.
- On auth error, exits non-zero with a clear message; do not retry.

## Known quirks

- Chinese and English both work; if the debate is English, include "Reply in English." in the role brief to prevent drift.
- Long multi-turn context occasionally triggers summarization on the server side — Kimi may compress earlier turns in its reply. Keep per-turn replies focused to limit drift.
- Rate-limit errors surface as non-zero exit with "rate limit" in stderr; back off 30s.
