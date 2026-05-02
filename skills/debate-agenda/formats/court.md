# court

## Defining commitment

Resolution is by **arbiter judgment** — not by vote tally, not by convergence. One or more parties argue against (and optionally for) a proposition, claim, prior verdict, or plan; an arbiter weighs the arguments and issues a ruling.

## Boundary conditions

- At least one challenging party. Court does not run with only a defender.
- Exactly one arbiter, who never argues. The arbiter's ruling is terminal — no vote, no convergence check.
- Arbiter must not be the same agent as any challenger or defender (orchestrator enforces).
- Output is a ruling: a disposition label + reasoning citing turn numbers + a stated dissent or strongest counter.

## Anti-drift fence

| If the task is… | The right primitive is… |
| --- | --- |
| "Many parties vote on a proposition" | parliament |
| "Peers co-author a shared draft" | workshop |
| "Independent reviewers each judge in isolation" | panel |
| "Generate options without committing to one" | brainstorm |

## Presets

Court is a **closed family of four named presets**. Each preset specifies a complete role/phase/contract/synthesis spec. Arbitrary parameter combinations are undefined — pick a named preset.

| Preset | structure | contract | input_type | When to pick |
| --- | --- | --- | --- | --- |
| `court` | symmetric | free_argument | task | Adversarial decisions with a clear for/against (PR review, "is X safe to merge"). |
| `appeals-court` | symmetric | free_argument | prior_verdict | Auditing a prior court verdict for error. |
| `red-team` | asymmetric | structured_failure_modes | task | Security / reliability / failure-mode hunts; pre-mortems. |
| `socratic` | probe | claim_test | claim | Stress-testing one specific claim or reasoning chain. |

The agenda's stage declares `format: court` plus `preset: <name>`. The moderator reads this file and uses the preset's section below.

---

## Preset: `court` (symmetric, free_argument, task)

### Roles

| Role | Brief |
| --- | --- |
| `prosecution` | Attack the proposition. Find the strongest reasons it is wrong, risky, or incomplete. Steelman the objections. Cite specifics (file paths, quotes, scenarios). |
| `defense` | Defend the proposition. Address the prosecution's points directly. Concede where honest; counter where sound. |
| `judge` | Rules on the merits. Does not argue. Weighs both sides, decides, produces the synthesis. |
| `expert_witness` *(optional)* | Called by either side to supply a domain opinion on a narrow factual question. Speaks only when invoked by name in a prior turn. |

Minimum roster: 3 (prosecution, defense, judge). Typical: 3. Max: 4 with an expert witness.

### Phases

#### 1. Charge — **sequential**, single turn

Role: `prosecution`.

```
You are the prosecution in a court debate on: {task}

State the charge against this proposition in 200–400 words. List your top 3–5 specific objections, each as a numbered point. Cite concrete details from the task (file paths, diff lines, scenarios) — no vague critiques.
```

Output contract: free text, must contain a numbered list of objections.

#### 2. Defense — **sequential**, single turn

Role: `defense`.

```
You are the defense. The prosecution's charge is below.

{transcript_slice: prosecution turn}

Respond in 200–400 words. Address each numbered objection by its number. For each: concede, refute, or refine. Do not introduce unrelated counter-arguments.
```

Output contract: free text, must reference each numbered objection from the charge.

#### 3. Cross-examination — **sequential**, `rounds` iterations (default 2)

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

#### 4. Expert witness — **optional**, invoked by name

If either side's turn contains a line like `Calling expert witness on <topic>:`, pause and run:

```
You are an expert witness called to testify on: {topic}

Context: {the calling turn}

Answer the narrow factual question in 100–200 words. Do not take a side. Do not speculate beyond the question.
```

Output contract: free text.

#### 5. Ruling — **sequential**, single turn

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

### Termination

- After phase 5.
- Early exit allowed: if either side says "we concede" in a cross turn, skip remaining cross-examination and go to ruling.

### Defaults

- **Rounds** (cross-examination): 2. Cap at 4.
- **Roster size**: 3 or 4 (with expert witness).
- **Agent failure**: if prosecution or defense fails twice, the other side wins by default and the ruling notes the forfeiture.

---

## Preset: `appeals-court` (symmetric, free_argument, prior_verdict)

