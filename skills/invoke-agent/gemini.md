# gemini — Google Gemini CLI

## Install check

```bash
command -v gemini && gemini --version
```

Install docs: https://geminicli.com/

## Invoke

Non-interactive one-shot:

```bash
gemini --model "{model}" --prompt "$(cat)" <<'PROMPT'
{prompt}
PROMPT
```

Or the more common short form:

```bash
gemini -m "{model}" -p - <<'PROMPT'
{prompt}
PROMPT
```

Placeholders:

- `{model}` — e.g. `gemini-2.5-pro`, `gemini-2.5-flash`. Omit to use the CLI default.
- `{prompt}` — full prompt body.

## Input

- Preferred: `-p -` reads prompt from stdin.
- Some versions require the prompt as a quoted argument to `-p`. If `-p -` fails, fall back to:
  ```bash
  PROMPT_BODY=$(cat <<'PROMPT'
  {prompt}
  PROMPT
  )
  gemini -m "{model}" -p "$PROMPT_BODY"
  ```

## Output

- Plain text to stdout.
- Request JSON explicitly in-prompt ("Return only a fenced json block...") — Gemini CLI does not guarantee structured mode across versions.
- Streaming output is rendered line-buffered to stdout; no special handling needed when capturing.

## Budget flags

- `--max-output-tokens N` on most versions.
- No hard request timeout flag — wrap in `timeout 300`.

## Auth

- `GEMINI_API_KEY` or `GOOGLE_API_KEY` env var, or OAuth via `gemini auth login`.
- On auth failure, stderr has a clear "authenticate" message — don't retry blindly.

## Known quirks

- Long prompts occasionally truncate silently. Put the most important instruction (the output contract) at the **end** of the prompt, not the start.
- Safety-filter refusals return exit code 0 with a short "I can't help with that" reply. Detect by length + content and treat as a contract violation.
- Rate limits surface as HTTP 429 in stderr; back off 30s and retry once.
