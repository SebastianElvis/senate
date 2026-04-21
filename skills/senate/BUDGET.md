# Budget guardrails

Every debate has three hard caps. If any is reached, the orchestrator gracefully terminates the current phase and jumps to synthesis with whatever material exists.

## The three caps

| Cap | Default | Max | Scope |
| --- | --- | --- | --- |
| `wall_clock_sec` | 900 (15 min) | 7200 (2 h) | Whole run |
| `total_tokens` | 200_000 | 1_000_000 | Whole run (sum across all turns) |
| `turn_timeout_sec` | 300 | 900 | Per turn (passed to `timeout` wrapper) |

Users override with flags in the task request ("run with a 5-minute budget", "cap at 50k tokens"). Orchestrator records effective caps in `roster.json`.

## Recording usage

Each turn writes `prompt_tokens` and `completion_tokens` to `transcript.jsonl`. If the CLI does not report token counts, estimate: `chars / 4` for English, `chars / 2` for Chinese-heavy text. Estimates are flagged with `"tokens_estimated": true`.

Running totals live in-memory for the orchestrator; they are not persisted per-turn.

## Pre-flight check

Before each turn:

1. Compute `wall_clock_remaining = wall_clock_sec - (now - started_at)`.
2. Compute `tokens_remaining = total_tokens - sum(turn tokens so far)`.
3. If either is below a **safety margin** (default: 10% of cap), skip the turn and go straight to synthesis. Record `"error": "budget_exhausted"` for the skipped turn.

Safety margin exists so synthesis itself has budget left.

## Enforcement

- **Wall clock:** wrapper `timeout $turn_timeout_sec` around each CLI invocation.
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

## Propagation to sub-debates (H4+)

When a format role is filled by a sub-debate, the sub-run inherits a **fraction** of the parent's remaining budget:

```
sub_wall_clock = parent_remaining_wall_clock * 0.4
sub_tokens = parent_remaining_tokens * 0.3
```

Defaults are conservative. A parent cannot spend more than the child consumed (sub-run reports usage back).

For H3 workflows, budget is declared per-stage in the workflow file; the sum should not exceed the workflow's global cap.

## User-visible reporting

`verdict.md` ends with a short budget line:

```markdown
---

**Run budget:** 12m 04s wall / 900s cap • 143k tokens / 200k cap • 0 timeouts
```

If any cap was reached, say so explicitly: `... • 1 turn skipped due to budget exhaustion`.
