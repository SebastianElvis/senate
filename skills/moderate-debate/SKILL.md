---
name: moderate-debate
description: Drives a multi-agent debate from a planned agenda — builds prompts, dispatches each CLI turn into a standalone subagent, commits the shared transcript and context, handles budget/failure/checkpoint policy, and adapts the agenda mid-run when the situation diverges from the plan. Use this skill when senate has an `agenda.md` ready and needs the actual turns run, or when resuming a paused or stalled debate run.
license: MIT
---

# moderate-debate — run the debate from an agenda

You are the **moderator**. You did not plan the debate (the planner wrote `agenda.md`) and you do not synthesize the verdict (the meeting-note skill does). Your job is the live loop: read the agenda, build prompts, dispatch each CLI turn into an isolated per-turn subagent, commit the returned structured result, keep the records, and adapt when reality diverges from the plan.

A debate without a moderator is a chat. A moderator without an agenda is a chat with extra steps. Both pieces are required.

## When to trigger

Activate when:

- `senate` has an `agenda.md` ready and asks you to run it.
- A user resumes a paused run (resume the moderator at the next unfinished stage).
- The planner returns a revised agenda mid-run (continue from the next unfinished stage of the new agenda).

## Inputs

1. **Run directory** — `<cwd>/.senate/runs/<id>/`. Must already contain `agenda.md` with `status: ready`.
2. **(Optional) Resume signal** — if non-empty `transcript.jsonl` exists, resume from the last unfinished stage.

## Steps

### 1. Pre-flight

Read `agenda.md` and validate:

- `status: ready` (or `revising` after a re-plan).
- All `cli` values resolve to playbooks under `../invoke-agent/references/`.
- All `format` values resolve to format files under `../debate-agenda/formats/`.
- All `input_bindings` reference an `output_bindings` from an earlier stage.

If any check fails, do not start. Surface to the user via `senate`.

### 2. Initialize shared context

Each run dir contains a set of files agents read every turn (see `references/context.md`; full layout in `../senate/references/workspace.md`):

```
agenda.md                                  # the plan (already exists)
context.md                                 # shared scratchpad, delta-only, append-only across turns — moderator writer
transcript.jsonl                           # append-only canonical per-turn record — moderator writer
agents/moderator.md                        # moderator's governance log (you write this)
agents/<cli>.md                            # per-agent private memory (one file per CLI in the roster) — moderator writer
stages/<n>-<name>/turns/<NNN>-<cli>-<role>/{prompt.derived.md,stdout.log,stderr.log,reply.md}  # per-turn subagent writer
```

On first start of a run:

- Create empty `context.md` with a brief header explaining its purpose.
- Create empty `agents/<cli>.md` for each unique CLI in the agenda.
- Create empty `agents/moderator.md` with a brief header explaining it is the governance log (re-plans, contract retries, role/format swaps, tie-break rationale — every entry must cross-link the relevant `turn:` / `stage:` / `incident:` ID).
- Create the `stages/<n>-<name>/` directory for each stage in the agenda. Single-stage runs still get exactly one stage dir (`stages/1-<format>/`).

### 3. Walk the stages

For each `stage` in `agenda.stages` (in `index` order):

