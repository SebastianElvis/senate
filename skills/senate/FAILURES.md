# Failure taxonomy

Every turn that goes wrong must be recorded in `transcript.jsonl` with a standard `error` code. This is the only way debates become debuggable, and the only way `senate-eval` can compute contract compliance rates per CLI.

## The taxonomy

There are exactly five error classes. Do not invent new ones without extending this file.

| Code | Meaning | Detection | Retry policy |
| --- | --- | --- | --- |
| `auth` | CLI not logged in / missing API key | Non-zero exit AND stderr contains "auth", "login", "api key", "401", "403" | **No retry.** Surface to user immediately. |
| `rate_limit` | Provider throttled the request | Non-zero exit AND stderr contains "rate", "429", "quota", "too many" | Backoff 30s, retry once. On second failure, record `rate_limit` in transcript and continue. |
| `timeout` | Exceeded wall-clock budget | Wrapper `timeout` returned 124, or `SIGTERM` | Retry once with same budget. On second failure, record `timeout`. |
| `contract_violation` | Reply did not parse / validate per the format's contract | See `CONTRACTS.md` extraction + validation | Re-prompt once per `CONTRACTS.md`. On second failure, apply format fallback. |
| `refusal` | Model declined to answer (safety, policy, scope) | Exit 0 AND reply length < 200 chars AND reply matches refusal patterns ("I can't", "I'm not able to", "I won't", "as an AI") | **No retry.** Record `refusal` and apply format fallback. Retrying a refusal almost always refuses again. |

Any non-zero exit not matching the patterns above is recorded as `"error": "unknown"` with stderr attached. Unknown errors are investigated manually.

## Transcript schema

Failed turns still write a line to `transcript.jsonl`. The `error` key is present; `text` holds whatever stdout did arrive (may be empty); `structured` is omitted.

```json
{
  "turn": 7,
  "phase": "rebuttal",
  "role": "mp_con",
  "cli": "gemini",
  "ts": "2026-04-20T14:47:02Z",
  "exit_code": 1,
  "error": "rate_limit",
  "retry_count": 2,
  "text": "",
  "stderr_tail": "HTTP 429: quota exceeded"
}
```

`retry_count` is the number of retries attempted before giving up. `stderr_tail` is the last 200 bytes of stderr; never the whole stream.

## Detection code (Bash)

Use this decision order — first match wins:

```bash
detect_error() {
  local exit_code="$1" stdout_file="$2" stderr_file="$3"
  local stderr=$(tail -c 2048 "$stderr_file" | tr '[:upper:]' '[:lower:]')
  local stdout_len=$(wc -c < "$stdout_file")

  # 1. timeout wrapper
  [[ "$exit_code" == "124" || "$exit_code" == "143" ]] && { echo "timeout"; return; }

  # 2. auth
  grep -qE 'auth|login|api key|401|403|unauthori[sz]ed' <<< "$stderr" && { echo "auth"; return; }

  # 3. rate limit
  grep -qE 'rate|429|quota|too many' <<< "$stderr" && { echo "rate_limit"; return; }

  # 4. exit 0 but short + refusal pattern
  if [[ "$exit_code" == "0" && "$stdout_len" -lt 200 ]]; then
    grep -qiE "i can't|i am not able|i won't|as an ai" "$stdout_file" && { echo "refusal"; return; }
  fi

  # 5. contract check is done by the orchestrator after this step

  [[ "$exit_code" != "0" ]] && echo "unknown"
}
```

Keep this inline rather than factoring out to a helper script — the whole project is markdown.

## Reporting

At end of run, the orchestrator writes `failures.md` next to `verdict.md` summarizing any non-empty error codes. If `failures.md` is absent, the run had zero errors.

Example:

```markdown
# Failures

- **T7** (gemini, rebuttal): rate_limit after 2 retries; continued.
- **T11** (codex, vote): contract_violation on retry; recorded as abstain.
```

## Escalation

- Any `auth` error terminates the run and reports to the user (nothing else is possible).
- Any `unknown` error terminates the current turn but not the run; orchestrator continues with fallback.
- Two or more `refusal` errors from the same CLI in one run: surface to user after the verdict — "this model may not be suitable for this task".
