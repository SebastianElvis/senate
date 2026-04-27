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
cursor-agent --print --model "{model}" <<'PROMPT'
{prompt}
PROMPT
```

Short form:

```bash
cursor-agent -p -m "{model}" <<'PROMPT'
{prompt}
PROMPT
```

Placeholders:

- `{model}` — e.g. `auto`, `claude-sonnet-4.5`, `gpt-5`. Accepts any model Cursor supports for the signed-in user.
- `{prompt}` — full prompt body via stdin.

## Input

- `-p`/`--print` reads from stdin and prints the final reply.
- For very long contexts, use a tempfile:
  ```bash
  PROMPT_FILE=$(mktemp)
  cat > "$PROMPT_FILE" <<'PROMPT'
  {prompt}
  PROMPT
  cursor-agent -p -m "{model}" < "$PROMPT_FILE"
  ```

## Output

- Plain text by default.
- `--output-format json` gives a structured record with the reply and tool-call trace. Prefer this when parsing:
  ```bash
  cursor-agent -p -m "{model}" --output-format json < "$PROMPT_FILE" | jq -r '.reply'
  ```

## Budget flags

- No token cap flag as of this writing. Cap via prompt wording and `timeout`.

## Auth

- Signed in via `cursor-agent login`. Uses the user's Cursor subscription — no raw API key env var required.
- If not signed in, stderr says so clearly; do not retry.

## Known quirks

- `cursor-agent` will attempt to read files and edit them by default when it sees path-like strings. For debate turns, explicitly instruct it: **"Do not edit files. Reply in text only."** Otherwise it may mutate the workspace mid-debate.
- Tool-calls are logged to stderr. Redirect stderr to a separate file if you want a clean stdout.
- The first invocation after a model switch can be slow (cold start); don't set `timeout` below 120s.