1. Read `../debate-agenda/formats/<stage.format>.md`. The format file declares roles, phases, turn order, contracts, and termination.
2. Build the stage input prompt: framing wrapper + agenda body excerpt + input bindings (resolved values from prior stages).
3. For each phase the format specifies:
   - For each turn in the phase (sequential or parallel per the format), execute these steps in this order. Steps a–c are "freeze the prompt" and must happen before any CLI dispatch — they make the prompt-bytes ↔ sha-bytes invariant load-bearing:
     - **a. Build the prompt** per "Turn prompt construction" below. Save the resulting string to a single variable (e.g. `$PROMPT`). **Do not** use placeholders like `[opening prompt — see prompt.derived.md]` — the eval harness reads `transcript.jsonl.prompt`, recomputes `sha256(prompt)`, and rejects the run if anything doesn't match.
     - **b. Compute the prompt's SHA-256 exactly once.** Run `printf '%s' "$PROMPT" | shasum -a 256 | cut -d' ' -f1` (or `python3 -c 'import sys,hashlib;print(hashlib.sha256(sys.stdin.read().encode()).hexdigest())' < <(printf '%s' "$PROMPT")`). Store the 64-char lowercase hex result in `$SHA`. **This single `$SHA` is the only sha you will write this turn.** Do not "regenerate" it later; do not invent a placeholder. The header in `prompt.derived.md` and the `prompt_sha256` field in the transcript line MUST both be `$SHA`. If the two ever diverge, the deterministic grader's `workspace_layout` check fails with `prompt.derived.md header does not match transcript`.
     - **c. Mint the turn directory** at `stages/<n>-<name>/turns/<NNN>-<cli>-<role>/` (NNN is the monotonic turn number across the whole run, zero-padded to 3 digits — same value as the `turn` field in `transcript.jsonl`). Then **write `<turn-dir>/prompt.derived.md`** as exactly:
       ```
       <!-- generated from transcript.jsonl turn N (sha256 $SHA); do not edit -->
       $PROMPT
       ```
       i.e. one header line ending in `\n`, then `$PROMPT` verbatim (no trimming, no normalization, no rewriting). The eval harness reads the file, strips the header line, and compares the remainder byte-for-byte to `transcript.jsonl.prompt` — any whitespace edit will fail. This file is **mandatory** for every dispatched-CLI turn; write it BEFORE dispatching the subagent.
     - **d. Dispatch the CLI call as a subagent** (see "Per-turn subagent" below). Pass `$PROMPT` to the subagent verbatim. Never shell out to the CLI from your own context — raw stdout, stderr, banners, and re-prompt traffic must not enter the moderator's window. The subagent reads the relevant `../invoke-agent/references/<cli>.md` playbook, captures stdout to `<turn-dir>/stdout.log` (always present, even if empty on failure) and stderr to `<turn-dir>/stderr.log` (delete if empty), validates the contract per `references/contracts.md`, and returns a small structured result (full shape in §4a). Parallel turns become parallel subagent dispatches; commit their results in turn-id order after all have returned (see "Parallel-turn ordering" in §4a).
     - **e. Commit:** forward the subagent's fields into `transcript.jsonl`, `context.md`, and `agents/<cli>.md` per the commit pattern, then discard the result — you do not retain `text` or `parsed_output` across turns. You never open the raw `stdout.log` / `stderr.log` files; they are for replay/debug only.
       - On `error.kind == "contract_violation"`, apply the format's fallback rule. On any other error, follow `references/failures.md`, record the line, **then apply the escalation rule from `references/failures.md` § Escalation before proceeding**. In particular: an `auth` error aborts the entire run; do not dispatch the same CLI again, do not start the next turn. Update `state.json` to `status: aborted` with `aborted_reason` and hand back to `senate`. (Failure facts live in `transcript.jsonl`; the scribe surfaces a rollup in `notes.md`.)
       - Append a **single-line** JSONL record to `transcript.jsonl` per the canonical schema in `../senate/references/workspace.md`. The serialized JSON object MUST be on one physical line — escape embedded newlines in `prompt` / `text` / `stderr_tail` as `\n` and after every append verify with `python3 -c 'import json,sys;[json.loads(l) for l in open("transcript.jsonl") if l.strip()]'` (it must exit 0). `prompt` MUST be `$PROMPT` verbatim; `prompt_sha256` MUST be `$SHA`. Subagent-sourced fields: `text`, `exit_code`, `retry_count`, `stderr_tail`, `structured` ← `parsed_output`, `error` ← `error.kind`, `log_path`, `retry_log_path`. Moderator-sourced fields: `prompt` (= `$PROMPT`), `prompt_sha256` (= `$SHA`), `ts`, `prompt_tokens` / `completion_tokens` / `tokens_estimated`, `context_delta_appended` / `private_delta_appended` (true iff you appended a non-empty delta this turn), `sub_run_id` (set only for composed sub-debate turns).
       - Write `<turn-dir>/reply.md` — the cleaned reply text with fenced `context-delta` / `private-delta` / structured-output blocks stripped (the subagent may write this directly, or the moderator does it on commit; see §4a).
       - Apply context updates: append `context_delta` to `context.md`; append `private_delta` to `agents/<cli>.md`. See `references/context.md`.
       - When you make an adaptive decision worth recording (re-prompt vs fallback, format swap, role swap, tie-break, decision to pause vs continue), append an entry to `agents/moderator.md` with a `turn:` cross-link rather than narrating the underlying fact.
   - **Update `state.json` at every turn boundary** with the new `last_activity_at` (atomic write: temp file + rename). Don't batch state updates to stage boundaries — a crashed or timed-out run leaves no signal of progress otherwise.
