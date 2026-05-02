# Failure taxonomy

Every turn that goes wrong must be recorded in `transcript.jsonl` with a standard `error` code. This is the only way debates become debuggable, and the only way the eval harness can compute contract compliance rates per CLI.

## The taxonomy

There are seven error codes. Five are detected by the **per-turn subagent** (see `../SKILL.md` §4a) from the CLI invocation; one (`contract_violation`) is also detected by the subagent after CLI success when the reply fails the format's contract; one (`budget_exhausted`) is imposed by the **moderator** before dispatching, never by the subagent. Do not invent additional codes without extending this file.

| Code | Meaning | Detection | Retry policy (executed inside the subagent unless noted) |
| --- | --- | --- | --- |
| `auth` | CLI not logged in / missing API key | Non-zero exit AND stderr contains "auth", "login", "api key", "401", "403" | **No retry.** Subagent returns `error.kind = "auth"`; moderator aborts the run per § Escalation. |
| `rate_limit` | Provider throttled the request | Non-zero exit AND stderr contains "rate", "429", "quota", "too many" | Subagent backs off 30s and retries once. On second failure, returns `error.kind = "rate_limit"` and the moderator continues. |
| `timeout` | Exceeded wall-clock budget | Wrapper `timeout` returned 124, or `SIGTERM` | Subagent retries once with same budget. On second failure, returns `error.kind = "timeout"`. |
| `contract_violation` | Reply did not parse / validate per the format's contract | See `contracts.md` extraction + validation, run inside the subagent after a successful CLI call | Subagent re-prompts once per `contracts.md` only if the shared retry budget is still available. On second failure, or on first contract failure after the retry budget was already consumed, returns `error.kind = "contract_violation"`; moderator applies the format fallback. |
| `refusal` | Model declined to answer (safety, policy, scope) | Exit 0 AND reply length < 200 chars AND reply matches refusal patterns ("I can't", "I'm not able to", "I won't", "as an AI") | **No retry.** Subagent returns `error.kind = "refusal"`; moderator applies the format fallback. Retrying a refusal almost always refuses again. |
| `unknown` | Non-zero exit not matching any pattern above, or exit 0 with empty stdout | Exit code ≠ 0 after all other detection rules, OR exit code 0 and stdout length is 0 | For non-zero unknown: no retry. For exit-0 empty stdout: subagent retries once because this is often a transient provider/CLI overload. On second empty stdout, returns `error.kind = "unknown"` with `stderr_tail` attached; moderator records the line and continues with the format fallback. |
| `budget_exhausted` | Moderator skipped the turn because a budget cap was hit pre-flight | Set by the moderator per `budget.md` before any subagent dispatch; the subagent never returns this code | No retry; moderator jumps to synthesis. |

CLI playbooks (`../../invoke-agent/references/<cli>.md`) MUST classify failures using exactly this taxonomy — they may not invent new codes or remap existing ones. The subagent is the sole component that runs CLI detection; the moderator only consumes the structured `error` field from the subagent's return shape (see `../SKILL.md` §4a).

## Shared retry budget

Each turn has **at most one** CLI re-invocation inside its subagent. The same `r1` retry budget is shared by:

- `rate_limit` retry,
- `timeout` retry,
- exit-0 empty-stdout `unknown` retry,
- contract re-prompt from `contracts.md`.

If the retry budget was already consumed by a non-contract failure and the retry then fails contract validation, do **not** make a second CLI call. Return `error.kind = "contract_violation"` immediately with `retry_count: 1` and `retry_log_path` pointing at the already-used `r1` attempt.

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
  "retry_count": 1,
  "text": "",
  "stderr_tail": "HTTP 429: quota exceeded",
  "log_path": "agents/gemini.7.log",
  "retry_log_path": "agents/gemini.7r1.log"
}
```

## Detection code (Bash)

This runs **inside the per-turn subagent**, after the CLI call returns and before contract validation. Use this decision order — first match wins:

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

  # 4. exit 0 but empty stdout (retryable unknown; see Shared retry budget)
  if [[ "$exit_code" == "0" && "$stdout_len" -eq 0 ]]; then
    echo "unknown"
    return
  fi

  # 5. exit 0 but short + refusal pattern
  if [[ "$exit_code" == "0" && "$stdout_len" -lt 200 ]]; then
    grep -qiE "i can't|i am not able|i won't|as an ai" "$stdout_file" && { echo "refusal"; return; }
  fi

  # 6. contract check is done by the subagent after this step (see contracts.md);
  #    a contract failure becomes error.kind = "contract_violation" in the return shape.

  [[ "$exit_code" != "0" ]] && echo "unknown"
}
```

Keep this inline rather than factoring out to a helper script — the whole project is markdown.

## Reporting

At end of run, the moderator writes `failures.md` next to `verdict.md` summarizing any non-empty error codes. If `failures.md` is absent, the run had zero errors.

Example:

```markdown
# Failures

- **T7** (gemini, rebuttal): rate_limit after 1 retry; continued.
- **T11** (codex, vote): contract_violation on retry; recorded as abstain.
```

The `meeting-note` skill reads `failures.md` and surfaces any non-trivial failures in the user-facing summary.

## Escalation

These rules are **load-bearing** — the moderator must apply them after recording each failed turn, before dispatching the next per-turn subagent. Skipping them produces infinite-retry loops on broken CLIs.

- **Any `auth` error aborts the entire run.** Do not dispatch a new subagent for the same CLI again. Do not start the next turn even with a different role. **Parallel-phase exception** (per `../SKILL.md` §4a "Parallel + escalation"): when an `auth` error returns from one of several parallel subagents, *await* the rest of the already-dispatched subagents before acting — they are already running and cancelling them buys nothing — then commit every returned result in ascending `turn_id` order (including the auth-error line). After all parallel results are committed: write/update `failures.md` with the auth context, set `state.json` `status: "aborted"` with `aborted_reason: "auth_failure_<cli>"`, then hand back to `senate`. Do not dispatch any further subagents in this run. The user must fix the CLI's auth before any further debate is possible. (Rationale: an unauthenticated CLI cannot recover within a debate run; continuing wastes turns and produces a malformed transcript. Sibling successes from a parallel phase are still part of the run record.)
- Any `unknown` error terminates the current turn but not the run; moderator continues with fallback.
- Two or more `refusal` errors from the same CLI in one run: surface to user after the verdict — "this model may not be suitable for this task".
- Three or more `contract_violation` errors from the same CLI in one run: call back to `../../debate-agenda/` for a re-plan; the planner may swap the CLI for the remaining stages.
