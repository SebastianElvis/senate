# senate — Product vision & roadmap

> A library of human-institution coordination patterns, reusable as skills, for orchestrating collaboration between AI coding agents.

## Vision

Human civilization's most durable invention is not any single institution — it is the *design space* of institutions. Parliaments, courts, committees, peer review, juries, tribunals, town halls, standing councils: each is a protocol for turning disagreement among imperfect reasoners into a decision that is *better than any individual* could have produced alone. The protocols differ in what they optimize for — breadth of perspective, adversarial stress, written record, expert deference, consensus — and skilled humans pick the right protocol for the right question.

AI coding agents today mostly do the opposite. We either ask one model, or we chain them with ad-hoc "judge this / refine that" prompts glued together in Python. The result: no record, no repeatable structure, no way to compare *this* debate to *last week's*, no reuse of hard-won facilitation patterns. Every multi-agent setup is reinvented.

`senate` is the thesis that **agent collaboration should borrow, explicitly and literally, from the playbook of human organizations**. Not as metaphor — as protocol. A `parliament` has named roles, turn order, a voting rule, a speaker who writes the minutes. A `court` has prosecution, defense, cross-examination, a ruling. These are not storytelling wrappers; they are coordination mechanisms with centuries of stress-testing behind them.

The product is a growing library of these protocols, packaged as agent skills, runnable from any host (Claude Code, Codex, Cursor, OpenCode, …) against any roster of CLIs. Markdown in, verdict out. Transcripts on disk. No runtime code. Add a protocol by writing a markdown file.

## Why now

