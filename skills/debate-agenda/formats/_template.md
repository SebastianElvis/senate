# <primitive-name>

## Defining commitment

One sentence stating the load-bearing invariant — what makes this primitive a primitive. Examples from the shipped library: parliament closes by vote tally; court closes by arbiter ruling; panel demands strict isolation of contributors with non-participating synthesis; workshop demands co-authorship of a shared draft; brainstorm forbids criticism during divergence.

A new primitive needs an axis no existing primitive owns. If you can describe the new shape as a preset of an existing primitive, write it there.

## Boundary conditions

3–5 bullets stating the invariants the runtime must enforce for this primitive to be honest about what it produces (e.g., "arbiter must not be the same agent as any party", "contributors must not see each other's outputs", "at least one round of reaction-to-revision").

## Anti-drift fence

| If the task is… | The right primitive is… |
| --- | --- |
| <shape this primitive does NOT cover> | <other primitive that does> |

List every adjacent primitive whose work this one might be confused with, plus one sentence on what distinguishes them. This table is the load-bearing fence against the primitive becoming baggy over time.

## Presets (if any)

Some primitives are closed families with named presets (court has 4; panel has 3; workshop has 2). Single-preset primitives (parliament, brainstorm) skip this section.

If presets exist:

| Preset | <axis 1> | <axis 2> | <axis 3> | When to pick |
| --- | --- | --- | --- | --- |
| `name_a` | ... | ... | ... | ... |
| `name_b` | ... | ... | ... | ... |

State explicitly: "Closed family. Arbitrary parameter combinations are undefined — pick a named preset."

The agenda's stage declares `format: <primitive>` plus `preset: <name>`.

Then for each preset, document the four sections below.

---

## (For each preset, or for the primitive if no presets)

### Roles

| Role | Brief |
| --- | --- |
| `role_a` | What this role does. Include tone and scope limits. |
| `role_b` | ... |

Min and typical roster sizes.

### Phases

#### N. <phase name> — **parallel** or **sequential**

Roles: which role(s) speak this phase.

Prompt template:

```
Plain-text template. Use {placeholders} for:
- {task} — the debate topic
- {role} — the speaking role's name
- {role_brief} — that role's brief
- {transcript_slice: ...} — which prior turns this role sees
- any preset-specific placeholders you invent
```

Output contract: describe what parses / what's free text. If structured, show the fenced json schema inline.

### Termination

When does the debate end? Fixed rounds, convergence check, explicit concession, judge ruling, ...

### Synthesis

Which role produces the synthesis content, with what prompt and what sections. Paste the prompt template inline. The moderator writes the synthesis to `stages/<N>/verdict.md` in multi-stage runs; `meeting-note` writes the canonical top-level `verdict.md` (see `../../meeting-note/references/verdict-schema.md`).

### Defaults

- **Rounds**: default and cap.
- **Roster size**: min and max.
- **Agent failure**: what happens if a participant fails a turn twice.
- **Edge cases**: ties, forfeitures, unexpected role invocations.

---

**Checklist before shipping a new primitive or preset:**

- [ ] Defining commitment names a behavioral axis no existing primitive owns.
- [ ] Anti-drift fence covers every adjacent primitive.
- [ ] Every phase declares parallel vs sequential.
- [ ] Every prompt template is self-contained (the moderator can fill it without reading other files).
- [ ] At least one phase has a structured-output contract so the termination check is mechanical.
- [ ] Synthesis produces a markdown verdict with the same top-level shape as other primitives.
- [ ] If adding a preset to a closed family, the parameters are contract-defining (different prompts, turn rules, output schemas) — not decorative.
- [ ] Added a row to `README.md`'s primitives table or to the parent primitive's preset table.
