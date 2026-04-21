# red-team

## Summary

One or more attackers try to break a proposal; a defender must address each attack; a judge rules on whether the proposal survives. Narrower than court — red-team is specifically about **finding failure cases**, not weighing general merits. Best for:

- security reviews of a protocol, script, or config,
- reliability analysis ("what if this fails mid-migration?"),
- adversarial stress-testing of a plan,
- pre-mortems ("if this project fails, what kills it?").

The defender does NOT need to "win" for the proposal to succeed — they need to show that every identified attack is either non-applicable, acceptable, or has a mitigation.

## Roles

| Role | Brief |
| --- | --- |
| `attacker` | Finds ways the proposal breaks. 1–3 attackers; multiple attackers work in parallel to broaden coverage. |
| `defender` | Addresses each attack. Owns the proposal. |
| `judge` | Reviews all attacks and defenses, issues a ruling: `survives`, `survives_with_mitigations`, `fails`. |

Minimum: 1 attacker + defender + judge = 3. Typical: 2–3 attackers + defender + judge = 4–5.

## Phases

### 1. Attack — **parallel**

Roles: all `attacker`s. Each works independently and does not see other attackers' findings.

Prompt:

```
You are an attacker red-teaming this proposal:

{task}

Find ways this proposal fails. For each failure mode, specify:

- **Name** — short label.
- **Trigger** — the specific condition, input, or event that causes it.
- **Impact** — what goes wrong and who notices.
- **Plausibility** — how likely this is in realistic deployment (low/medium/high).

Produce 3–7 failure modes. Prefer quality over quantity — a plausible failure with a specific trigger is worth 5 vague ones.

Do NOT suggest mitigations. Your job is to find problems, not fix them.

Output format: numbered list, each item with the four fields above.
```

Output contract: free text with a numbered list of at least 3 failure modes, each containing the four fields.

### 2. Defense — **sequential**, single turn

Role: `defender`.

Prompt:

```
You are the defender of this proposal. Attackers have identified the failure modes below.

{transcript_slice: all attack turns, deduplicated by theme}

For each identified failure mode, respond with exactly one of:

- **Non-applicable** — the trigger cannot occur in our deployment context (explain why).
- **Accepted** — we accept this risk (explain the reasoning and the acceptable blast radius).
- **Mitigated** — we have a concrete mitigation (describe it; reference any code, config, or procedural change).
- **Unresolved** — you cannot defend against this attack right now.

Be honest. "Unresolved" is a legitimate answer and is always preferable to hand-waving.

Output format: one subsection per failure mode, named by the attacker's label.
```

Output contract: free text, must have one subsection per input failure mode + disposition label for each. Re-prompt once if any failure mode is unaddressed.

### 3. Judgment — **sequential**, single turn

Role: `judge`.

Prompt:

```
You are the judge of this red-team review.

All attacks and defenses are below.

{transcript_slice: full}

Rule on the proposal. Produce a markdown document:

- **Ruling** — one of:
  - `survives` — all significant attacks were non-applicable or fully mitigated.
  - `survives_with_mitigations` — the proposal is viable once the listed mitigations are implemented.
  - `fails` — at least one high-plausibility attack is unresolved or poorly mitigated.
- **Strongest attacks** — top 2–3 attacks by plausibility × impact.
- **Effective defenses** — defenses that satisfactorily resolved an attack.
- **Outstanding risks** — unresolved or weakly-mitigated attacks; MUST be listed even if ruling is `survives_with_mitigations`.
- **Recommendations** — what must happen before this proposal goes forward.
```

Output contract: markdown + trailing fenced json:

```json
{"ruling": "survives" | "survives_with_mitigations" | "fails", "unresolved_count": 0, "confidence": 0.0-1.0}
```

## Termination

- After phase 3.
- No cross-examination rounds by default. If the judge needs clarification, they may pose up to 2 narrow follow-ups to either attacker or defender (optional phase 2b) before ruling.

## Defaults

- **Attackers**: 2–3. Use 3 for security-critical reviews.
- **Rounds**: 1 (single attack + single defense + single judgment).
- **Agent failure**: a missing attacker narrows coverage; missing defense = proposal fails by forfeit; missing judgment = rerun the judgment with a different CLI.
- **Blind attack**: attackers must not see each other's turns in phase 1.
- **Judge impartiality**: judge should NOT be the same CLI as the defender. Orchestrator enforces.
