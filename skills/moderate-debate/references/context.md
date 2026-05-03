# Shared and private context

The transcript owns all meaning; `context.md` and `agents/<cli>.md` are the **agent-facing projections** of the transcript at two visibility scopes (see "Invariants on derived projections" in `../../senate/references/workspace.md`). This file describes the agent-side contract — fence labels, prefixes, delta-only discipline.

Two scopes:

- **Shared** — `context.md`, one per run. Every agent reads it at the top of every turn. Agents emit `context-delta` fenced blocks in their replies; the per-turn subagent extracts the verbatim string and returns it as `context_delta`; the moderator commits it to the transcript row and projects it into `context.md` with a `[T<n>, <role>]` prefix.
- **Private** — `agents/<cli>.md`, one per CLI. Only that CLI reads its own file. Same flow with `private-delta` / `private_delta` and a `[T<n>]` prefix.

Both files are free-form scratchpads, not databases. The transcript and bindings carry the structured signal.

### Delta-only discipline

The moderator must not lift prose from the agent's main reply into either projection — the full cleaned reply already lives in `transcript.jsonl.text` (and is mirrored to `<turn-dir>/reply.md`). The projections carry only what the agent explicitly chose to broadcast at each visibility scope.

## `context.md` — shared scratchpad

Lives at `<run-dir>/context.md`. Initialized with a brief header on first start of the run:

```markdown
# Shared context

This file is shared working memory across all agents in this run. Every agent reads it at the top of every turn. You may append to it via a `context-delta` fenced block in your reply (see the turn instruction). Treat it like a meeting whiteboard: write things others should see; do not rewrite or delete prior entries.

## Notes

(empty — agents will append below)
```

### How agents append

The turn instruction includes a section like:

```
After your main reply, you may emit a `context-delta` fenced block:

\`\`\`context-delta
- <one-line note you want shared with everyone in the next turn>
- <another note>
\`\`\`

Use it for: pointers to evidence ("see line 42 of the diff"), open questions you want others to address, partial findings that aren't yet a position. Don't repeat what's in your main reply — others will read that in the transcript.
```

After the turn, the moderator commits the extracted string to `transcript.jsonl.context_delta` and projects it under `## Notes` with the turn marker (full commit pattern in `../SKILL.md` §4a). Example projection:

```markdown
- [T3, mp_pro] Migration cost estimate hinges on tokenizer compatibility — see crate `tiktoken-rs` v0.5.
- [T4, mp_con] If we keep Python, we still need to address the GIL bottleneck in the worker pool.
```

Agents may also write into other sections of `context.md` (creating new sections is allowed); the subagent returns the `context-delta` block verbatim and the moderator preserves it verbatim, prefixed with the turn marker.

### Append-only by convention

Agents are instructed not to rewrite past entries. The moderator does not enforce this with locks (it would burn turns), but does include a reminder in the turn prompt. Past notes in `context.md` are part of the run's audit trail.

### Size cap

If `context.md` grows beyond 8000 tokens, the moderator inserts a divider and a brief auto-summary:

```markdown
---

## Summary (auto, T12)

The debate has so far surfaced: <3 bullet points>. Notes above this divider are still in the file but agents may consult the summary as a starting point.

## Notes

```

The divider preserves the audit trail; the summary becomes the de facto starting point for subsequent agents.

To keep the projection invariant intact, the moderator pairs the on-disk insertion with a `summarize_context` ledger row in `transcript.jsonl` (see the non-turn ledger examples in `../../senate/references/workspace.md`). Replaying the transcript reproduces the divider + summary block.

## `agents/<cli>.md` — private memory

Lives at `<run-dir>/agents/<cli>.md`. Initialized on first start with:

```markdown
# Private memory — <cli>

This file is your private scratchpad across turns. Only you read it. Use it to: track what you've checked, your current best argument, things you'd consult on a future turn. The moderator passes the full file into your prompt at the top of every turn; you may emit a `private-delta` block in your reply to update it.

## Memory

(empty — you will append below)
```

### How the agent updates it

The turn instruction includes:

```
After your main reply (and after any `context-delta`), you may emit a `private-delta` fenced block:

\`\`\`private-delta
- <something only you need to remember between turns>
\`\`\`

Use it for: your evolving private theory, things you don't want to share yet, notes-to-self.
```

Same flow as shared context, with `private-delta` / `private_delta` and the `[T<turn>] ` prefix under `## Memory`.

### One file per CLI, not per role

Each CLI gets one private memory file across the whole run, even if it plays multiple roles in different stages. This matches how the same CLI might carry context from being an MP in stage 1 to being an editor in stage 2.

If the user wants per-role memory, they can run distinct CLIs in each role.

## Reading order in a turn prompt

The moderator builds the prompt in this order (see `../SKILL.md` step 4):

1. Run header.
2. Role brief.
3. Shared context (full `context.md`).
4. Private memory (full `agents/<cli>.md`).
5. Transcript slice.
6. Turn instruction.

Shared comes before private so the agent integrates the public state first, then layers in its own notes.

## What does NOT belong in context files

- **The verdict.** The synthesis content comes from the in-format synthesizer role (speaker / judge / editor / arbiter / synthesizer); the moderator writes it to `stages/<N>/verdict.md` (the bindings target), and the scribe folds it into the run-wide `notes.md`.
- **Per-turn output for the record.** That's `transcript.jsonl`.
- **Bindings between stages.** Those are extracted from `verdict.md` per the agenda's `output_bindings`.
- **Long quotes from the original artifact.** The artifact is in the prompt header or referenced by path; don't re-quote it into the scratchpad.

## Context files for sub-debates

A composed role's sub-debate has its own `context.md` and `agents/<cli>.md` files inside the embedded sub-run directory at `stages/<n>-<name>/turns/<NNN>-compose-<role>/sub/`. Sub-debate context is **opaque** to the parent: only the sub's verdict text (mirrored to `sub-verdict.md` next to the sub-run) flows up. This matches the privacy norm in `../../debate-agenda/references/composition.md`.
