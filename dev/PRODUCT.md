# senate — Product vision & roadmap

> A library of human-institution coordination patterns, reusable as skills, for orchestrating collaboration between AI coding agents.

## Vision

Human civilization's most durable invention is not any single institution — it is the *design space* of institutions. Parliaments, courts, committees, peer review, juries, tribunals, town halls, standing councils: each is a protocol for turning disagreement among imperfect reasoners into a decision that is *better than any individual* could have produced alone. The protocols differ in what they optimize for — breadth of perspective, adversarial stress, written record, expert deference, consensus — and skilled humans pick the right protocol for the right question.

AI coding agents today mostly do the opposite. We either ask one model, or we chain them with ad-hoc "judge this / refine that" prompts glued together in Python. The result: no record, no repeatable structure, no way to compare *this* debate to *last week's*, no reuse of hard-won facilitation patterns. Every multi-agent setup is reinvented.

`senate` is the thesis that **agent collaboration should borrow, explicitly and literally, from the playbook of human organizations**. Not as metaphor — as protocol. A `parliament` has named roles, turn order, a voting rule, a speaker who writes the minutes. A `court` has prosecution, defense, cross-examination, a ruling. These are not storytelling wrappers; they are coordination mechanisms with centuries of stress-testing behind them.

The product is a growing library of these protocols, packaged as agent skills, runnable from any host (Claude Code, Codex, Cursor, OpenCode, …) against any roster of CLIs. Markdown in, verdict out. Transcripts on disk. No runtime code. Add a protocol by writing a markdown file.

## Why now

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
- `invoke-agent` with codex / gemini / cursor / kimi / claude playbooks.
- `debate-format` with parliament / court / consensus / template.
- Workspace spec (`.senate/runs/<id>/`).

**Definition of done:** a user can `npx skills add SebastianElvis/senate`, then in their host agent say *"run a parliament between codex, gemini, and claude on X"* and get a `verdict.md`.

---

### Horizon 1 — Reliability

Make H0 boring. Today's H0 ships correct-looking prompts; H1 ships prompts that **actually produce structured output 99% of the time** across all five CLIs, with deterministic replay and a real eval harness.

**Ships:**

- **Contract hardening.** Every phase that emits structured output gets a contract file (`contracts/parliament-vote.json`) — JSON schema + example + re-prompt template. Orchestrator validates and retries mechanically.
- **Eval harness** (a separate skill, `senate-eval`). A set of fixture debates with expected shape of outcome. Nightly runnable locally; reports format success rate per CLI.
- **Replay.** `transcript.jsonl` is complete enough that `senate replay <run-id>` re-runs the same debate deterministically (same prompts, same CLIs, same order) to compare models.
- **Budget guardrails.** Per-run token/wall-clock caps enforced in the orchestrator prompt.
- **Failure taxonomy.** Standard vocabulary in `transcript.jsonl` for the five ways an agent turn fails: auth, rate-limit, timeout, contract-violation, refusal.
- **Docs: playbooks for common debates.** "Review this PR as a court", "Design an API by consensus", "Weigh a migration in parliament".

**Definition of done:** running 20 debates in a row without a human having to intervene; eval shows ≥95% contract compliance per CLI on the three headline formats.

---

### Horizon 2 — Expanded society

Go from 3 formats to ~10, each drawn directly from a well-understood human institution. The product thesis — *that the space of human coordination patterns is the right design space* — starts being visible here. **This is the headline horizon**: format surface is what makes the library genuinely useful, and every later horizon assumes a rich format catalog underneath.

**New formats:**

- **`committee`** — deliberate in private, produce a written recommendation. Small roster, long-form output, editor role writes the final doc.
- **`peer-review`** — author, 2–3 reviewers, editor. Reviewers submit blind comments; author revises; editor adjudicates. Excellent for design docs.
- **`brainstorm`** — diverge then converge. All agents generate freely in round 1 (no critique); round 2 is clustering and ranking; round 3 selects the top-k for deeper development.
- **`oracle`** — expert panel. One questioner, N domain experts, synthesizer. Experts answer independently (no cross-talk) before synthesis. For *"what do we need to know before deciding X?"*.
- **`socratic-interview`** — one interviewer, one subject. Interviewer probes by asking the narrowest possible follow-up. Useful for debugging an agent's reasoning on a specific claim.
- **`appeals-court`** — re-runs a prior `court` verdict with a different roster, looking specifically for errors in the original ruling. Takes a previous `run_id` as input.
- **`rfc`** — distributed written comment. An author posts a draft; everyone annotates independently and asynchronously; editor merges. Scales beyond debate size limits.
- **`red-team`** — adversarial audit. One or more attackers try to find the failure case in a proposal; defender must address each.