- **Multi-agent debate is established science.** [Du et al. 2023](https://arxiv.org/abs/2305.14325), [Liang et al. 2023](https://arxiv.org/abs/2305.19118), [Chan et al. 2023 (ChatEval)](https://arxiv.org/abs/2308.07201), and [Khan et al. 2024](https://arxiv.org/abs/2402.06782) have each shown that structured disagreement among LLMs improves factuality, reasoning, evaluation quality, and truthfulness over single-model baselines. The research validates the *mechanism*; the open question is the *protocol library* — and that's a markdown problem, not a research problem.
- **Skills as a substrate.** The [Agent Skills spec](https://agentskills.io) and `npx skills` distribution mean coordination patterns can ship as pure markdown, installable in one command, compatible across 40+ agents. Before this, cross-agent orchestration needed a runtime. Now it needs a README.
- **Multiple credible CLIs.** Codex, Gemini, Cursor, Kimi, Claude each have genuine strengths and failure modes. The value of a second opinion is higher when the second opinion is *different*, not a checkpoint of the same base model.
- **The "which model is best?" question is dissolving.** It's increasingly clear the right unit is not *model* but *ensemble under a protocol*. `senate` is the library of protocols.

## Non-goals

- **Not a new CLI.** No `senate` binary. No Node runtime. The orchestrating agent drives everything; we ship instructions.
- **Not a general agent framework.** We do not manage tools, memory, or tool-use. We manage *how agents talk to each other*.
- **Not a benchmarking harness** (for now). Eval comes later, as Horizon 2.
- **Not opinionated about which model plays which role.** The user picks the roster.
- **Not a chat UI.** Transcripts live as JSONL on disk; any rendering is the host's job.

## Design principles

1. **Markdown is the source of truth.** If it can't be expressed in a SKILL.md, it probably shouldn't exist in this project.
2. **Workspace > skill repo.** The skill is read-only at runtime. All state lives in `<cwd>/.senate/`.
3. **Progressive disclosure.** Entry-point SKILL.md is short and points at sub-files. No 1000-line instructions.
4. **Contracts, not conventions.** Every phase that needs to be machine-parsed declares a structured-output contract (fenced JSON). Convention-based parsing rots.
5. **One protocol = one file.** Adding `tribunal.md` should not require touching any other file except the format table.
6. **Parity across hosts.** Anything that works in Claude Code should work in Codex, Cursor, OpenCode. Host-specific tricks go in agent-specific files, not the protocol.

## Roadmap

Each horizon is a **meaningful milestone**, not a release number. They roughly correspond to thesis-level bets — reach the end of a horizon and you have a shippable product that is materially more capable than the previous one.

---

### Horizon 0 — Foundation *(done)*

The minimum believable thing. Three formats, five CLIs, workspace conventions.

**Ships:**

- `senate` orchestrator skill.
- `invoke-agent` with codex / gemini / cursor / kimi / claude playbooks, loaded by per-turn subagents dispatched from the moderator.
- `debate-agenda` with parliament / court / committee / template.
- Workspace spec (`.senate/runs/<id>/`).

**Definition of done:** a user can `npx skills add SebastianElvis/senate`, then in their host agent say *"run a parliament between codex, gemini, and claude on X"* and get a `notes.md`.

---

### Horizon 1 — Reliability *(shipped)*

Make H0 boring. Today's H0 ships correct-looking prompts; H1 ships prompts that **produce structured output reliably** across all five CLIs, with deterministic replay, a real eval harness, and worked examples for the common cases.

**Shipped:**

- **Contract hardening.** Per-phase output contracts documented in `skills/moderate-debate/references/contracts.md`; format files declare the contract for each turn.
- **Eval harness** at `evals/` — separate from the shipped bundle. Two-tier grading: deterministic checks against the run-dir contract + LLM judges via `claude -p`. Fixtures cover the headline formats; runner is `evals/run.sh`. Available locally for anyone changing a skill; no CI compliance bar gates merges.
- **Replay.** `skills/senate/references/replay.md` defines the replay contract; `transcript.jsonl` is the source of truth.
- **Budget guardrails.** `skills/moderate-debate/references/budget.md` — per-run token/wall-clock caps enforced by the moderator.
- **Failure taxonomy.** `skills/moderate-debate/references/failures.md` — vocabulary for auth / rate-limit / timeout / contract-violation / refusal turn failures, written into `transcript.jsonl` and surfaced via the failure rollup section in `notes.md`.
- **Worked examples for common debates.** `examples/` ships three end-to-end recipes — *Review a PR as a court*, *Draft a spec by committee*, *Weigh a migration in parliament* — covering when to pick each format, the prompt to give the orchestrator, the recommended roster, what shows up in the run dir, and how to read the verdict.

**Definition of done:** the substrate (contracts, replay, budget, failure taxonomy, eval harness) is in place; `examples/` covers the three headline formats end-to-end. Compliance is measured locally via the harness when skills change, not enforced as a CI bar — the harness is a tool for the contributor, not a gate on merges.

---

### Horizon 2 — Expanded society *(shipped, then simplified)*

Go from 3 formats to a focused library, each drawn directly from a well-understood human institution. The product thesis — *that the space of human coordination patterns is the right design space* — starts being visible here. Format surface is what makes the library genuinely useful, and every later horizon assumes a rich format catalog underneath.

**Shipped library** (six flat single-stage formats in `skills/debate-agenda/formats/` — no presets, no closed families):

- **`parliament`** — collective decision by aggregation (vote tally with recorded dissent). Carries forward the H0 parliament.
- **`court`** — adversarial argument resolved by an arbiter (one prosecution, one defense, one judge). For "second opinion on a prior court verdict", run a fresh `court` with the prior verdict pasted in and a different roster.
- **`red-team`** — asymmetric failure-mode hunt: N parallel attackers, one defender, one judge. The adversarial-audit shape.
- **`peer-review`** — independent isolated reviewer judgments combined by a non-participating editor. Author/blind-reviewers/editor.
- **`committee`** — editor-led iterative co-authorship of a shared draft, closed by a member vote with explicit dissent.
- **`brainstorm`** — divergent generation under a no-criticism rule, then convergent selection. Produces options, not decisions.

The earlier presets (`appeals-court`, `socratic`, `oracle`, `rfc`, `consensus`) were removed: each either duplicated a surviving format's interaction contract or didn't earn its complexity in a multi-CLI context. `appeals-court` is replaced by re-running `court` with a fresh roster; `consensus` is subsumed by `committee`; the rest are retired.

**Also shipped:**

- **Format selector.** `skills/debate-agenda/references/format-selection.md` — decision tree the planner walks; the formats README has a quick "user says X → pick Y" table.
- **Format composition.** Implemented as multi-stage pipelines (`mode: pipeline`) rather than a separate `invoke-format` primitive. Pipelines pass each stage's verdict as input to the next; see H3 for the four shipped pipelines and the `stages/<N>-<name>/` run-dir layout that makes composition observable.

**Still open:**

- **Real-world debate examples in the docs** for each format. The format files document shape and contracts; opinionated end-to-end walk-throughs are sparse beyond the three in `examples/` (court, committee, parliament).
- **Mini-debate composition inside a single stage** (e.g., a committee role filled by a sub-court for tiebreaks). This is H4's territory; today, composition only happens at pipeline-stage granularity.

**Definition of done:** six flat formats covering the load-bearing interaction shapes (vote, adversarial ruling, failure-mode hunt, blind review, co-authorship, ideation), each with a real-world debate example in the docs; at least two formats that compose. *Surface-level done; example docs and intra-stage composition are the gap.*

---

### Horizon 3 — Workflows / longitudinal governance *(substrate shipped)*

Most real decisions are not one debate — they are a pipeline. A bill becomes law by: draft → committee review → floor debate → vote → signature. A paper becomes published by: draft → peer review → revision → editorial ruling. H3 makes multi-stage governance first-class, so `senate` can model the full life of a decision, not just a single deliberation.

This is the horizon that turns a library of formats into a **governance substrate** — and it's prioritized alongside H2 because most valuable real-world decisions live in pipelines, not single debates.

**Design deviation from the original plan:** rather than a separate top-level "workflow" skill, pipelines are unified with single-stage formats inside `debate-agenda`. A pipeline recipe lists stages that point at primitive format files. The planner expands either a primitive or a pipeline recipe into the same `agenda.md`; the moderator runs each stage with its primitive's contracts. This keeps "one debate" and "many debates chained" on the same substrate and avoids a parallel workflow skill that would duplicate the run-dir contract.

**Shipped:**

- **Pipelines as a first-class agenda mode.** `mode: pipeline` in `agenda.md`; stages, bindings, and a `stages/<N>-<name>/` run-dir layout that captures intermediate verdicts.
- **Canonical pipelines.** `draft-review-finalize` (`committee` → `peer-review` → `committee`), `design-review` (`committee` → (`peer-review` ‖ `red-team`) → `committee`), `bill-to-law` (`committee` → `peer-review` → `parliament` → `committee`), `incident-post-mortem` (`red-team` → `committee`). All four are recipes in `skills/debate-agenda/references/stages.md`.
- **Human-in-the-loop checkpoints.** `skills/moderate-debate/references/checkpoints.md` — pipelines can pause between stages and resume from `state.json`.
- **Branch and merge** (basic). `design-review` runs `peer-review` ‖ `red-team` in parallel and merges verdicts at the next `committee` stage. The bindings vocabulary supports this; richer fan-out/fan-in patterns are still ad-hoc per pipeline.

**Still open:**

- **Time-spanning runs in practice.** The run-dir contract accommodates multi-day state, but we have not exercised resume-after-days flows in the eval harness.
- **End-to-end demonstration on a real design doc** as a documented example.

**Definition of done:** a user can run a full RFC pipeline on a design doc — draft submitted, reviewers in parallel, author revises, editor rules — as a single command, with all intermediate artifacts preserved and resumable.

---

### Horizon 4 — Nested debates / hierarchies

Humans organize debate hierarchically. A single senator's position is informed by their staff; a committee's recommendation reflects an internal deliberation; a jury's verdict is the output of a private process. H4 makes this native, and pairs naturally with H3 — workflow stages become strictly more expressive when each stage can itself recurse.

**Ships:**

- **Sub-debates.** Any role in any format can be filled not by a single CLI but by a *format invocation*. "The prosecution role is filled by a 3-agent `committee`" — the orchestrator spawns that sub-debate, captures its verdict, and uses it as the prosecution's contribution.
- **Budget propagation.** A sub-debate inherits a fraction of the parent's token/time budget.
- **Nested transcripts.** Sub-runs are embedded under the triggering turn at `.senate/runs/<parent-id>/stages/<n>-<name>/turns/<NNN>-compose-<role>/sub/`. Parent verdicts reference the relative path to the sub-run.
- **Private deliberation.** A sub-debate's transcript is not automatically visible to peer roles at the parent level — only its output. This matches human norms (jury room privacy).
- **Composition library.** Pre-baked "combined" formats: `supreme-court` (3-judge panel, each judge is a private `committee`), `two-party-parliament` (each party is a `committee`), etc.

**Definition of done:** a user can say "run a court where the jury is itself a 3-way `committee` of codex / gemini / kimi" and have it work without writing any format file.

---

### Horizon 5 — Persistent actors *(deprioritized)*

*Deprioritized after review: the reliability and format-surface work in H1–H2 plus the pipeline substrate in H3 are where the near-term value lives. Reputation systems are load-bearing only once there is enough run volume to make track records statistically meaningful, which follows, not precedes, the other horizons.*

Every debate up to here is a stateless one-off. Humans are not: a senator who was wrong three times in a row about the economy carries that history. H5 introduces **persistent agent identity across runs** — once the preceding horizons have generated enough debate volume to make reputations meaningful.

**Ships:**

- **Actor profiles.** `<cwd>/.senate/actors/<name>.md` — persistent markdown file per actor (not per CLI). An actor is a *CLI + role + accumulated context*: "Claude-as-pragmatist", "Codex-as-type-theorist". Profiles accumulate short summaries of past positions and outcomes.
- **Reputation / track record.** After a debate resolves, the arbiter can annotate which actor's position proved correct (either immediately, via a test suite, or retrospectively when the user reports back). Actors accumulate hit/miss records.
- **Weighted voting.** Parliament (and other voting formats) can optionally weight by track record on similar tasks. Off by default.
- **Callback.** "The verdict said X; two weeks later, the outcome was Y." A `senate resolve <run-id> --outcome ...` records ground truth into the relevant actors' profiles.
- **Standing actors.** A small library of curated canonical actors ("the skeptic", "the minimalist", "the historian") with pre-written briefs and typical assignments.

**Risks:** gameable reputation, reinforcement of early-run noise. Must ship with a "reset" path and explicit warnings about reputation drift.

**Definition of done:** running the same kind of debate twice reuses actor profiles; a user can audit *why* an actor voted the way it did by reading its profile and transcript history.

---

### Horizon 6 — Incentives & markets *(deprioritized)*

*Deprioritized. Most users will never need budget markets or stake-weighted voting; they add real complexity for a narrow gain. Revisit only if concrete use cases emerge where the other horizons are demonstrably insufficient.*

Human institutions have budgets, roles have prestige, votes have weights, juries are selected. At this horizon, `senate` grows from *protocol library* into *coordination economy*.

**Ships:**

- **Budget markets.** Global token/time budget per run; agents/formats bid for share. Important sub-debates can claim more resources.
- **Role auctions.** When a role needs filling, eligible actors "bid" (by past performance + declared confidence on this task). The orchestrator picks.
- **Stake-weighted voting.** Actors can stake reputation on their vote; wrong votes cost more reputation than right ones gain.
- **Incentive-compatible mechanisms.** Quadratic voting, Schulze method, Condorcet — pluggable voting rules as a small library, with guidance on when each is appropriate.

**Risks:** over-engineering; most users don't need this. Gate behind explicit opt-in.

**Definition of done:** formats optionally support stake-weighted voting, with documented research-grounded mechanisms. A teaching doc explains when stakes help vs. hurt.

---

### Horizon 7 — Standing organizations

The final and most speculative horizon: **persistent, evolving agent organizations**. Not just a debate you run, but an institution you *join*.

**Ships:**

- **Organizations as skills.** An "org" is a directory of standing roles, a charter (the rules about how decisions are made), an archive of past verdicts, and membership criteria.
- **Example: Design Review Board.** A standing body for a codebase. New PRs are submitted as RFCs to the DRB; the DRB runs the workflow from H3; decisions are archived; members accumulate reputation per H5; stakes per H6.
- **Constitutional formats.** A format for *amending a format*. The org can vote to change its own rules; changes are themselves recorded.
- **Inter-org interaction.** Two orgs can negotiate, treaty-style, over a shared decision. A team's DRB and a security team's DRB can run a joint session.
- **Federation.** Orgs can live in git repos and be shared: *"my project uses the `anthropics/design-review-board` org"*.

**Definition of done:** a user can instantiate a standing DRB for their repo, submit PRs to it, see it operate over months, and hand off its archive when the project changes hands — with every decision traceable to a transcript.

---

## Open questions

- **Verdict trust.** A verdict is a markdown document produced by a synthesizer agent. How do we surface when the synthesis *disagreed with the underlying vote*? Maybe synthesizers must also emit a structured `{decision, tally, override?: true, reason}` that orchestrators can flag.
- **Cross-CLI context budget.** A long parliament may exceed a small CLI's context window. Do we auto-summarize, sample turns, or fail loudly? H1 will land on "fail loudly + provide a summarize-and-retry format".
- **Privacy boundary for sub-debates.** What's the right default — opaque (jury-room model) or transparent (glass-box)? Probably opaque with a `--verbose` flag.
- **Host heterogeneity.** The moderator spec now requires per-turn subagent isolation. Hosts without an Agent/Task-style primitive need an equivalent isolation shim before they can run debates correctly.
- **What happens when actors diverge from their CLI?** If Claude-as-pragmatist has a reputation built from Sonnet 4.5 and the user upgrades to Sonnet 4.7, is that still the same actor? Probably yes, with a version marker.

---

## How this all relates back to the core thesis

Every horizon is a step *toward* the full claim: that agent collaboration should be designed the way humans designed their institutions — deliberately, with protocols chosen for the question, with records kept, with rules about how the rules change. The H0–H7 progression mirrors, loosely, the evolution of human coordination: from informal debate → stable formats → multi-stage governance → hierarchical deliberation → (eventually, when the substrate is rich enough) persistent identity, incentives, and standing institutions.

The priority path is **H0 → H1 → H2 → H3**: a reliable foundation, a focused format catalog, and a pipeline substrate. As of this writing, H0 and H1 are done — H1 ships the contract / replay / budget / failure substrate, the local eval harness, and three worked examples covering the headline formats. H2 is shipped with six flat single-stage formats and a format selector. H3's substrate is shipped with four canonical pipelines and resumable checkpoints. The near-term focus is exercising H3 in real use (time-spanning runs, end-to-end pipeline demonstrations) and filling in per-format examples beyond the H1 three — rather than reaching for new horizons.

H4 lands naturally once H3 is exercised in real use. H5 and H6 remain parked until run volume makes reputation and incentives load-bearing rather than ornamental. H7 is the long view.

We are not inventing. We are porting.
