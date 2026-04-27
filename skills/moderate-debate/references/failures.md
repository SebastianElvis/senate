# Failure taxonomy

Every turn that goes wrong must be recorded in `transcript.jsonl` with a standard `error` code. This is the only way debates become debuggable, and the only way the eval harness can compute contract compliance rates per CLI.

## The taxonomy

There are seven error codes. Five are detected from the CLI invocation; two are imposed by the moderator (`unknown` for non-zero exits the detection rules can't classify, `budget_exhausted` for turns the moderator skipped because a cap was hit per `budget.md`). Do not invent additional codes without extending this file.

| Code | Meaning | Detection | Retry policy |
| --- | --- | --- | --- |
| `auth` | CLI not logged in / missing API key | Non-zero exit AND stderr contains "auth", "login", "api key", "401", "403" | **No retry.** Surface to user immediately. |
| `rate_limit` | Provider throttled the request | Non-zero exit AND stderr contains "rate", "429", "quota", "too many" | Backoff 30s, retry once. On second failure, record `rate_limit` in transcript and continue. |
| `timeout` | Exceeded wall-clock budget | Wrapper `timeout` returned 124, or `SIGTERM` | Retry once with same budget. On second failure, record `timeout`. |
| `contract_violation` | Reply did not parse / validate per the format's contract | See `contracts.md` extraction + validation | Re-prompt once per `contracts.md`. On second failure, apply format fallback. |
| `refusal` | Model declined to answer (safety, policy, scope) | Exit 0 AND reply length < 200 chars AND reply matches refusal patterns ("I can't", "I'm not able to", "I won't", "as an AI") | **No retry.** Record `refusal` and apply format fallback. Retrying a refusal almost always refuses again. |
| `unknown` | Non-zero exit not matching any pattern above | Exit code ≠ 0 after all other detection rules | Record with `stderr_tail` attached and continue with the format fallback. Investigate manually. |
| `budget_exhausted` | Moderator skipped the turn because a budget cap was hit pre-flight | Set by the moderator per `budget.md`, not by CLI exit | No retry; jump to synthesis. |

CLI playbooks (`../../invoke-agent/references/<cli>.md`) MUST classify failures using exactly this taxonomy — they may not invent new codes or remap existing ones.

## Transcript fields for failed turns

Failed turns still write a line to `transcript.jsonl`. The full schema is canonical in `../../senate/references/workspace.md` (`## transcript.jsonl schema`); here is the failure-specific shape:

- `error` — set to one of the codes above; `null` on success.
- `retry_count` — number of retries attempted before the line was committed; `0` on first-try success.
- `stderr_tail` — last 200 bytes of stderr when `error` is set; never the whole stream.
- `text` — whatever stdout did arrive (may be empty).
- `structured` — omitted when `error` is set.

Example failed-turn line:

```json
{
  "turn": 7,
  "stage": 1,
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

  # 5. contract check is done by the moderator after this step

  [[ "$exit_code" != "0" ]] && echo "unknown"
}
```

Keep this inline rather than factoring out to a helper script — the whole project is markdown.

## Reporting

At end of run, the moderator writes `failures.md` next to `verdict.md` summarizing any non-empty error codes. If `failures.md` is absent, the run had zero errors.

Example:

```markdown
# Failures

- **T7** (gemini, rebuttal): rate_limit after 2 retries; continued.
- **T11** (codex, vote): contract_violation on retry; recorded as abstain.
```

The `meeting-note` skill reads `failures.md` and surfaces any non-trivial failures in the user-facing summary.

## Escalation

- Any `auth` error terminates the run and reports to the user (nothing else is possible).
- Any `unknown` error terminates the current turn but not the run; moderator continues with fallback.
- Two or more `refusal` errors from the same CLI in one run: surface to user after the verdict — "this model may not be suitable for this task".
- Three or more `contract_violation` errors from the same CLI in one run: call back to `../../debate-agenda/` for a re-plan; the planner may swap the CLI for the remaining stages.
