# Weigh a migration in parliament

The `parliament` primitive is the right format when the question is *open* — *"should we do X?"* — and you want diversity of perspective with a recorded vote and dissent. Multiple parties argue from different angles, then vote. The speaker tallies and writes the verdict.

## When to pick parliament (vs. court or consensus)

`parliament` and `court` are two of the five primitive formats; `consensus` is a preset of the `workshop` primitive. Pick by what you want out the other side:

- **`parliament`** — *"should we migrate to Rust?"* — open question, multiple legitimate viewpoints, you want a vote *and* the dissent on the record.
- **`court:court`** — *"is this PR safe to merge?"* — binary, adversarial, single ruling.
- **`workshop:consensus`** — *"design the migration plan"* — converging on a document, not a decision.

Use parliament when the answer might reasonably be yes, no, or *"yes, but with conditions"* — and when you want the dissenting argument written down even if you go ahead.

## The situation

Your team has a Python ingest service handling ~500 events/sec. You're considering migrating it to Rust for performance and memory-footprint reasons. Your team has 4 years of Python in production, async/await comfort, and zero production Rust experience. The decision is real, the answer isn't obvious, and whichever way you go you want to record what the other side said.

## The prompt

```
Run a parliament between codex, gemini, kimi, and claude on whether to
migrate our core ingest service from Python to Rust.

Context:
- Service handles ~500 events/sec, mostly I/O bound with bursts of CPU
  on JSON parsing and validation.
- Team: 10 engineers, 4 years of production Python, async/await comfort,
  zero production Rust.
- Stated goal of the migration: latency tail and memory footprint.
- Hiring market for Rust at this team's location is thin.

Roster:
- codex as mp_pro (argue for migrating)
- gemini as mp_con (argue against)
- kimi as mp_neutral (weigh both sides, surface false dichotomies)
- claude as speaker (tally votes, write the verdict)

Two rebuttal rounds. Speaker writes a verdict with Decision, Rationale,
and Dissent sections.
```

A few notes on the prompt:

- **Front-load context.** Parliament works best when every MP sees the same situational facts. Pin them in the prompt; don't make MPs infer load, team size, or constraints.
- **Name the parties explicitly** if the default `mp_pro / mp_con / mp_neutral` doesn't fit. A migration debate often benefits from named parties: *"mp_pragmatic"*, *"mp_perfectionist"*, *"mp_status_quo"*. Each gets a custom brief.
- **Pick the speaker last.** The speaker doesn't argue; it tallies and synthesizes. A model strong at reading transcripts and writing balanced summaries fits — claude is a common default.

## Recommended roster

| Role | Suggested CLI | Why |
| --- | --- | --- |
| `mp_pro` | `codex` | Steelmans the migration — performance gains, ecosystem maturity, type safety. |
| `mp_con` | `gemini` | Steelmans staying — team velocity, hiring, the cost of "rewrites". |
| `mp_neutral` | `kimi` | Surfaces angles neither side raised; flags false dichotomies (e.g., *"the choice isn't all-or-nothing"*). |
| `speaker` | `claude` | Reads the full transcript, tallies, writes the verdict. |

Minimum is 2 MPs + speaker; 3 MPs + speaker is the comfortable shape. Past 5 MPs the rebuttal phase gets long without producing more signal.

## What you'll see during the run

The orchestrator mints `<cwd>/.senate/runs/<id>-parliament/` and runs four phases:

1. **Opening statements** — every MP gives a 150–300 word opening in parallel. Position, top 3 reasons, evidence.
2. **Rebuttal rounds** (default 2) — every MP, in roster order, gives a 100–200 word rebuttal that addresses the strongest point made by another MP and references prior turns by number (e.g., *"T2 underweights the hiring constraint"*).
3. **Final vote** — every MP submits a fenced JSON block: `{"vote": "yes" | "no" | "abstain", "confidence": 0.0–1.0, "reason": "..."}`.
4. **Verdict** — the speaker writes the verdict: **Decision** (with the tally), **Rationale** (cites turn numbers), **Dissent** (the strongest argument the speaker ruled against, fairly stated).

Parliament *always* plays out the full round count — there's no early exit even if one side concedes. Recording dissent is the point.

## How to read the verdict

`notes.md` (the user-facing summary) will have a vote tally and a decision:

- **pass** → plurality voted yes. **Rationale** cites which arguments carried the room. **Dissent** records the strongest case for not doing it — read it before you start the migration; that's your risk register.
- **fail** → plurality voted no. **Dissent** here is the strongest case the *pro* side made. If you're going to migrate anyway, that's the case you'll need to argue to leadership.
- **tied** → speaker tiebreak. The speaker's tiebreak is labeled in the verdict (`speaker_tiebreak: yes | no`). Treat tied verdicts as evidence the question is genuinely close, not as a clean answer.

The structured outcome at the end of `notes.md` (`outcome`, `tally`, `speaker_tiebreak`) is machine-parseable; pipelines can bind to it from the underlying stage verdict (e.g., `bill-to-law` uses parliament's `outcome` to decide whether to proceed).

## Common pitfalls

- **Vague proposition.** *"Should we use Rust?"* is too broad — every MP will argue past every other. *"Should we migrate **this specific service** to Rust **for these specific reasons**?"* is debatable. Pin the question.
- **Stacking the roster.** If both `mp_pro` and `mp_neutral` are models that tend toward the same take, the debate is decided before it starts. Pick CLIs that genuinely disagree on the topic.
- **Skipping mp_neutral.** A 2-MP parliament (pro vs. con) collapses toward court. The neutral MP exists to surface considerations neither side raised — *"the choice isn't 'rewrite everything' vs. 'do nothing'; you could rewrite the hot path only"*. That third angle is most of the value.
- **Treating the tally as the answer.** A 2–1 vote on a migration is not a green light. Read **Dissent** — that's where the unmitigated risks live.
- **Re-running until you like the answer.** Don't. If you disagree with the verdict, run a `court:appeals-court` on it, or run a `workshop:consensus` to design the migration plan and let the disagreements surface there.

## After the run

- **Decide.** The verdict is one well-reasoned argument; you still own the decision. If the parliament voted *pass* and the dissent was thin, proceed. If it voted *fail* and the dissent (the pro case) was thin, don't.
- **Use the dissent.** Whatever the decision, the dissent section is the most actionable thing in the verdict — it's the risks or upside you'd otherwise miss.
- **Plan the next debate.** A migration decision usually triggers a follow-up *"how do we do it?"* — that's a `workshop:consensus` (design the migration plan) or the `design-review` pipeline recipe (`panel:oracle` → `workshop:committee` → `panel:peer-review` ‖ `court:red-team` → `workshop:committee`; the recipe lives in `skills/debate-agenda/references/stages.md`). Parliament is the *whether*; the *how* is downstream.
