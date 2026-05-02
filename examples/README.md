# Worked examples

Three end-to-end walk-throughs of the most common ways to use `senate`. Each one is a complete recipe: the situation, the prompt to give the orchestrator, what shows up on disk, and how to read the result.

Pick the one closest to your problem and read it before running anything — the difference between *"my refactor is safe"* (court), *"design this API"* (workshop:consensus), and *"should we migrate?"* (parliament) is the difference between three useful runs and three confused ones.

| Example | Format · Preset | When to pick this |
| --- | --- | --- |
| [Review a PR as a court](./pr-review-as-court.md) | `court` (primitive — uses the default `court` preset) | A specific change is on the table; you want the strongest case for and against it, then a ruling. |
| [Design an API by consensus](./api-design-by-consensus.md) | `workshop` · `consensus` preset | The deliverable is a document — a spec, an API surface, a plan — and you want multiple models to converge on it. |
| [Weigh a migration in parliament](./migration-by-parliament.md) | `parliament` (primitive) | The question is open ("should we do X?") and you want diversity of perspective and a recorded dissent, not a single ruling. |

The terminology: a **primitive** is one of the five interaction-contract playbooks (`parliament`, `court`, `panel`, `workshop`, `brainstorm`); a **preset** is a named configuration of a primitive (e.g., `workshop:consensus`, `court:appeals-court`, `panel:rfc`). The example walk-throughs use the friendly preset names in prose; the orchestrator routes them to the right primitive.

If none of these fits your task, ask the orchestrator *"which format should I use?"* — `debate-agenda` will recommend one with a one-paragraph rationale.

## What every example assumes

- You have `senate` installed (see the top-level [README](../README.md)).
- You have at least three of `codex`, `gemini`, `kimi`, `cursor`, `claude` installed and authenticated. Each example notes the roster it uses; substitute freely.
- You're in a host agent (Claude Code, Codex, Cursor, OpenCode, …) with the skill bundle on the path.

## What you'll see in every run

Every example produces the same run-dir layout under `<cwd>/.senate/runs/<id>/`:

```
agenda.md                # the plan
context.md               # shared scratchpad
transcript.jsonl         # append-only per-turn record (failures live here as `error` codes)
state.json               # for resume
notes.md                 # single user-facing summary
agents/
  moderator.md           # moderator's governance log
  <cli>.md               # per-CLI private memory across turns
stages/<n>-<name>/
  verdict.md             # synthesis content (bindings target)
  turns/<NNN>-<cli>-<role>/
    prompt.derived.md
    stdout.log          # always present; may be empty on failure
    stderr.log          # only if non-empty
    reply.md
```

When the orchestrator finishes, it returns a 2–4 sentence summary plus the path to `notes.md`. Read that, not the raw transcript.
