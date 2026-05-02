# Design an API by consensus

A `consensus` debate is the right format when the deliverable is a *document* — an API surface, a spec, a plan — and you want multiple models to converge on it. Every contributor is a peer; there are no adversarial roles. The output is the agreed artifact, not a ruling.

## When to pick consensus (vs. committee or peer-review)

- **consensus** — *"design this API together"* — every CLI proposes, all critique each other's drafts, then they iterate until they converge. The output is one merged design.
- **committee** — *"draft a memo / ADR / position paper"* — small group deliberates in private; an editor writes the final doc. Better when you want one voice on the page.
- **peer-review** — *"review this design doc"* — you already have a draft; reviewers critique it independently and an editor adjudicates. Better when there's a single author.

If you don't have a draft yet and want multiple models to *jointly produce* one, consensus fits. If you do, peer-review fits. If you want a polished one-voice document, committee fits.

## The situation

You're designing the public REST API for a new "saved searches" feature. There's no draft yet. You want three models to each propose a full API surface, critique each other's proposals, and converge on one design — endpoints, request/response shapes, error model, pagination, auth.

## The prompt

```
Drive consensus between codex, gemini, and claude on the REST API for a
"saved searches" feature.

Requirements:
- Authenticated users can create, list, update, and delete saved searches.
- A saved search is a name + a query string + optional filters + created_at.
- Up to 50 per user.
- List responses must paginate.

Deliverable: a single agreed design — endpoints, request/response shapes,
error model, pagination strategy, and a one-paragraph rationale for each
non-obvious choice. Claude is the arbiter.
```

A few notes on the prompt:

- **State the requirements explicitly.** Consensus converges on the design, but it can only converge if every contributor sees the same constraints. Don't make them infer.
- **Name the deliverable's shape.** *"A single agreed design"* with the sections you want. Otherwise contributors will produce different artifacts and there's nothing to converge on.
- **Pick an arbiter deliberately.** The arbiter is the orchestration role that decides when consensus is reached and writes the synthesis. It's not the "most important" voice; it's the editor. A model with strong synthesis (claude is a common pick) usually fits.

## Recommended roster

| Role | Suggested CLI | Why |
| --- | --- | --- |
| `contributor` | `codex` | Strong at concrete API shapes and edge cases. |
| `contributor` | `gemini` | Tends to surface idiomatic patterns from across ecosystems. |
| `contributor` | `claude` | Often the contributor that mediates between proposals. |
| `arbiter` | `claude` | The arbiter doesn't contribute content in normal phases; it decides convergence and writes the synthesis. Reusing the same CLI as a contributor is fine. |

A consensus needs at least 2 contributors plus an arbiter; 3–4 contributors is the sweet spot. More than 5 contributors and you'll spend more rounds reconciling than converging.

## What you'll see during the run

The orchestrator mints `<cwd>/.senate/runs/<id>-consensus/` and runs five phases:

1. **Initial proposals** — every contributor independently writes a full draft. These are the candidate designs.
2. **Critique** — each contributor critiques the *other* proposals (not their own): strongest aspect, biggest flaw, one concrete improvement. Done in parallel.
3. **Refine** — every contributor produces a refined draft, ending each turn with `{"changed": true|false, "confidence": 0.0–1.0, "remaining_concerns": [...]}`. Repeated up to `max_rounds` (default 3).
4. **Convergence check** — the arbiter reads all refined drafts after each refine round and decides: converged, not converged, or stalled.
5. **Synthesis** — the arbiter produces the final artifact: **Artifact** (the agreed design), **Confidence** (converged / partial / stalled), **Remaining concerns**, **Process notes**.

Termination: all contributors report `"changed": false` and no `remaining_concerns`, OR the round cap fires (stalled — the arbiter picks the most-supported draft and notes what's outstanding).

## How to read the verdict

`verdict.md` is the agreed design. The **Confidence** field tells you how much weight to put on it:

- **converged** → all contributors stopped changing their drafts. High confidence; the design is genuinely shared.
- **partial** → most converged, but one contributor still had concerns. Skim **Remaining concerns** before accepting.
- **stalled** → the round cap fired without convergence. Read **Remaining concerns** carefully — these are the genuine disagreements. The arbiter picked one draft, but the others didn't endorse it. Often a sign that the *requirements* are under-specified, not that the models disagree.

**Process notes** tells you which contributor's draft became the base and how many rounds it took. Useful for diagnosing whether one model dominated the synthesis.

## Common pitfalls

- **Under-specified requirements.** Consensus exposes ambiguity ruthlessly. If contributors keep disagreeing on the same axis (e.g., one wants cursor pagination, another offset, another both), the requirement on pagination wasn't pinned. Re-prompt with a concrete constraint and re-run.
- **Treating one contributor as the author.** Consensus is symmetric. If you want one model to draft and others to critique, pick **peer-review**, not consensus.
- **Round count too low.** Default is 3. For genuinely complex designs (auth flows, schema evolution, multi-step workflows), bump to 4–5. *"max_rounds: 5"* in the prompt overrides the default.
- **Arbiter doing too much.** The arbiter shouldn't be deciding the design; it's deciding whether the contributors agree. If the verdict reads like a fourth opinion rather than a synthesis of three, the arbiter overstepped — note it and re-run with a different arbiter.

## After the run

- **Adopt or refine.** The artifact is yours to take. If it's `converged`, you have a design. If it's `partial` or `stalled`, treat the **Remaining concerns** as the open questions and either resolve them yourself or re-run consensus on just those points.
- **Spec it.** Consensus is good at the *shape* of an API; specifying it (OpenAPI, types) is downstream work. Hand the artifact to a single model and ask it to produce the formal spec — that's not a debate, that's transcription.
- **Validate.** Once the design is committed, the next debate worth running is a `red-team` on the design — *"find failure modes in this saved-searches API"*. Consensus produces designs that all contributors agree on; red-team finds the cases none of them thought of.