**Also:**

- **Format composition primitives.** `invoke-format` lets one format call another (e.g., a `committee` that resolves disagreement by spawning a mini-`court`).
- **Format selector skill** — given a task, recommend the best-fit format with a one-paragraph rationale. Reduces the "which format should I use?" friction.

**Definition of done:** ≥10 formats, each with a real-world debate example in the docs; at least two formats that compose (`committee` invoking `court` for internal tiebreaks).

---

### Horizon 3 — Workflows / longitudinal governance

Most real decisions are not one debate — they are a pipeline. A bill becomes law by: draft → committee review → floor debate → vote → signature. A paper becomes published by: draft → peer review → revision → editorial ruling. H3 makes multi-stage governance first-class, so `senate` can model the full life of a decision, not just a single deliberation.

This is the horizon that turns a library of formats into a **governance substrate** — and it's prioritized alongside H2 because most valuable real-world decisions live in pipelines, not single debates.

**Ships:**

- **Workflow skill.** A new top-level skill that takes a *pipeline* (ordered list of formats with handoff rules) and runs it end to end. State persists between stages; each stage's verdict becomes the next stage's input.
- **Canonical workflows.** `rfc-pipeline`, `design-review`, `bill-to-law`, `incident-post-mortem`. Each ships as a workflow file referencing the relevant format files from H2.
- **Human-in-the-loop checkpoints.** Workflows can pause for user approval between stages. Resume from checkpoint.
- **Time-spanning runs.** A workflow can be paused and resumed days later. Run directory layout accommodates multi-day state.
- **Branch and merge.** A workflow can fan out into parallel sub-pipelines (e.g., security review and perf review running in parallel) and merge their verdicts before proceeding.

**Definition of done:** a user can run a full RFC pipeline on a design doc — draft submitted, 3 reviewers in parallel, author revises, editor rules — as a single command, with all intermediate artifacts preserved and resumable.

---

### Horizon 4 — Nested debates / hierarchies

Humans organize debate hierarchically. A single senator's position is informed by their staff; a committee's recommendation reflects an internal deliberation; a jury's verdict is the output of a private process. H4 makes this native, and pairs naturally with H3 — workflow stages become strictly more expressive when each stage can itself recurse.

**Ships:**

- **Sub-debates.** Any role in any format can be filled not by a single CLI but by a *format invocation*. "The prosecution role is filled by a 3-agent consensus" — the orchestrator spawns that consensus, captures its verdict, and uses it as the prosecution's contribution.
- **Budget propagation.** A sub-debate inherits a fraction of the parent's token/time budget.
- **Nested transcripts.** Sub-runs live at `.senate/runs/<parent-id>/sub/<child-id>/`. Parent verdicts reference child run IDs.
- **Private deliberation.** A sub-debate's transcript is not automatically visible to peer roles at the parent level — only its output. This matches human norms (jury room privacy).
- **Composition library.** Pre-baked "combined" formats: `supreme-court` (3-judge panel, each judge is a private consensus), `two-party-parliament` (each party is a committee), etc.

**Definition of done:** a user can say "run a court where the jury is itself a 3-way consensus of codex / gemini / kimi" and have it work without writing any format file.

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
- **Host heterogeneity.** Some host agents have parallel subagent tools; others only have shell. Format files mostly assume shell; we may eventually want conditional instructions.
- **What happens when actors diverge from their CLI?** If Claude-as-pragmatist has a reputation built from Sonnet 4.5 and the user upgrades to Sonnet 4.7, is that still the same actor? Probably yes, with a version marker.

---

## How this all relates back to the core thesis

Every horizon is a step *toward* the full claim: that agent collaboration should be designed the way humans designed their institutions — deliberately, with protocols chosen for the question, with records kept, with rules about how the rules change. The H0–H7 progression mirrors, loosely, the evolution of human coordination: from informal debate → stable formats → multi-stage governance → hierarchical deliberation → (eventually, when the substrate is rich enough) persistent identity, incentives, and standing institutions.

The priority path is **H0 → H1 → H2 → H3**: a reliable foundation, a rich format catalog, and a pipeline substrate. H4 lands naturally once H3 is in place. H5 and H6 are parked until real usage volume makes reputation and incentives load-bearing rather than ornamental. H7 is the long view.

We are not inventing. We are porting.
