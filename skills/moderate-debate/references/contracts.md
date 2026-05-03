# Structured-output contracts

Every phase that needs to be machine-parsed or mechanically validated declares a contract. The **per-turn subagent** (see `../SKILL.md` §4a) validates the agent's reply against the contract; on first failure it re-prompts the CLI once if the turn's shared retry budget is still available; on second failure (or first failure after that budget was already consumed) it returns `error: { "kind": "contract_violation" }` and the **moderator** applies the format's fallback rule (usually: abstain / forfeit / reuse last draft). The moderator never sees the raw reply — it acts only on the subagent's structured result.

This is the single most important reliability lever in the system. Conventions rot. Contracts do not.

## Contract shape

A contract has up to five parts (the first four are required):

1. **Schema** — either a JSON-shaped skeleton specifying required keys, types, and enums, or a free-text structure that can be checked deterministically.
2. **Example** — a concrete, well-formed instance. Showing, not just telling.
3. **Extraction rule** — how to pull the structured block out of the agent's full reply.
4. **Re-prompt template** — the exact text to send back to the agent on a first failure.
5. **Validators** *(optional)* — a list of named, free-form predicates the subagent runs against the agent's reply alongside schema validation. Each entry has a `name`, a one-sentence description, and a check (regex, substring match, or short rule the subagent can evaluate from the reply text alone — no external state). Failure of any validator is treated identically to a schema-validation failure: same shared retry budget, same `error.kind = "contract_violation"` if validation still fails. Validators are how format-level rules like "no critique language in phase 1" (`brainstorm`) ride along on the contract's failure path without needing a separate enforcement mechanism.

Contracts live inline in the format file that requires them. When the moderator reads a format file, it also reads the contract(s) referenced there and forwards the whole contract object to the per-turn subagent (see `../SKILL.md` §4a).

## Extraction

Default extraction rule: find the **last** fenced block labelled `json` in the reply and `jq .` it. Using the last block (not the first) tolerates agents that show their reasoning before the answer.

```bash
awk '/^```json$/{buf="";cap=1;next} /^```$/{if(cap){last=buf;cap=0}} cap{buf=buf"\n"$0} END{print last}' reply.log | jq .
```

If no fenced block is present, fall back to scanning for the first `{` that parses as JSON through end-of-reply. If neither works, it's a contract violation.

The same extraction approach applies to the `context-delta` and `private-delta` blocks (fence label is the only difference); the subagent returns each verbatim string as `context_delta` / `private_delta` and the moderator commits and projects per `../SKILL.md` §4a. Their absence is **not** a contract violation — they are optional.

## Validation

The subagent validates each reply in two passes:

**Pass 1 — schema** (against the extracted object for JSON contracts, or against the extracted reply text for free-text contracts):

- All required keys present.
- Types match.
- Enum values are in the allowed set.
- Numeric ranges respected (e.g., `confidence` in `[0, 1]`).

`jq` is enough for most schema checks. For formats with deeper schemas, consider a reference JSON Schema file under `contracts/`.

**Pass 2 — validators** (against the full reply text and/or the extracted object):

- Run any predicates declared in the contract's `validators` list (see "Contract shape" §5). Each predicate is a short, deterministic check the subagent can evaluate from the reply alone — typically a regex against the prose body or an additional invariant on the extracted object.
- Any validator failure is treated identically to a schema failure for the failure-policy section below: one re-prompt if the shared retry budget is still available; otherwise return `error.kind = "contract_violation"`.
- Validators are not a backdoor for free-form LLM judgment. Keep them mechanical (regex, substring, simple object predicate). If a check requires LLM-grade reasoning, it belongs in a downstream synthesis turn, not a validator.

## Failure policy

On a contract violation:

1. **The subagent re-prompts once if the turn's shared retry budget is still available.** It sends the CLI the verbatim reply it gave, the contract, and an explicit statement that the previous reply did not parse or did not pass a validator — using the contract's own `re-prompt template` (which the format author tailors to the contract's shape: a JSON-shape contract asks for the fenced JSON block, a free-text contract asks for the structural rules to be re-honored). The retry is a fresh CLI invocation, written to `<turn-dir>/stdout.r1.log` / `stderr.r1.log` next to the canonical `stdout.log` (where `<turn-dir>` = `stages/<n>-<name>/turns/<NNN>-<cli>-<role>/`; uniform retry naming used by contract re-prompts and transient CLI retries — see `failures.md`). `retry_count` is set to `1` in the return shape and `retry_log_path` is populated.
   - If the retry budget was already consumed by a `rate_limit`, `timeout`, or exit-0 empty-stdout `unknown` retry before contract validation, do **not** call the CLI again. Return `error: { "kind": "contract_violation" }` immediately with `retry_count: 1`.
2. **On second failure**, the subagent returns `error: { "kind": "contract_violation" }` with the truncated `stderr_tail` and the `text` it did receive. The moderator records the failure line in `transcript.jsonl` (with `"error": "contract_violation"`) and applies the format's fallback rule. Never let a single misbehaving agent block the whole run.
3. **Never silently reinterpret.** Neither the subagent nor the moderator may "guess" what the agent meant. Either it parsed or it didn't.

## Re-prompt template

Every contract must ship with a re-prompt template. The template is itself a string; the subagent fills in the agent's previous reply.

For **JSON-shape contracts** (e.g., `vote`, `refine`, `ruling`), the canonical template is:

```
Your previous reply did not match the required format.

You replied:
---
{previous_reply}
---

Required format (fenced json block, no other text):

{schema_example}

Reply now with ONLY the fenced json block. No prose.
```

For **free-text contracts** (e.g., `brainstorm-idea-list`), the format author writes a template that names the specific structural rules and validators that failed — schema headings, no-critique language, etc. — and asks for a corrected full reply. JSON-only language is wrong here and must not be reused. See the `brainstorm-idea-list` contract block in `brainstorm.md` for an example.

## Canonical contracts

These are reused across formats. Formats may define format-specific contracts inline.

### `vote`

Used by parliament closure votes. (`committee` defines its own format-local `committee-final-vote` contract with `approve` / `approve_with_dissent` / `block` values; see that format file.)

**Schema:**

```json
{
  "vote": "yes" | "no" | "abstain",
  "confidence": 0.0,
  "reason": "..."
}
```

**Example:**

```json
{"vote": "no", "confidence": 0.72, "reason": "The migration risk dominates the projected latency gain."}
```

**Extraction rule:** parse the last fenced `json` block in the reply.

**Re-prompt template:** use the canonical JSON-shape template above with the `vote` schema filled in. Reply must be only the fenced JSON block.

**Fallback on terminal failure:** `abstain` with `confidence: 0` and the raw reply preserved in `transcript.jsonl.text`.

### `ruling`

Used by court. Other formats (red-team, peer-review) define their own verdict contracts inline.

**Schema:**

```json
{
  "decision": "sustain" | "dismiss" | "remand",
  "reasoning_turns": [1, 4, 7],
  "dissent": "..."
}
```

**Example:**

```json
{"decision": "remand", "reasoning_turns": [2, 5], "dissent": ""}
```

**Extraction rule:** parse the last fenced `json` block in the reply.

**Re-prompt template:** use the canonical JSON-shape template above with the `ruling` schema filled in. Reply must be only the fenced JSON block.

**Fallback on terminal failure:** `remand`.

## Adding a new contract

In the format file that needs it, add a `### Contract: <name>` section with the four required parts (schema, example, extraction rule, re-prompt template) and, if the format has free-form rules to enforce, an optional fifth `validators` part. If the contract is general enough to be reused, promote it to this file under "Canonical contracts".
