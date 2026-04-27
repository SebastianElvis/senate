# court

## Summary

Adversarial format with fixed roles: prosecution attacks, defense defends, judge rules. Best for binary decisions, PR reviews, "is this safe?" questions, or anywhere you want the strongest case for and against a specific proposition. Unlike parliament, court produces a single ruling, not a vote tally.

## Roles

| Role | Brief |
| --- | --- |
| `prosecution` | Attack the proposition. Find the strongest reasons it is wrong, risky, or incomplete. Steelman the objections. Cite specifics (file paths, quotes, scenarios). |
| `defense` | Defend the proposition. Address the prosecution's points directly. Concede where honest; counter where sound. |
| `judge` | Rules on the merits. Does not argue. Weighs both sides, decides, produces the synthesis. |

Optional fourth role:

| `expert_witness` | Called by either side to supply a domain opinion on a narrow factual question. Speaks only when invoked by name in a prior turn. |

Minimum roster: 3 (prosecution, defense, judge). Typical: 3. Max: 4 with an expert witness.

## Phases

### 1. Charge — **sequential**, single turn

Role: `prosecution`.

Prompt:

```
You are the prosecution in a court debate on: {task}

State the charge against this proposition in 200–400 words. List your top 3–5 specific objections, each as a numbered point. Cite concrete details from the task (file paths, diff lines, scenarios) — no vague critiques.
```

Output contract: free text, must contain a numbered list of objections.

### 2. Defense — **sequential**, single turn

Role: `defense`.

Prompt:

```
You are the defense. The prosecution's charge is below.

{transcript_slice: prosecution turn}

Respond in 200–400 words. Address each numbered objection by its number. For each: concede, refute, or refine. Do not introduce unrelated counter-arguments.
```

Output contract: free text, must reference each numbered objection from the charge.

### 3. Cross-examination — **sequential**, `rounds` iterations (default 2)

Roles: `prosecution`, then `defense`, alternating.

Prompt (prosecution's cross):

```
You are the prosecution. The defense's response is below.

{transcript_slice: full so far}

Pick the weakest point in the defense's response and press on it in 100–200 words. Reference the defense turn by number.
```

Prompt (defense's cross):

```
You are the defense. The prosecution's follow-up is below.

{transcript_slice: full so far}

Respond to the prosecution's latest point in 100–200 words. Concede if honest.
```

Output contract: free text, must cite the turn being addressed.

### 4. Expert witness — **optional**, invoked by name

If either side's turn contains a line like `Calling expert witness on <topic>:`, pause and run:

Prompt (`expert_witness`):

```
You are an expert witness called to testify on: {topic}

Context: {the calling turn}

Answer the narrow factual question in 100–200 words. Do not take a side. Do not speculate beyond the question.
```

Output contract: free text.

### 5. Ruling — **sequential**, single turn

Role: `judge`.

Prompt:

```
You are the judge. The full argument is below.

{transcript_slice: full}

Issue your ruling on: {task}

Produce a markdown document with sections:

- **Decision** — one of: sustain (prosecution wins), dismiss (defense wins), remand (unresolved, needs more info).
- **Reasoning** — weigh the strongest points from each side, cite turn numbers.
- **Dissent** — the strongest argument you ruled against, fairly stated.
```

Output contract: markdown with those three sections. The judge's ruling becomes the synthesis content; `meeting-note` writes the canonical `verdict.md` from it (see `../../meeting-note/references/verdict-schema.md`).

## Termination

- After phase 5 completes.
- Early exit allowed: if either side says "we concede" in a cross turn, skip remaining cross-examination rounds and go straight to ruling.

## Defaults

- **Rounds** (cross-examination): 2. Cap at 4.
- **Roster size**: 3 (required) or 4 (with expert witness).
- **Agent failure**: if prosecution or defense fails a turn twice, the other side wins by default and the judge's ruling notes the forfeiture.