Re-examines a prior `court` verdict with a **different** roster, looking for errors in the original ruling. Does not re-litigate the underlying facts.

**Input requirement**: a prior `run_id` for a court run (or any preset of court that produced a ruling). If invoked without one, ask the user which run to appeal.

**Roster constraint**: at least the `appeals_judge` must be a different CLI than the original `judge`. If feasible, all three roles use different CLIs than the original.

### Roles

| Role | Brief |
| --- | --- |
| `appellant` | Argues the original ruling was wrong. Typically takes the losing side's position. |
| `respondent` | Argues the original ruling was right. Typically takes the winning side's position. |
| `appeals_judge` | Rules on the appeal. Does NOT re-rule on the underlying case. Only answers: did the original ruling stand on sound reasoning? |

Minimum: 3. No juries or witnesses.

### Phases

#### 1. Case review — **sequential**, single turn

Role: `appeals_judge`.

```
You are an appeals judge. A prior court has ruled on this task:

{original_task}

The original roster was:
{original_roster}

The original ruling was:

{original_verdict}

Read the original transcript (below) and produce a neutral case summary in 200–400 words. Identify:
- the core question the court answered,
- the original ruling's disposition (sustain / dismiss / remand),
- the reasoning the original judge cited.

Do NOT opine on whether the original was correct. That comes after the appeal.

{transcript_slice: original full transcript}
```

Output contract: free text.

#### 2. Appeal — **sequential**, single turn

Role: `appellant`.

```
You are the appellant. The original ruling went against your position. Case summary:

{case_summary}

Argue the ruling was in error in 300–500 words. You may argue:
- **Factual error** — the judge misread the evidence (cite specific original turn numbers).
- **Procedural error** — the judge relied on a point neither side actually argued.
- **Reasoning error** — the judge's stated rationale does not actually support the disposition.
- **Missing consideration** — a decisive point was raised but not addressed in the ruling.

Do NOT introduce new arguments that could have been raised at trial. Appeal is limited to errors in the prior proceeding.
```

Output contract: free text, must name at least one error class above.

#### 3. Response — **sequential**, single turn

Role: `respondent`.

```
You are the respondent. The appellant's claim of error is below.

{appeal turn}

Respond in 300–500 words. For each alleged error, defend the original ruling or concede. You may cite the original transcript's turn numbers to support your defense.
```

Output contract: free text.

#### 4. Appellate ruling — **sequential**, single turn

Role: `appeals_judge`.

```
You are the appeals judge. The appeal, response, and original case are all before you.

{transcript_slice: full appeal}

Rule on the appeal. Produce a markdown document:

- **Original ruling** — restated one line.
- **Appeal disposition** — one of:
  - `affirmed` — the original ruling stands; appellant's claims of error are insufficient.
  - `reversed` — the original ruling was in error; the appeal prevails.
  - `remanded` — the original proceeding was flawed enough that the case should be re-heard.
- **Reasoning** — weigh each alleged error; cite the original and appeal turn numbers.
- **Scope of ruling** — what this disposition does and does NOT establish about the underlying question.
```

Output contract: markdown + trailing fenced json:

```json
{"disposition": "affirmed" | "reversed" | "remanded", "confidence": 0.0-1.0}
```

On contract failure, fallback to `affirmed` with confidence 0.3 (default toward status quo).

### Termination

- After phase 4.
- On `remanded`, `senate` may offer the user to run a fresh `court` (preset `court`) on the original task as a new run.

### Defaults

- **Rounds**: 1 (no cross-appeal).
- **Roster size**: exactly 3.
- **Agent failure**: if the appellant cannot complete their turn, the appeal is dismissed as abandoned.

---

## Preset: `red-team` (asymmetric, structured_failure_modes, task)

N parallel attackers find failure modes; one defender consolidates a response; a judge rules on whether the proposal survives. The defender does not need to "win" — they need to show every identified attack is non-applicable, accepted, mitigated, or unresolved.

### Roles

| Role | Brief |
| --- | --- |
| `attacker` | Finds ways the proposal breaks. 1–3 attackers; multiple attackers work in parallel to broaden coverage. |
| `defender` | Addresses each attack. Owns the proposal. |
| `judge` | Reviews all attacks and defenses, issues a ruling. |

