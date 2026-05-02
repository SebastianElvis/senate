# Budget guardrails

Every debate has three hard caps. If any is reached, the moderator gracefully terminates the current phase and jumps to synthesis with whatever material exists.

## The three caps

| Cap | Default | Max | Scope |
| --- | --- | --- | --- |
| `wall_clock_sec` | 900 (15 min) | 7200 (2 h) | Whole run (or whole stage in pipelines) |
| `total_tokens` | 200_000 | 1_000_000 | Whole run (sum across all turns) |
| `turn_timeout_sec` | 300 | 900 | Per turn (passed to `timeout` wrapper) |

The agenda may override per-stage in `stage.budget`; otherwise these defaults apply. The user may override at run start ("run with a 5-minute budget", "cap at 50k tokens"). The moderator records the effective caps in the run's `state.json`.

## Recording usage

Each turn writes `prompt_tokens` and `completion_tokens` to `transcript.jsonl`. If the CLI does not report token counts, estimate: `chars / 4` for English, `chars / 2` for Chinese-heavy text. Estimates are flagged with `"tokens_estimated": true`.

Running totals live in-memory for the moderator; they are not persisted per-turn (recompute from the transcript on resume).

## Pre-flight check

Before each turn:

1. Compute `wall_clock_remaining = wall_clock_sec - (now - started_at)`.
2. Compute `tokens_remaining = total_tokens - sum(turn tokens so far)`.
3. If either is below a **safety margin** (default: 10% of cap), skip the turn and go straight to synthesis. Record `"error": "budget_exhausted"` for the skipped turn with `exit_code: null`, `retry_count: 0`, `stderr_tail: null`, `log_path: null`, and `retry_log_path: null` because no per-turn subagent was dispatched.

Safety margin exists so synthesis itself has budget left.

## Enforcement

- **Wall clock:** wrap each CLI invocation with a portable timeout command. Resolve it once per per-turn subagent:

  ```bash
  timeout_cmd() {
    local seconds="$1"; shift
    if command -v timeout >/dev/null 2>&1; then
      timeout "$seconds" "$@"
    elif command -v gtimeout >/dev/null 2>&1; then
      gtimeout "$seconds" "$@"
    else
      perl -e 'alarm shift; exec @ARGV' "$seconds" "$@"
    fi
  }
  ```

  Use `timeout_cmd "$turn_timeout_sec" <cli command ...>` rather than assuming bare GNU `timeout` exists. macOS does not ship `timeout` by default; Homebrew Coreutils installs it as `gtimeout`; Perl is available on the supported macOS baseline.
- **Token cap:** checked between turns, not mid-turn. Some CLIs emit more than they should; we cannot truncate a response in flight.
- **Prompt cap:** if a single prompt would exceed the CLI's known context window, **auto-summarize the transcript slice** before sending. Add a transcript line `"action": "summarize_transcript", "from_turn": N, "to_turn": M`.

Context-window estimates per CLI:

| CLI | Context window |
| --- | --- |
| codex | 200k |
| gemini | 1M (Pro), 128k (Flash) |
| cursor | depends on model |
| kimi | 128k |
| claude | 200k (Sonnet/Opus), 1M (Opus 1M) |

If uncertain, assume 128k.

## Multi-stage budgets

For pipelines (multi-stage agendas), each stage has its own budget either declared in the agenda or inherited from the global default. The sum of stage budgets should not exceed a global pipeline cap — enforced at stage entry.

If a stage is about to exceed the pipeline's remaining budget, the moderator pauses for user intervention rather than burning the rest of the budget on one stage.

## Sub-debate budgets (composition)

When a stage role is filled by a sub-debate (per `../../debate-agenda/references/composition.md`), the sub-run inherits a **fraction** of the parent's remaining budget:

```
sub_wall_clock = parent_remaining_wall_clock * sub.budget_multiplier (default 0.4)
sub_tokens = parent_remaining_tokens * sub.budget_multiplier (default 0.3)
```

Defaults are conservative. A parent cannot spend more than the child consumed (sub-run reports usage back to the parent's running total).

## User-visible reporting

`verdict.md` ends with a short budget line written by `meeting-note`:

```markdown
---

**Run budget:** 12m 04s wall / 900s cap • 143k tokens / 200k cap • 0 timeouts
```

If any cap was reached, say so explicitly: `... • 1 turn skipped due to budget exhaustion`.
