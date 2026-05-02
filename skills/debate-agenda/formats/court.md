# court

## Defining commitment

Resolution is by **arbiter judgment** — not by vote tally, not by convergence. A challenging party argues against a proposition, a defending party argues for it, and an arbiter weighs the arguments and issues a ruling.

## Boundary conditions

- Exactly one prosecution and one defense. Court does not run with a single side.
- Exactly one judge, who never argues. The judge's ruling is terminal — no vote, no convergence check.
- Judge must not be the same agent as the prosecution or the defense (orchestrator enforces).
- Output is a ruling: a disposition label + reasoning citing turn numbers + a stated dissent or strongest counter.

## Anti-drift fence

| If the task is… | The right primitive is… |
| --- | --- |
| "Many parties vote on a proposition" | parliament |
| "Peers co-author a shared draft" | committee |
| "Independent reviewers each judge in isolation" | peer-review |
| "Find ways this could fail" | red-team |
| "Generate options without committing to one" | brainstorm |

## Summary

Best for adversarial decisions with a clear for/against (PR review, "is X safe to merge"). For "second opinion on a prior court verdict", run a fresh `court` with the prior verdict pasted into the task and a different roster.

## Roles

| Role | Brief |
| --- | --- |
| `prosecution` | Attack the proposition. Find the strongest reasons it is wrong, risky, or incomplete. Steelman the objections. Cite specifics (file paths, quotes, scenarios). |
| `defense` | Defend the proposition. Address the prosecution's points directly. Concede where honest; counter where sound. |
| `judge` | Rules on the merits. Does not argue. Weighs both sides, decides, produces the synthesis. |
| `expert_witness` *(optional)* | Called by either side to supply a domain opinion on a narrow factual question. Speaks only when invoked by name in a prior turn. |

Minimum roster: 3 (prosecution, defense, judge). Typical: 3. Max: 4 with an expert witness.

## Phases

### 1. Charge — **sequential**, single turn

Role: `prosecution`.

```
You are the prosecution in a court debate on: {task}

State the charge against this proposition in 200–400 words. List your top 3–5 specific objections, each as a numbered point. Cite concrete details from the task (file paths, diff lines, scenarios) — no vague critiques.
```

Output contract: free text, must contain a numbered list of objections.

### 2. Defense — **sequential**, single turn

Role: `defense`.

```
You are the defense. The prosecution's charge is below.

{transcript_slice: prosecution turn}

Respond in 200–400 words. Address each numbered objection by its number. For each: concede, refute, or refine. Do not introduce unrelated counter-arguments.
```

Output contract: free text, must reference each numbered objection from the charge.

### 3. Cross-examination — **sequential**, `rounds` iterations (default 2)

Roles: `prosecution`, then `defense`, alternating.

Prosecution prompt:

```
You are the prosecution. The defense's response is below.

{transcript_slice: full so far}

Pick the weakest point in the defense's response and press on it in 100–200 words. Reference the defense turn by number.
```

Defense prompt:

```
You are the defense. The prosecution's follow-up is below.

{transcript_slice: full so far}

Respond to the prosecution's latest point in 100–200 words. Concede if honest.
```

Output contract: free text, must cite the turn being addressed.

### 4. Expert witness — **optional**, invoked by name

If either side's turn contains a line like `Calling expert witness on <topic>:`, pause and run:

```
You are an expert witness called to testify on: {topic}

Context: {the calling turn}

Answer the narrow factual question in 100–200 words. Do not take a side. Do not speculate beyond the question.
```

Output contract: free text.

### 5. Ruling — **sequential**, single turn

Role: `judge`.

```
You are the judge. The full argument is below.

{transcript_slice: full}

Issue your ruling on: {task}

Produce a markdown document with sections:

- **Decision** — one of: sustain (prosecution wins), dismiss (defense wins), remand (unresolved, needs more info).
- **Reasoning** — weigh the strongest points from each side, cite turn numbers.
- **Dissent** — the strongest argument you ruled against, fairly stated.
```

Output contract: markdown with those three sections. The judge's ruling becomes the synthesis content. The moderator writes it to `stages/<N>/verdict.md` (schema in `../../meeting-note/references/verdict-schema.md`); the scribe folds it into the run-wide `notes.md`.

## Termination

- After phase 5.
- Early exit allowed: if either side says "we concede" in a cross turn, skip remaining cross-examination and go to ruling.

## Defaults

- **Rounds** (cross-examination): 2. Cap at 4.
- **Roster size**: 3 or 4 (with expert witness).
- **Agent failure**: if prosecution or defense fails twice, the other side wins by default and the ruling notes the forfeiture.
