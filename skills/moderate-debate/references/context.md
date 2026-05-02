# Shared and private context

A debate's participants need somewhere to share intermediate state that doesn't fit cleanly into the structured per-turn record. The transcript is for the public record (one line per turn, structured); the context files are for working memory.

There are two kinds:

- **Shared context** — `context.md`, one per run. Free-form. Every agent reads it at the top of every turn; agents may append to it via a `context-delta` fenced block in their reply. The per-turn subagent extracts the block and returns it as `context_delta`; the moderator appends to `context.md`.
- **Private memory** — `agents/<cli>.md`, one per CLI in the roster. Free-form. Only that CLI reads its own file. The per-turn subagent extracts a `private-delta` fenced block from the CLI's reply and returns it as `private_delta`; the moderator appends to `agents/<cli>.md`. (Both writers — extraction and append — are described in `../SKILL.md` §4a.)

These files are deliberately unstructured. They are scratchpads, not databases. The transcript and bindings carry the structured signal.

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

After the turn, the per-turn subagent extracts the `context-delta` block from the CLI reply (the moderator never opens the raw log) and returns it as `context_delta` in its result. The moderator then appends it to `context.md` under the `## Notes` section, prefixed with `[T<turn>, <role>]`:

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

The divider preserves the audit trail; the summary becomes the de facto starting point for subsequent agents that don't want to reread everything.

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

The per-turn subagent extracts the `private-delta` block (returned as `private_delta` in its result); the moderator appends it to `agents/<cli>.md` under `## Memory`, prefixed with `[T<turn>]`. Same append-only discipline as shared context.

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

- **The verdict.** The synthesis content comes from the in-format synthesizer role (speaker / judge / editor / arbiter / synthesizer); the canonical top-level `verdict.md` is written by `meeting-note` from that content.
- **Per-turn output for the record.** That's `transcript.jsonl`.
- **Bindings between stages.** Those are extracted from `verdict.md` per the agenda's `output_bindings`.
- **Long quotes from the original artifact.** The artifact is in the prompt header or referenced by path; don't re-quote it into the scratchpad.

## Context files for sub-debates

A composed role's sub-debate has its own `context.md` and `agents/<cli>.md` files inside `<parent-run>/sub/<sub-id>/`. Sub-debate context is **opaque** to the parent: only the sub's `verdict.md` flows up. This matches the privacy norm in `../../debate-agenda/references/composition.md`.
