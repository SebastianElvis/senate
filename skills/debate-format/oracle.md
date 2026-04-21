# oracle

## Summary

A questioner consults a panel of domain experts. Experts answer **independently and without cross-talk**; a synthesizer then combines their answers. Best for *"what do we need to know before deciding X?"* — any question where the goal is to surface relevant considerations, not to reach a decision. Differs from parliament (no voting) and from consensus (no iteration).

The structural commitment: **experts never see each other's answers**. This preserves independence of error — two experts agreeing is signal only if they couldn't have been influenced by each other.

## Roles

| Role | Brief |
| --- | --- |
| `questioner` | Frames the question for the panel, potentially refining it after seeing initial answers. |
| `expert` | Answers from a specific perspective / discipline. The orchestrator assigns each expert a named domain (e.g., "security expert", "performance expert", "pragmatist"). |
| `synthesizer` | Reads all expert answers, produces the combined response. |

Minimum: questioner + 2 experts + synthesizer = 4. Typical: questioner + 3–4 experts + synthesizer = 5–6.

## Phases

### 1. Frame — **sequential**, single turn

Role: `questioner`.

Prompt:

```
You are the questioner consulting a panel of experts on: {task}

Produce the question(s) for the panel. Be specific. For each question, state:
- what you want to know,
- what it would change in your decision,
- any assumptions you want the expert to challenge.

The panel's composition is:
{list of expert_role + assigned domain}

End with the question(s) clearly numbered.
```

Output contract: free text, must contain a numbered question list.

### 2. Expert answers — **parallel**

Roles: all `expert`s. **Strict isolation**: each expert's `transcript_slice` contains only phase 1 (the framing), never other experts' answers.

Prompt:

```
You are the {expert_domain} expert on a panel consulted on: {task}

The questioner's framing and questions are below.

{framing}

Answer from your domain perspective. For each numbered question:
- your answer, in 100–300 words,
- the evidence or reasoning,
- what you are NOT qualified to say (where this question extends beyond your domain).

Do not try to cover the ground other experts would cover. Stay in your lane.
```

Output contract: free text, one numbered section per question.

### 3. Refinement (optional) — **sequential**, one turn

Role: `questioner`.

Triggered only if the orchestrator detects divergent answers (experts fundamentally disagree on a factual point).

Prompt:

```
You are the questioner. The experts' answers are below.

{transcript_slice: expert answers}

Experts gave conflicting answers on:
{auto-detected divergence points}

Produce at most 3 narrower follow-up questions that would resolve the disagreement. Do not take sides.
```

If the orchestrator cannot auto-detect divergence (hard to do reliably), skip this phase.

### 3b. Follow-up expert answers — **parallel**

If phase 3 fired. Experts answer the follow-ups using the same isolation rule.

### 4. Synthesis — **sequential**, single turn

Role: `synthesizer`.

Prompt:

```
You are the synthesizer. All expert answers are below.

{transcript_slice: full}

Produce the oracle verdict as a markdown document:

- **Question** — the original task, restated crisply.
- **Panel composition** — who the experts were (domains only).
- **Key answers** — for each of the questioner's numbered questions, what the experts said. Note where they agreed and where they diverged.
- **What we now know** — the synthesized answer, written as if briefing a decision-maker.
- **What we still don't know** — open points, named explicitly.
- **Confidence** — high / medium / low, with reasoning.
```

Output contract: markdown with those six sections.

## Termination

- After phase 4. Oracle does not produce a decision — it produces information.
- Common follow-up: feed the verdict into a `court`, `parliament`, or `committee` for the actual decision.

## Defaults

- **Experts**: 3–4.
- **Follow-up round**: enabled by default; disable with `--no-followup`.
- **Agent failure**: a missing expert answer = that domain is absent from the synthesis; flag in "What we still don't know".
- **Isolation is non-negotiable.** If the orchestrator cannot guarantee that experts do not see each other's turns, do not claim this format produces independent answers.