Minimum: 1 attacker + defender + judge = 3. Typical: 2–3 attackers + defender + judge = 4–5.

**Constraint**: judge must NOT be the same CLI as the defender. Attackers must not see each other's turns.

### Phases

#### 1. Attack — **parallel**

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

#### 2. Defense — **sequential**, single turn

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

#### 3. Judgment — **sequential**, single turn

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

### Termination

- After phase 3.
- If the judge needs clarification, they may pose up to 2 narrow follow-ups to either attacker or defender (optional phase 2b) before ruling.

### Defaults

- **Attackers**: 2–3. Use 3 for security-critical reviews.
- **Rounds**: 1.
- **Agent failure**: missing attacker narrows coverage; missing defense = proposal fails by forfeit; missing judgment = rerun with a different CLI.

---

## Preset: `socratic` (probe, claim_test, claim)

One interviewer + one subject + optional arbiter. Interviewer asks the narrowest possible follow-up to the subject's last answer, drilling into a specific claim until it is either clearly supported or clearly false.

**Acknowledged loose joint**: socratic belongs to the court family by lineage (terminal arbiter judgment), but its force comes from disciplined questioning, not from adversarial sides. It is kept here because the alternative is a sixth primitive whose only member is socratic itself.

### Roles

| Role | Brief |
| --- | --- |
| `interviewer` | Asks questions. **Never states a position**. Each question narrows the scope of the previous answer. |
| `subject` | The agent being probed. Answers each question directly. May concede, refine, or restate. |
| `arbiter` *(optional)* | Reads the exchange and produces the verdict: was the subject's core claim sustained or overturned? Can be the same role as interviewer if budget is tight. |

Minimum: 2 (interviewer + subject). Typical: 3 with arbiter.

### Phases

#### 1. Position statement — **sequential**, single turn

Role: `subject`.

```
You are the subject of a Socratic interview on: {task}

State your position in 150–300 words. Be specific and committed — a vague position cannot be tested. Include:
- your main claim,
- the key reasons you believe it,
- the boundary conditions (when your claim would NOT hold).
```

Output contract: free text.

#### 2. Probe rounds — **sequential**, repeated for `rounds` iterations (default 4)

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

##### Contract: `socratic-question`

The moderator passes this contract to the per-turn subagent for interviewer probe turns (see `../../moderate-debate/references/contracts.md` and `../../moderate-debate/SKILL.md` §4a):

- **Schema** — free-text reply containing exactly one interviewer question; this validates `text` only and produces no separate `parsed_output`.
- **Example** — `What evidence would distinguish your claim from the weaker possibility that the improvement came from caching rather than the new algorithm?`
- **Extraction rule** — the whole reply text.
- **Re-prompt template** — `Your previous reply did not satisfy the Socratic interviewer role. Reply now with exactly one question. Do not state your own opinion, do not argue, and do not add commentary before or after the question.`
- **Validators**:
  - `is_question` — after trimming whitespace, the reply ends with `?` and contains no more than two question marks total.
  - `no_opinion_statement` — reply does not match `\b(I think|I believe|my view|the answer is|clearly|obviously|you should)\b` (case-insensitive).

The per-turn subagent enforces the "ask, don't argue" rule on the same shared retry path as any other contract violation; on terminal failure, the subagent returns `error.kind = "contract_violation"` and the moderator skips that probe turn per the agent-failure fallback.

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

#### 3. Verdict — **sequential**, single turn

Role: `arbiter` (or `interviewer` if no separate arbiter).

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

### Termination

- After `rounds` probe turns complete, OR
- Early exit when the subject concedes the core claim ("you're right", "I was wrong", "I concede"), OR
- Early exit when the interviewer signals closure (produces a statement rather than a question two turns in a row).

### Defaults

- **Rounds**: 4. Cap at 8.
- **Roster size**: 2 or 3.
- **Agent failure**: missing interviewer turn = probe round skipped; if subject misses, record as forfeit and go to verdict.
- **Style rule**: interviewer probe turns MUST use the `socratic-question` contract above. The per-turn subagent enforces the "ask, don't argue" rule on the same shared retry path as any other contract violation; on terminal failure, the subagent returns `error.kind = "contract_violation"` and the moderator skips that probe turn per the agent-failure fallback above.
