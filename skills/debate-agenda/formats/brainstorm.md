# brainstorm

## Summary

Diverge aggressively, then converge. Three phases: everyone generates freely with no critique allowed; ideas are clustered and ranked; top-k ideas are developed in depth. Best for early-stage exploration where the goal is **optionality, not decision** — feature ideation, naming, API shape exploration, research directions.

The defining rule: **no criticism in phase 1**. Critical feedback in the divergent phase collapses diversity and leaves you with the most defensible idea, not the best idea.

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

Output contract: markdown with those four sections.

## Termination

- After phase 4. Brainstorm does not make decisions — it produces options.
- Common follow-up: feed the top option(s) to a `parliament` or `committee` for a decision.

## Defaults

- **n_ideas per generator** (phase 1): 7. Range 5–10.
- **top_k** (phase 3): 3. Range 2–5.
- **Roster size**: 3–6.
- **Agent failure**: missing generator in phase 1 = fewer ideas, brainstorm continues; missing converge turn = that cluster is skipped in phase 4 with a note.
- **Strict no-criticism rule**: if any phase-1 reply contains critique language ("but this won't work", "the problem with X is"), the moderator re-prompts once with the rule restated.
