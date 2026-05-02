# brainstorm

## Defining commitment

**Divergent generation under a strict no-criticism rule, then convergent selection.** Output is **options, not decisions** — feature ideation, naming, API shape exploration, research directions. The no-criticism rule in the divergent phase is structural: critical feedback during divergence collapses diversity and leaves you with the most defensible idea, not the best idea.

## Boundary conditions

- Phase 1 is criticism-free. The phase-1 contract's `no_critique_language` validator (enforced by the per-turn subagent) catches critique language and re-prompts once on the shared retry path.
- At least 2 generators + facilitator. Generators produce; facilitator clusters and selects.
- Output is a set of developed options + recommended next steps, not a ruling, not a vote, not a deliverable.

## Anti-drift fence

| If the task is… | The right primitive is… |
| --- | --- |
| "Pick one of these options" | parliament (vote) or court (rule) |
| "Co-author a shared draft" | committee |
| "Independent reviewers critique a submission" | peer-review |
| "Find what's wrong with this proposal" | red-team |

## Summary

Three phases: everyone generates freely with no critique allowed; ideas are clustered and ranked; top-k ideas are developed in depth. Common follow-up: feed the top option(s) to a `parliament` or `committee` for a decision.

## Roles

| Role | Brief |
| --- | --- |
| `generator` | Produces ideas in the divergent phase, ranks in the clustering phase, develops in the convergent phase. All participants are generators. |
| `facilitator` | Runs the clustering and final selection. Does not generate ideas. |

Minimum: 2 generators + facilitator = 3. Typical: 3 generators + facilitator = 4. Max: 5 generators + facilitator = 6. More than 5 generators produces too many ideas to cluster meaningfully.

## Phases

### 1. Diverge — **parallel**

Roles: all `generator`s.

Prompt:

```
You are a generator in a brainstorm on: {task}

Produce {n_ideas} distinct ideas. Ideas should span the range — from conservative / obvious to bold / unusual. Variety is more important than polish.

Format each idea as:

- **Title** (max 8 words)
- **One-sentence description**

Do NOT critique ideas, yours or anyone else's. Do NOT prioritize. Do NOT explain at length. Just generate.

Produce all {n_ideas} ideas in one reply.
```

`{n_ideas}` defaults to 7 per generator.

Output contract: free text, each idea formatted per template. Parsing rule: count "**" bolded titles; should equal `n_ideas`.

#### Contract: `brainstorm-idea-list`

The moderator passes this contract to the per-turn subagent (see `../../moderate-debate/references/contracts.md` and `../../moderate-debate/SKILL.md` §4a):

- **Schema** — free-text reply with `n_ideas` bolded titles (no fenced JSON expected); this validates `text` only and produces no separate `parsed_output`.
- **Example** — see the prompt template above.
- **Extraction rule** — the whole reply text.
- **Re-prompt template** — `Your previous reply did not produce {n_ideas} distinct ideas in the required format, or contained critique language. Reply now with exactly {n_ideas} ideas, each starting with "- **Title**" followed by a one-sentence description, and no critique of any idea.`
- **Validators**:
  - `idea_count` — count of lines matching `^- \*\*` equals `n_ideas`.
  - `no_critique_language` — reply does not match `\b(but this won't work|the problem with [A-Za-z]+ is|won't scale|too complex|that's wrong|bad idea)\b` (case-insensitive). This enforces the strict no-criticism rule from § Defaults.

### 2. Cluster — **sequential**, single turn

Role: `facilitator`.

Prompt:

```
You are the facilitator. All ideas from all generators are below.

{transcript_slice: diverge phase}

Cluster ideas by theme. For each cluster:

- Name the cluster.
- List member ideas by generator + title.
- Identify the "archetype" idea best representing the cluster.

Then produce a ranked list of clusters. Ranking criterion: **diversity of perspectives × likely user value**. Not "most polished" — novelty counts.

End with a fenced json block:

```json
{"clusters_ranked": ["cluster_name_1", "cluster_name_2", "..."], "top_k": 3}
```
```

Output contract: free text (clustering) + fenced json (rank). Top-k defaults to 3.

### 3. Converge — **parallel** for each of top-k, then **sequential** merge

For each of top-k clusters, assign one generator (rotating) to develop it in depth.

Generator prompt (for cluster X):

```
You are a generator assigned to develop cluster "{cluster_name}". The archetype idea is:

{archetype_idea}

Related ideas from the brainstorm:

{related_ideas}

Develop this into a concrete proposal in 300–600 words. Include:
- refined description,
- how it solves the underlying task,
- the most important risk / objection,
- a rough sketch of what "doing it" looks like.

You are advocating for this cluster — make the strongest case. Criticism comes later.
```

Output contract: free text.

### 4. Selection — **sequential**, single turn

Role: `facilitator`.

Prompt:

```
You are the facilitator. The top-k developed proposals are below.

{transcript_slice: converge phase}

Produce the brainstorm verdict as a markdown document with sections:

- **Top options** — the developed proposals, numbered.
- **Recommended next step** — which option(s) warrant further exploration, and why. May recommend multiple.
- **Dropped clusters** — any cluster worth naming that didn't make top-k, with one line on why.
- **Open questions** — what a follow-up brainstorm or decision-format should tackle.
```

Output contract: markdown with those four sections. The facilitator's reply becomes the synthesis content. The moderator writes it to `stages/<N>/verdict.md` (schema in `../../meeting-note/references/verdict-schema.md`); the scribe folds it into the run-wide `notes.md`.

## Termination

- After phase 4. Brainstorm does not make decisions — it produces options.
- Common follow-up: feed the top option(s) to a `parliament` or `committee` for a decision.

## Defaults

- **n_ideas per generator** (phase 1): 7. Range 5–10.
- **top_k** (phase 3): 3. Range 2–5.
- **Roster size**: 3–6.
- **Agent failure**: missing generator in phase 1 = fewer ideas, brainstorm continues; missing converge turn = that cluster is skipped in phase 4 with a note.
- **Strict no-criticism rule**: the phase-1 contract MUST declare a `validators` entry named `no_critique_language` (regex over the reply prose, matching e.g. "but this won't work", "the problem with X is"; see `../../moderate-debate/references/contracts.md` § "Contract shape" item 5). The per-turn subagent enforces it on the same shared retry path as any other contract violation — re-prompt once with the rule restated if the turn's retry budget is still available; on terminal failure, the subagent returns `error.kind = "contract_violation"` and the moderator applies the format fallback.
