# Review a PR as a court

A `court` debate is the right format when a specific change is on the table and you want the strongest case for and against it, ending in a single ruling. Three roles, fixed: prosecution attacks, defense defends, judge rules.

## When to pick court (vs. peer-review or red-team)

- **court** — *"is this change safe to merge?"* — adversarial, binary outcome, judge ruling.
- **peer-review** — *"give me independent critique on this design doc"* — multiple reviewers, no fixed adversary.
- **red-team** — *"find ways this could fail"* — many attackers, no defender; useful before you've committed to the change.

If you already wrote the PR and want to know whether to merge it, court fits. If you want to harden it before opening, red-team fits.

## The situation

You opened a PR that reworks how rate limits are enforced — moving from a per-IP token bucket in middleware to a per-user sliding window in the application layer. Diff is ~600 lines across 8 files. CI is green. You want a real adversarial read before merging.

## The prompt

```
Run a court debate on PR #482 in this repo.

The diff is the change under review. Codex prosecutes (find reasons not to
merge). Claude defends (the author's case). Gemini judges.

Specifically: rule on whether this PR is safe to merge as-is, with
reasoning that cites concrete file paths and diff lines.
```

A few notes on the prompt:

- Give a **specific question to rule on**. *"Is this safe to merge as-is?"* is rulable; *"is this good?"* isn't.
- Pin the artifact under review. The orchestrator will paste the diff into `context.md` so all three CLIs see the same thing.
- Pick the prosecutor and defender deliberately. A model that *doesn't* know your codebase well is often a better prosecutor — it asks the questions an outsider would. A model that wrote (or is closest to) the change is a fair defender.

## Recommended roster

| Role | Suggested CLI | Why |
| --- | --- | --- |
| `prosecution` | `codex` | Strong at spotting concrete failure cases in diffs. |
| `defense` | `claude` | Good at constructing the affirmative case from the change's intent. |
| `judge` | `gemini` | Independent of the other two; rules on merits without re-arguing. |

You can also add an `expert_witness` (4-CLI roster) if there's a narrow factual question one side wants answered — e.g., *"how does Postgres handle concurrent advisory locks under contention?"* — without dragging the whole debate into it.

## What you'll see during the run

The orchestrator mints `<cwd>/.senate/runs/<id>-court/` and runs five phases in order:

1. **Charge** — prosecution lists 3–5 numbered objections, citing file paths and diff lines.
2. **Defense** — defense addresses each numbered objection: concede, refute, or refine.
3. **Cross-examination** (default 2 rounds) — prosecution presses on the weakest defense point; defense responds. Alternates.
4. **Expert witness** *(optional)* — fires only if a turn explicitly says `Calling expert witness on <topic>:`.
5. **Ruling** — judge writes the verdict with three sections: **Decision** (sustain / dismiss / remand), **Reasoning** (cites turn numbers like `T2`), **Dissent** (the strongest argument the judge ruled against, fairly stated).

Early exit: if either side concedes mid-cross, the moderator skips to the ruling.

## How to read the verdict

`verdict.md` will have one of three decisions:

- **sustain** → prosecution wins. The PR has problems the defense couldn't refute. Do not merge as-is. Read **Reasoning** for which objections held.
- **dismiss** → defense wins. The objections were addressable. Read **Dissent** to see what the judge thought was the *next-strongest* concern — that's usually the thing to fix anyway, even if it didn't block.
- **remand** → unresolved. The judge needs more information (a benchmark, a runtime check, a clarification from you). Read **Reasoning** for what's missing.

A `remand` is a feature, not a failure. It means the debate surfaced a question that genuinely couldn't be answered from the diff alone.

## Common pitfalls

- **Vague task.** *"Review this PR"* gets a generic critique. *"Rule on whether this PR is safe to merge as-is, given current production load"* gets a real ruling. Make the question rulable.
- **Imbalanced roster.** If both sides are the same model, the prosecution and defense converge — the model agrees with itself. Use different CLIs for prosecution and defense.
- **Treating the verdict as binding.** It isn't. The verdict is one well-reasoned argument; you still own the merge decision. Use `appeals-court` (re-run with a different roster) if you genuinely doubt a ruling.
- **Re-arguing in chat.** If you disagree with the judge, don't bicker — run an `appeals-court` on the run ID. That's what it's for.

## After the run

- **Merge or fix.** If the ruling is `sustain`, address the objections and re-run (or just open a new court on the revised diff).
- **Archive.** The run dir is yours; check it in alongside the PR if the decision was contested. Future-you will appreciate the receipt.
- **Appeals.** *"Get a second opinion on the court verdict in run `<id>`"* triggers `appeals-court`, which re-runs with a different roster looking specifically for errors in the original ruling.
