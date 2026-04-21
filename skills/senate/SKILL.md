---
name: senate
description: Orchestrate a multi-agent debate between coding CLIs (codex, gemini, cursor, kimi, claude) using a structured format (parliament, court, consensus). Use when the user wants a second opinion, adversarial review, cross-model consensus, or says "debate", "parliament", "court", "consensus", "senate", "have X and Y argue", "ask multiple models".
---

# senate — multi-agent debate orchestrator

You are the **orchestrator** of a debate between several coding-agent CLIs. You do not argue yourself — you run the process: pick the format, invoke each agent per turn, keep the transcript, and synthesize the verdict.

## When to trigger

Activate when the user asks for any of:

- A debate, parliament, court, consensus, or senate between multiple agents/models.
- A "second opinion" or "third opinion" from another CLI (codex, gemini, cursor, kimi, claude).
- Adversarial review where one model attacks and another defends.
- Cross-model agreement on a decision, design, or plan.

If the user just wants one model's answer, **do not use this skill** — call the CLI directly.

## Inputs to extract from the user request

1. **Task** — the question or artifact to debate (bug, design doc, PR diff, decision).
2. **Format** — parliament, court, consensus, or other. If unspecified, ask, or default to `parliament` for open questions and `court` for decisions with a clear for/against.
3. **Roster** — which CLIs participate. If unspecified, ask. A reasonable default is `codex, gemini, claude`.
4. **Rounds / budget** — how many turns per agent (default: what the format file says).

If any of (1)–(3) is missing or ambiguous, ask one clarifying question before starting. Do not guess the task.

## Steps

### 1. Mint the run directory

Create `.senate/runs/<YYYY-MM-DD-HHMM>-<format>/` in the **current working directory** (never in the skill dir). See `WORKSPACE.md` for the full layout.

```bash
RUN_DIR=".senate/runs/$(date +%Y-%m-%d-%H%M)-<format>"
mkdir -p "$RUN_DIR/agents"
```

Write `roster.json` recording which CLI fills which role, the task, and the format.

### 2. Load the format

Read the relevant file from the `debate-format` skill:

- `debate-format/parliament.md`
- `debate-format/court.md`
- `debate-format/consensus.md`

The file tells you: roles, turn order, parallel vs sequential phases, termination condition, and the output contract for each turn.

### 3. Load per-CLI invocation playbooks

For each CLI in the roster, read the relevant file from the `invoke-agent` skill:

- `invoke-agent/codex.md`
- `invoke-agent/gemini.md`
- `invoke-agent/cursor.md`
- `invoke-agent/kimi.md`
- `invoke-agent/claude.md`

These tell you the exact command template, stdin/flag conventions, output parsing, and known quirks for each CLI.

### 4. Run turns

For each turn the format specifies:

1. Build the prompt. Every prompt has three parts:
   - **Role brief** (from the format file) — who this agent is in this debate (e.g., "prosecution", "MP for party X", "synthesizer").
   - **Transcript slice** — the prior turns this role is allowed to see (some formats redact; e.g., a jury doesn't see the judge's sidebar).
   - **Turn instruction** — what to produce this turn, including any structured-output contract.
2. Invoke the CLI using its playbook. Redirect stdout to `.senate/runs/<id>/agents/<cli>.<turn>.log`.
3. Append a JSONL record to `.senate/runs/<id>/transcript.jsonl`:
   ```json
   {"turn": 3, "role": "prosecution", "cli": "codex", "ts": "2026-04-20T14:32:11Z", "text": "...", "tokens": 812}
   ```
4. If the format declares this phase as parallel, launch the per-agent subprocesses concurrently and wait for all before appending (order by role for determinism).

### 5. Enforce output contracts

Every phase with structured output declares a contract (see `CONTRACTS.md`). Validate each reply; on first failure, re-prompt with the contract restated; on second failure, record `"error": "contract_violation"` and apply the format's fallback rule.

Detect and record other failure classes (`auth`, `rate_limit`, `timeout`, `refusal`, `unknown`) per `FAILURES.md`. Never silently drop a participant.

Respect the budget caps in `BUDGET.md`: check `wall_clock_remaining` and `tokens_remaining` before each turn; if either is below its safety margin, skip to synthesis with what exists.

### 6. Synthesize the verdict

When the format's termination condition fires, run the synthesis turn as specified (usually one designated "judge" or "speaker" role). Write the final verdict to `.senate/runs/<id>/verdict.md` with:

- The question.
- The roster and format.
- The verdict itself.
- A short rationale citing turn numbers from the transcript.
- Any dissenting minority opinion.

### 7. Report back

Return to the user:

- A two-to-four-sentence summary of the verdict.
- The path to `verdict.md` and the run dir.
- Anything unexpected (an agent that kept failing, a split vote, etc.).

Do **not** dump the full transcript into the chat — it's on disk, linkable.

## Guardrails

- **Workspace state only in `.senate/`**, never in the skill directory. The skill is read-only at runtime.
- **Budget.** Default to 1 opening + 2 rebuttal rounds + 1 synthesis per agent. Respect any `--max-rounds` or `--budget` the user gives.
- **Parallelism.** Use parallel subprocesses only when the format phase is declared parallel. Sequential phases (e.g., court) must wait for each turn.
- **Failures.** If a CLI fails a turn twice (non-zero exit or contract violation), record the failure in `transcript.jsonl` and continue. Never silently drop a participant.
- **No secrets in prompts.** Strip env vars, tokens, and credentials from anything sent to another CLI.

## Files in this skill

- `SKILL.md` — this file.
- `WORKSPACE.md` — spec for `.senate/runs/<id>/` layout.
- `CONTRACTS.md` — structured-output contract discipline.
- `FAILURES.md` — the five error classes and how to detect/retry each.
- `BUDGET.md` — wall-clock, token, and per-turn caps.
- `REPLAY.md` — deterministic replay of past runs.

## Related skills

- `../invoke-agent/*.md` — per-CLI invocation playbooks.
- `../debate-format/*.md` — per-format playbooks (and `../invoke-format/` for composition).
- `../format-selector/` — when format is unspecified, ask this skill.
- `../workflow/` — multi-stage pipelines that chain formats.
- `../senate-eval/` — contract-compliance fixtures and scoring.
