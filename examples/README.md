# Worked examples

Three end-to-end walk-throughs of the most common ways to use `senate`. Each one is a complete recipe: the situation, the prompt to give the orchestrator, what shows up on disk, and how to read the result.

Pick the one closest to your problem and read it before running anything — the difference between *"my refactor is safe"* (court), *"design this API"* (consensus), and *"should we migrate?"* (parliament) is the difference between three useful runs and three confused ones.

| Example | Format | When to pick this |
| --- | --- | --- |
| [Review a PR as a court](./pr-review-as-court.md) | `court` | A specific change is on the table; you want the strongest case for and against it, then a ruling. |
| [Design an API by consensus](./api-design-by-consensus.md) | `consensus` | The deliverable is a document — a spec, an API surface, a plan — and you want multiple models to converge on it. |
| [Weigh a migration in parliament](./migration-by-parliament.md) | `parliament` | The question is open ("should we do X?") and you want diversity of perspective and a recorded dissent, not a single ruling. |

If none of these fits your task, ask the orchestrator *"which format should I use?"* — `debate-agenda` will recommend one with a one-paragraph rationale.

## What every example assumes

- You have `senate` installed (see the top-level [README](../README.md)).
- You have at least three of `codex`, `gemini`, `kimi`, `cursor`, `claude` installed and authenticated. Each example notes the roster it uses; substitute freely.
- You're in a host agent (Claude Code, Codex, Cursor, OpenCode, …) with the skill bundle on the path.

## What you'll see in every run

Every example produces the same run-dir layout under `<cwd>/.senate/runs/<id>/`:

```
agenda.md          # the plan
context.md         # shared scratchpad
agents/<cli>.md    # per-CLI private memory
transcript.jsonl   # append-only per-turn record
verdict.md         # canonical decision
meeting-notes.md   # user-facing summary
state.json         # for resume
```

When the orchestrator finishes, it returns a 2–4 sentence summary plus paths to `verdict.md` and `meeting-notes.md`. Read those, not the raw transcript.
