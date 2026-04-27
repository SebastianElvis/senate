# socratic

## Summary

One interviewer, one subject, iterative probing. Interviewer asks the narrowest possible follow-up to the subject's last answer, drilling into a specific claim until it is either clearly supported or clearly false. Best for:

- debugging an agent's reasoning about a specific bug or claim,
- stress-testing a single premise,
- producing a high-confidence "do you really believe X?" assessment.

Not suited for open questions, multi-perspective evaluation, or decisions — this format tests *one thing at a time*.

## Roles

| Role | Brief |
| --- | --- |
| `interviewer` | Asks questions. Never states a position. Each question narrows the scope of the previous answer. |
| `subject` | The agent being probed. Answers each question directly. May concede, refine, or restate. |
| `arbiter` *(optional)* | Reads the exchange and produces the final verdict: was the subject's core claim sustained or overturned? Can be the same role as interviewer if budget is tight. |

Minimum: 2 (interviewer + subject). Typical: 3 with arbiter.

## Phases

### 1. Position statement — **sequential**, single turn

Role: `subject`.

Prompt:

```
You are the subject of a Socratic interview on: {task}

State your position in 150–300 words. Be specific and committed — a vague position cannot be tested. Include:
- your main claim,
- the key reasons you believe it,
- the boundary conditions (when your claim would NOT hold).
```

Output contract: free text.

### 2. Probe rounds — **sequential**, repeated for `rounds` iterations (default 4)

Each round: interviewer asks, subject answers.

Interviewer prompt:

```
You are the Socratic interviewer. The full exchange so far is below.

{transcript_slice: full}

Ask ONE follow-up question. The question must:
- target the narrowest specific claim in the subject's latest answer,
- be answerable in 150 words or less,
- not introduce a new topic — stay on the thread.

Do not state your own opinion. Do not argue. Ask one question.
```

Output contract: free text, must be a question.

Subject prompt:

```
You are the subject. The interviewer asked:

{interviewer question}

Answer directly in 100–250 words. You may:
- defend your position,
- refine it,
- concede that the interviewer's question exposes a flaw.

Be honest. Restating without engaging counts as forfeit.
```

Output contract: free text.

### 3. Verdict — **sequential**, single turn

Role: `arbiter` (or `interviewer` if no separate arbiter).

Prompt:

```
You are the arbiter of this Socratic interview. The full exchange is below.

{transcript_slice: full}

Original claim (from phase 1): {claim}

Produce the verdict as a markdown document:

- **Claim** — the subject's position, restated.
- **Disposition** — one of: sustained / refined / overturned / inconclusive.
- **Key turning point** — the specific turn (by number) where the claim was most stressed. What happened there?
- **What the subject got right.**
- **What the subject got wrong (or couldn't defend).**
- **Confidence** — high / medium / low.
```

Output contract: markdown + trailing fenced json:

```json
{"disposition": "sustained" | "refined" | "overturned" | "inconclusive", "confidence": 0.0-1.0}
```

On contract failure, fallback to `inconclusive`.

## Termination

- After `rounds` probe turns complete, OR
- Early exit when the subject concedes the core claim (detected by phrases like "you're right", "I was wrong", "I concede"), OR
- Early exit when the interviewer signals closure (produces a statement rather than a question two turns in a row).

## Defaults

- **Rounds** (probes): 4. Cap at 8 — beyond this, diminishing returns.
- **Roster size**: 2 or 3.
- **Agent failure**: a missing interviewer turn = probe round skipped; if the subject misses, record as forfeit and go to verdict.
- **Style rule**: if the interviewer states opinions instead of asking questions, re-prompt once with the role brief.
