# red-team

## Defining commitment

N parallel attackers find failure modes; one defender consolidates a response; a judge rules on whether the proposal survives. The defender does not need to "win" — they need to show every identified attack is non-applicable, accepted, mitigated, or unresolved.

## Boundary conditions

- At least one attacker, exactly one defender, exactly one judge. Judge must not be the same CLI as the defender.
- Attackers do not see each other's turns (parallel, isolated). The moderator enforces transcript-slice scoping.
- Output is a ruling: a disposition label + outstanding risks + recommendations.

## Anti-drift fence

| If the task is… | The right primitive is… |
| --- | --- |
| "Adversarial decision with a clear for/against" | court |
| "Independent reviewers each judge in isolation" | peer-review |
| "Many parties vote on a proposition" | parliament |
| "Peers co-author a shared draft" | committee |
| "Generate options without committing to one" | brainstorm |

## Summary

Best for security, reliability, and pre-mortem reviews — finding what breaks before it breaks. The asymmetry (many attackers, one defender) is structural: parallel attackers broaden coverage; the defender treats every attack honestly rather than deflecting.

## Roles

| Role | Brief |
| --- | --- |
| `attacker` | Finds ways the proposal breaks. 1–3 attackers; multiple attackers work in parallel to broaden coverage. |
| `defender` | Addresses each attack. Owns the proposal. |
| `judge` | Reviews all attacks and defenses, issues a ruling. |

Minimum: 1 attacker + defender + judge = 3. Typical: 2–3 attackers + defender + judge = 4–5.

**Constraint**: judge must NOT be the same CLI as the defender. Attackers must not see each other's turns.

## Phases

### 1. Attack — **parallel**

Roles: all `attacker`s. Each works in isolation; transcript_slice excludes other attackers' turns.

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

**Why challengers do not propose mitigations**: this preserves separation between attack generation and defense judgment, so the judge sees an honest adversarial signal rather than pre-resolved attacks.

### 2. Defense — **sequential**, single turn

Role: `defender`.

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

Output contract: free text, one subsection per input failure mode + disposition label for each. If any failure mode is unaddressed, the per-turn subagent treats it as a contract violation and re-prompts once if the turn's retry budget is still available.

### 3. Judgment — **sequential**, single turn

Role: `judge`.

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

The judge's ruling becomes the synthesis content. The moderator writes it to `stages/<N>-<name>/verdict.md` (schema in `../../meeting-note/references/verdict-schema.md`); the scribe folds it into the run-wide `notes.md`.

## Termination

- After phase 3.
- If the judge needs clarification, they may pose up to 2 narrow follow-ups to either attacker or defender (optional phase 2b) before ruling.

## Defaults

- **Attackers**: 2–3. Use 3 for security-critical reviews.
- **Rounds**: 1.
- **Agent failure**: missing attacker narrows coverage; missing defense = proposal fails by forfeit; missing judgment = rerun with a different CLI.
