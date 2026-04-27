# Structured-output contracts

Every phase that needs to be machine-parsed declares a contract. The moderator validates each agent's reply against the contract; on failure, re-prompt once with the contract restated; on second failure, apply the format's fallback rule (usually: abstain / forfeit / reuse last draft).

This is the single most important reliability lever in the system. Conventions rot. Contracts do not.

## Contract shape

A contract has four parts:

1. **Schema** — a JSON-shaped skeleton specifying required keys, types, and (where applicable) enums.
2. **Example** — a concrete, well-formed instance. Showing, not just telling.
3. **Extraction rule** — how to pull the structured block out of the agent's full reply.
4. **Re-prompt template** — the exact text to send back to the agent on a first failure.

Contracts live inline in the format file that requires them. When the moderator reads a format file, it also reads the contract(s) referenced there.

## Extraction

Default extraction rule: find the **last** fenced block labelled `json` in the reply and `jq .` it. Using the last block (not the first) tolerates agents that show their reasoning before the answer.

```bash
awk '/^```json$/{buf="";cap=1;next} /^```$/{if(cap){last=buf;cap=0}} cap{buf=buf"\n"$0} END{print last}' reply.log | jq .
```

If no fenced block is present, fall back to scanning for the first `{` that parses as JSON through end-of-reply. If neither works, it's a contract violation.

The same extraction approach applies to the `context-delta` and `private-delta` blocks defined in `context.md`, only the fence label is `context-delta` / `private-delta` instead of `json`. Their absence is **not** a contract violation — they are optional.

## Validation

Validate the extracted object against the schema:

- All required keys present.
- Types match.
- Enum values are in the allowed set.
- Numeric ranges respected (e.g., `confidence` in `[0, 1]`).

`jq` is enough for most contracts. For formats with deeper schemas, consider a reference JSON Schema file under `contracts/`.

## Failure policy

On a contract violation:

1. **Re-prompt once.** Send the agent the verbatim reply it gave, the contract, and an explicit statement that the previous reply did not parse. Ask for **only the fenced json block** this time.
2. **On second failure**, record the failure in `transcript.jsonl` with `"error": "contract_violation"` and apply the format's fallback rule. Never let a single misbehaving agent block the whole run.
3. **Never silently reinterpret.** Do not try to "guess" what the agent meant. Either it parsed or it didn't.

## Re-prompt template

Every contract must ship with a re-prompt template. The template is itself a string; the moderator fills in the agent's previous reply:

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

## Canonical contracts

These are reused across formats. Formats may define format-specific contracts inline.

### `vote`

Used by parliament, red-team judgment, oracle final tally.

Schema:

```json
{
  "vote": "yes" | "no" | "abstain",
  "confidence": 0.0,
  "reason": "..."
}
```

Example:

```json
{"vote": "no", "confidence": 0.72, "reason": "The migration risk dominates the projected latency gain."}
```

Fallback on double-failure: `abstain` with `confidence: 0` and the raw reply preserved in `transcript.jsonl`.

### `refine`

Used by consensus refine phase, rfc revision.

Schema:

```json
{
  "changed": true,
  "confidence": 0.0,
  "remaining_concerns": ["..."]
}
```

Fallback on double-failure: treat as `{"changed": false, "confidence": 0.0, "remaining_concerns": ["agent failed contract"]}`.

### `ruling`

Used by court, appeals-court, peer-review editor.

Schema:

```json
{
  "decision": "sustain" | "dismiss" | "remand",
  "reasoning_turns": [1, 4, 7],
  "dissent": "..."
}
```

Fallback on double-failure: `remand`.

## Adding a new contract

In the format file that needs it, add a `### Contract: <name>` section with the four parts. If the contract is general enough to be reused, promote it to this file under "Canonical contracts".
