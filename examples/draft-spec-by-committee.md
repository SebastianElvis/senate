# Draft a spec by committee

The `committee` format is the right fit when the deliverable is a *document* — an API surface, a spec, an ADR — and you want a single coherent voice on the page. An editor frames the work, members contribute, the editor drafts, members review and vote. The output is the agreed artifact, not a ruling.

## When to pick committee (vs. peer-review or red-team)

- **`committee`** — *"draft this spec together"* — there's no prior draft. Members deliberate; an editor drives the writing and closes on final text. Best when one coherent voice matters.
- **`peer-review`** — *"review this design doc"* — you already have a draft; reviewers critique it independently and an editor adjudicates. Best when there's a single author and you want independent error-checking.
- **`red-team`** — *"find ways this could fail"* — adversarial pressure, not co-authorship.

If you don't have a draft yet and want to *jointly produce* one, `committee` fits. If you do, `peer-review` fits.

## The situation

You're designing the public REST API for a new "saved searches" feature. There's no draft yet. You want the team to deliberate, an editor to write the spec from member input, and members to vote on whether to publish — endpoints, request/response shapes, error model, pagination, auth.

## The prompt

```
Run a committee debate between codex, gemini, kimi, and claude on the
REST API for a "saved searches" feature.

Requirements:
- Authenticated users can create, list, update, and delete saved searches.
- A saved search is a name + a query string + optional filters + created_at.
- Up to 50 per user.
- List responses must paginate.

Deliverable: a single agreed design doc — endpoints, request/response
shapes, error model, pagination strategy, and a one-paragraph rationale
for each non-obvious choice.

Roster:
- codex, gemini, kimi as members
- claude as editor (drives drafting, closes on final text)
```

A few notes on the prompt:

- **State the requirements explicitly.** Members deliberate on those facts; if they're not pinned, the draft drifts.
- **Name the deliverable's shape.** "A single agreed design" with the sections you want. Otherwise members talk past each other.
- **Pick an editor deliberately.** The editor is not the "most important" member; it's the writer. A model with strong synthesis (claude is a common pick) usually fits.

## Recommended roster

| Role | Suggested CLI | Why |
| --- | --- | --- |
| `member` | `codex` | Strong at concrete API shapes and edge cases. |
| `member` | `gemini` | Tends to surface idiomatic patterns from across ecosystems. |
| `member` | `kimi` | Often surfaces angles other members didn't raise. |
| `editor` | `claude` | The editor drives drafting and closes on final text. Reusing one of the member CLIs as editor is allowed but generally weaker — the editor's coherence work is easier when not also voicing a position. |

A committee needs at least 2 members plus an editor; 3–4 members is the sweet spot. Past 5 members the review rounds get long without producing more signal.

## What you'll see during the run

The orchestrator mints `<cwd>/.senate/runs/<id>-committee/` and runs six phases:

1. **Framing** — the editor writes a one-paragraph framing of the task (scope, out-of-scope, deliverable shape).
2. **Member input** — every member contributes their view in parallel: most important point, easily-overlooked considerations, framing objections. Members do not write the doc.
3. **Draft** — the editor writes draft 1 from member input, listing open points where members disagreed or the editor made a judgment call.
4. **Review rounds** (default 2) — members comment on the current draft (parallel), then the editor revises (sequential). This loop is what distinguishes committee from peer-review: members react to revised text and to other members' critiques across rounds.
5. **Closure vote** — every member submits a fenced JSON block: `{"vote": "approve" | "approve_with_dissent" | "block", "confidence": ..., "dissent_point": "..."}`.
6. **Publication** — the editor publishes the final document with a "Committee disposition" footer recording approvals, dissent, and round count.

Termination: phase 5 fires after the configured rounds; phase 6 always runs. If a `block` vote is cast, the editor either revises once more or publishes with the dissent recorded as a blocking minority opinion (default: publish with dissent).

## How to read the verdict

`notes.md` is the agreed design (the run-wide user-facing summary; the underlying stage verdict is at `stages/1-committee/verdict.md`). The committee disposition tells you how to weight it:

- **All `approve`** → uncontested. Adopt the spec.
- **Some `approve_with_dissent`** → mostly agreed, but at least one member flagged a concern in `dissent_point`. Read those before adopting; sometimes they're the bug.
- **Any `block`** → a member explicitly objected. The editor either revised or published over the block; read the dissent and decide if the block was substantive.

## Common pitfalls

- **Under-specified requirements.** Committee exposes ambiguity through member disagreement. If members keep disagreeing on the same axis (e.g., one wants cursor pagination, another offset), the requirement on pagination wasn't pinned. Re-prompt with a concrete constraint and re-run.
- **Editor doing too much.** The editor synthesizes member input; it shouldn't be inventing positions members didn't raise. If the published draft reads like a fourth opinion rather than a synthesis of three, the editor overstepped — note it and re-run with a different editor.
- **Round count too low.** Default is 2. For genuinely complex designs (auth flows, schema evolution, multi-step workflows), bump to 3–4. *"rounds: 4"* in the prompt overrides the default.
- **Treating dissent as failure.** A `committee` that publishes with `approve_with_dissent` is doing its job — it's the format that records minority opinion explicitly.

## After the run

- **Adopt or refine.** The artifact is yours to take. If members all `approve`d, you have a design. If there's dissent, treat the `dissent_point` as the open question to resolve before shipping.
- **Spec it.** Committee is good at the *shape* of an API; specifying it (OpenAPI, types) is downstream work. Hand the artifact to a single model and ask it to produce the formal spec — that's not a debate, that's transcription.
- **Validate.** Once the design is committed, the next debate worth running is a `red-team` on the design — *"find failure modes in this saved-searches API"*. Committee produces designs the team agreed on; `red-team` finds the cases none of them thought of.