4. Check budget per `references/budget.md` between turns. If a cap is near, gracefully terminate and skip to the stage's synthesis turn.
5. Extract the stage's `output_bindings` from the verdict.
6. Honor checkpoints per `references/checkpoints.md`. If a `required` or triggered `conditional` checkpoint fires, write checkpoint state and pause.

### 4. Turn prompt construction

Every turn prompt has these sections, in this order:

1. **Run header** — task, run_id, current stage name, format name. From `agenda.md`.
2. **Role brief** — from the format file. Who this agent is in this debate.
3. **Shared context** — full content of `context.md`. Read fresh each turn.
4. **Private memory** — full content of `agents/<cli>.md`. The agent's own scratchpad from prior turns.
5. **Transcript slice** — prior turns this role is allowed to see (some formats redact).
6. **Turn instruction** — what to produce this turn, including the output contract (fenced JSON) if any, and the fence labels for an optional `context-delta` block (free-form prose to append to shared context) and an optional `private-delta` block (free-form prose to append to the agent's own memory).

The prompt string is handed to the per-turn subagent, which passes it to the CLI via stdin per `../invoke-agent/SKILL.md` and wraps the call with the portable timeout command from `references/budget.md`.

### 4a. Per-turn subagent

Every turn-level CLI invocation runs inside a fresh subagent (Agent / Task tool, isolated context). The moderator never reads raw CLI stdout. If that turn needs the one permitted retry (`rate_limit`, `timeout`, exit-0 empty stdout, or contract re-prompt), the retry stays inside the same isolated subagent and is recorded as that turn's `r1` attempt; retry traffic still never enters the moderator's context.

**Why:** debates are long. Raw CLI output, ANSI banners, re-prompt traffic, and CLI quirks would otherwise accumulate in the moderator's context, crowding out the transcript and shared scratchpad and coupling moderator stability to per-CLI failure modes. Subagent isolation also lets parallel turns actually run in parallel.

**Inputs to the subagent** (everything it needs — it does not see the moderator's wider state):

- `run_dir` — absolute path to `<cwd>/.senate/runs/<id>/`.
- `cli` — name matching a playbook in `../invoke-agent/references/<cli>.md`.
- `turn_id` — integer matching the upcoming `turn` field in `transcript.jsonl`. Used to compose the per-turn directory `stages/<n>-<name>/turns/<NNN>-<cli>-<role>/` (`<NNN>` = `turn_id` zero-padded to 3 digits) where `stdout.log` and `stderr.log` land. The moderator pre-mints this directory before dispatch; the subagent only writes inside it.
- `prompt` — the full turn prompt built per "Turn prompt construction".
- `contract` — `schema`, `example`, `extraction rule`, `re-prompt template`, and an optional `validators` list (from the format file; full shape in `references/contracts.md`). `validators` carries free-form predicates the subagent enforces alongside schema validation — e.g., the brainstorm format's "no critique language in phase 1" or rfc's "paragraphs are numbered" rule. They run on the same shared retry path as schema validation: any predicate failure is treated as a contract violation, the subagent re-prompts once if the turn's retry budget is still available, and a second failure (or a first contract failure after a non-contract retry already consumed the budget) returns `error.kind = "contract_violation"`. `contract` is `null` for turns with no machine validation: the subagent skips validation, sets `contract_ok: true`, and `parsed_output: null`. Free-text contracts may validate `text` without producing a separate `parsed_output`. The `context-delta` / `private-delta` extraction is independent of the contract and runs either way.
- `timeout_seconds` — per `references/budget.md`.

**What the subagent does** (and only this — files it owns are listed below; it never touches `transcript.jsonl`, `context.md`, `agents/<cli>.md`, `state.json`, `failures.md`, `agenda.md`, or any stage verdict):

1. Read `../invoke-agent/references/<cli>.md` for the exact invocation shape.
2. Shell out non-interactively, prompt on stdin, wrapped with the portable timeout command from `references/budget.md`. Strip ANSI. Capture stdout to `<turn-dir>/stdout.log` and stderr to `<turn-dir>/stderr.log`, where `<turn-dir>` is `stages/<n>-<name>/turns/<NNN>-<cli>-<role>/` (already pre-minted by the moderator). **Always keep `stdout.log`** (even when empty, so `log_path` always resolves); delete `stderr.log` only if it ended up empty (`[ -s file ] || rm -f file`).
3. Detect non-contract errors per `references/failures.md` (auth / rate_limit / timeout / refusal / unknown). On `rate_limit`, `timeout`, or exit-0 empty-stdout `unknown`, retry per the policy in that file before returning — the retry attempt's stdout/stderr go to `<turn-dir>/stdout.r1.log` / `stderr.r1.log` (uniform retry naming, see step 4); set `retry_log_path` on the return. `error.kind` MUST be one of the codes in that file's taxonomy.
4. If the call succeeded (no error), validate against the contract per `references/contracts.md`. On first parse/validate failure, re-prompt the CLI once with the re-prompt template **only if the turn's shared retry budget has not already been consumed**. The re-prompt call is written to `<turn-dir>/stdout.r1.log` / `stderr.r1.log`. On second failure, or on first contract failure after a non-contract retry already consumed `r1`, return `error: { kind: "contract_violation" }`. Whether the retry was triggered by `rate_limit`, `timeout`, exit-0 empty stdout, or contract validation, the file naming is the same `.r1.log` suffix and there is at most one retry per turn.
5. Extract optional `context-delta` and `private-delta` blocks per `references/context.md`.
6. Return a single structured result. No prose, no narrative, no rendered raw stdout.

**Subagent return shape** (fixed; moderator code reads these field names directly):

```json
{
  "contract_ok": true,
  "text": "…cleaned reply, ANSI-stripped, exactly what should land in transcript.jsonl.text…",
  "parsed_output": { "...": "..." },
  "context_delta": "…or null…",
  "private_delta": "…or null…",
  "log_path": "stages/<n>-<name>/turns/<NNN>-<cli>-<role>/stdout.log",
  "stderr_path": null,
  "retry_log_path": null,
  "retry_stderr_path": null,
  "exit_code": 0,
  "retry_count": 0,
  "stderr_tail": null,
  "duration_seconds": 42,
  "error": null
}
```

Field rules — split by where the value lands:

*Forwarded to transcript line* (moderator copies into `transcript.jsonl`):

- `text` — present on every return (success or failure); empty string if the CLI produced no usable stdout. Forwarded verbatim into `transcript.jsonl.text`; it is the only place cleaned reply prose enters the moderator's context, and only fleetingly during commit.
- `parsed_output` — object iff the contract declares a machine-readable structured block (usually fenced JSON) AND validation passed. `null` for free-text contracts that only validate the reply prose, for `contract: null` turns, and for any error (including `contract_violation`). Maps to `transcript.jsonl.structured` and is omitted from the transcript when `null`.
- `exit_code` — last CLI invocation's exit code (the retry's, if a retry happened). Maps directly.
- `retry_count` — counts CLI re-invocations the subagent performed (`rate_limit`, `timeout`, exit-0 empty-stdout `unknown`, or contract re-prompt — at most one retry per turn under any policy). `0` on first-try success, `1` on any retried turn.
- `stderr_tail` — last 200 bytes of stderr when `error` is set, else `null`. Already truncated by the subagent.
- `error` — `null` on success. Otherwise `{ "kind": "<code>", "detail": "..." }` where `<code>` is one of the codes in `references/failures.md` (`auth | rate_limit | timeout | contract_violation | refusal | unknown`). The moderator imposes `budget_exhausted` itself before dispatching; the subagent never returns it. The moderator stores only `error.kind` in `transcript.jsonl.error`.
- `log_path` — relative path (from run dir) to the first-attempt `stdout.log` under the per-turn directory (e.g., `stages/1-parliament/turns/007-codex-mp_pro/stdout.log`). Always set; the file always exists (even when empty).
- `retry_log_path` — relative path to the retry attempt's stdout log (e.g., `stages/1-parliament/turns/007-codex-mp_pro/stdout.r1.log`); `null` when no retry happened. Naming is uniform across retry causes (`rate_limit`, `timeout`, exit-0 empty stdout, contract violation): `stdout.r1.log` (and `stderr.r1.log` if non-empty) sit next to `stdout.log` in the same per-turn directory. There is never an `r2` — at most one retry per turn under any policy.

*Used for moderator control flow / failures-md / debug, not persisted in transcript:*

- `contract_ok` — boolean. Convenience for the moderator: equivalent to `error == null` (any non-`null` error means contract validation either didn't run or didn't pass). Equivalently, `contract_ok` is `true` iff the moderator can use this turn's output without invoking the format fallback. Discard after deciding whether to apply the format fallback.
- `stderr_path`, `retry_stderr_path` — relative paths to `.stderr` files when they survived the empty-prune; `null` otherwise. Used by the moderator only when populating `failures.md` for an error turn; otherwise discarded.
- `duration_seconds` — wall-clock seconds the subagent spent on this turn (sum across attempts). Aggregated into `state.json.budget_remaining` when applicable; not stored per-line in the transcript.

*Forwarded to context/private files* (moderator appends to the right file):

- `context_delta` — string or `null`. If non-`null` and non-empty, the moderator appends it to `context.md` and sets `transcript.jsonl.context_delta_appended = true`.
- `private_delta` — string or `null`. Same shape, appended to `agents/<cli>.md` and reflected as `private_delta_appended`.

**Parallel-turn ordering.** When a phase declares parallel turns, the moderator dispatches all subagents concurrently and **awaits all** before committing any writes. After await, commit results to `transcript.jsonl`, `context.md`, and `agents/<cli>.md` in ascending `turn_id` order. All parallel subagents in a phase see the same pre-phase snapshot of `context.md` and `agents/<cli>.md`; they cannot observe each other's deltas. (This is intentional — parallel phases model independent reasoning. If a format needs deltas to be visible mid-phase, declare the turns sequential.)

**Parallel + escalation.** Even if one parallel subagent returns an `auth` error (or any other escalation-trigger per `references/failures.md`), the moderator still **awaits the rest** before acting — they are already running and cancelling them buys nothing. After await, commit every returned result in ascending `turn_id` order (including the auth error), then apply the escalation rule. For `auth`: stop dispatching new subagents anywhere, write `state.json: aborted` with the reason, write `failures.md`, hand back to `senate`. Do **not** treat sibling successes as invalid; they are part of the run record.

**Commit pattern (mandatory).** For each completed subagent result, the moderator's loop is: receive → write transcript line (atomic append) → append deltas to `context.md` / `agents/<cli>.md` → update `state.json.last_activity_at` (temp file + rename) → discard the result object. Do not retain `text` or `parsed_output` in your context after commit; reread `transcript.jsonl` if a later step needs them.

**Subagent crash / malformed return.** A dispatched subagent may fail to return a structured result — tool failure, hard timeout outside the inner `timeout` wrapper, malformed JSON. In that case:

1. Treat the missing turn as `error.kind = "unknown"` for the purposes of `transcript.jsonl` and `failures.md`.
2. **Restore the log invariant before writing the transcript line:** check whether `<turn-dir>/stdout.log` exists (where `<turn-dir>` is `stages/<n>-<name>/turns/<NNN>-<cli>-<role>/`); if not, create it as an empty file (`: > <path>`) so the `log_path` invariant ("always resolves") still holds. Do the same for `<turn-dir>/stdout.r1.log` only if it exists partially or its presence is implied by what the subagent did before crashing — otherwise leave `retry_log_path` as `null`.
3. Synthesize the transcript line: `text: ""`, `exit_code: null`, `retry_count: 0`, `stderr_tail: "<reason the subagent gave, or 'subagent_crash'>"`, `structured` omitted, `log_path` set to the (now-guaranteed-existing) first-attempt path, `retry_log_path` per the rule above.
4. Apply the format's fallback rule (same as any other terminal error).
5. The escalation rules in `references/failures.md` § Escalation still apply, with the synthetic `unknown` error counting toward `unknown`-error escalation thresholds. A subagent crash is never `auth` (auth would have been detected and returned by a working subagent), so do not abort the run on a single crash; rely on the existing escalation policy.

**What the moderator owns** (never delegate these to the subagent — they need the wider run state):

- Building the prompt (needs `context.md`, `agents/<cli>.md`, transcript slice).
- Appending to `transcript.jsonl` (sole writer; subagent never touches it).
- Updating `context.md` and `agents/<cli>.md` from the deltas (sole writer; serialized in turn-id order).
- Atomic `state.json` updates: `last_activity_at` at every turn boundary, full re-write at every stage boundary and checkpoint per `../senate/references/workspace.md`.
- Failure escalation, re-plan callbacks, checkpoint decisions.

### 5. Adaptive moderation

The agenda is the plan, not a script. When reality diverges, decide whether to:

- **Continue as planned** — minor variance (one slow turn, one transient retry inside the subagent). Default. Note: contract re-prompts are owned by the per-turn subagent (§4a) and are invisible to this loop unless they fail twice.
- **Apply format fallback** — subagent returned `error.kind == "contract_violation"` (the in-subagent re-prompt did not recover the reply) or another terminal error per `references/failures.md`. Per the format file's fallback rule.
- **Pause for the user** — checkpoint hit, or stage failed catastrophically (all agents refused, budget exhausted). Per `references/checkpoints.md`.
- **Call back to `debate-agenda` for a re-plan** — the situation has changed in a way the plan didn't anticipate (user changed direction, an agent kept refusing across stages, a checkpoint was rejected with a request for new structure). Pass: prior agenda, recent transcript slice, the reason. Receive: revised agenda. Resume at the next unfinished stage.

The bias should be toward continuing; only escalate when continuing would clearly produce a worse run.

#### Plan-validate-execute gate for destructive transitions

For any transition that mutates `agenda.md`, `state.json`, or already-written stage verdicts — specifically: **roster swap mid-run, format swap, stage insertion or deletion, abort, resume-from-revise, or re-plan callback** — do not mutate in place. Run this gate first:

1. **Plan.** Write the intended mutation as a single self-describing block (e.g., diff of the agenda's `## Stages` section, or the exact `state.json` field changes, plus a one-line reason).
2. **Validate.** Check the plan against:
   - `agenda-schema` (every `cli` resolves to a playbook; every `format` resolves to a format file; every `input_bindings` references an earlier stage's `output_bindings`).
   - The `state.json` schema in `../senate/references/workspace.md`.
   - Invariants: no rewriting of completed stages' verdicts; no breaking the append-only `transcript.jsonl`; no skipping a `required` checkpoint.
   - For a re-plan callback: the planner's revised agenda passes the same pre-flight checks as step 1 above.
3. **Execute.** Apply the mutation. For agenda changes, **the planner is the only writer of `agenda.md`** — call it back rather than editing the file yourself, and append a `## Revisions` entry. For `state.json`, write atomically (temp file + rename). For abort, persist the abort reason in `state.json` before pausing.

If any validation step fails, do not execute. Surface to the user via `senate` with the plan and the failed check.

### 6. Stage completion

When a stage's termination condition fires (per the format file), the moderator:

- Runs the stage's synthesis turn — one designated role per the format (speaker / judge / editor / synthesizer). The synthesis turn's structured output and prose become the stage's verdict content.
- Writes the stage's verdict to `<run-dir>/stages/<index>-<name>/verdict.md`. Every run has at least one stage (single-stage runs get `stages/1-<format>/`), so this is always a real path. The verdict's content is the synthesis turn's structured output and prose.
- Extracts `output_bindings` and writes them to `<run-dir>/bindings.json` (cumulative across stages).
- Honors any checkpoint declared on this stage.

The moderator does **not** write the top-level `<run-dir>/notes.md` — that is `meeting-note`'s job. The format-level "speaker writes the verdict" wording refers to the synthesis turn's *content production*; the moderator writes that content to `stages/<N>/verdict.md` (the bindings target), and the scribe folds it into `notes.md` after the run.

### 7. Hand off

When the last stage finishes:

- Update `<run-dir>/state.json`: `status: completed`, `completed_at: "..."`. Full schema in `../senate/references/workspace.md` (`## state.json schema`).
- Return to `senate` with a one-line summary and the path to the run dir.

`senate` then invokes `meeting-note`, which writes the user-facing `notes.md` (the merged file that replaces the old `verdict.md` + `meeting-notes.md` pair). The moderator never writes `notes.md`. The moderator does write per-stage `stages/<n>/verdict.md` files (the bindings target).

## Single-stage vs multi-stage

There is one code path. A single-stage agenda walks one stage; a multi-stage agenda walks N. Bindings, checkpoints, and re-planning all work the same way.

## Resume from pause

If the moderator is invoked on a run dir that already has `transcript.jsonl` content, follow the full resume / crash-recovery / revise / re-plan flows in `references/checkpoints.md`. The moderator owns `state.json`; the planner owns `agenda.md`. After the appropriate flow, continue from the first unfinished stage per the (possibly revised) agenda.

## Files in this skill

- `SKILL.md` — this file.
- `references/context.md` — `context.md` (shared scratchpad) and per-agent memory file conventions.
- `references/contracts.md` — structured-output contract discipline.
- `references/failures.md` — error taxonomy and retry policy.
- `references/budget.md` — wall-clock, token, and per-turn caps.
- `references/checkpoints.md` — human-in-the-loop pause / resume.

## Related skills

- `../debate-agenda/` — produces the `agenda.md` this skill consumes; called back for mid-run re-plans. Format library at `../debate-agenda/formats/`.
- `../invoke-agent/` — per-CLI invocation playbooks, read inside the per-turn subagent for the CLI it is about to invoke.
- `../meeting-note/` — runs after the moderator finishes; consolidates the transcript into user-facing notes.
