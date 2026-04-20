# <format-name>

## Summary

One paragraph: when should the orchestrator pick this format over parliament / court / consensus? What shape of question is it best for?

## Roles

| Role | Brief |
| --- | --- |
| `role_a` | What this role does. Include tone and scope limits. |
| `role_b` | ... |

Describe the minimum and typical roster size.

## Phases

Number the phases. For each, specify:

### N. <phase name> — **parallel** or **sequential**

Roles: which role(s) speak this phase.

Prompt template:

```
Plain-text template. Use {placeholders} for:
- {task} — the debate topic
- {role} — the speaking role's name
- {role_brief} — that role's brief
- {transcript_slice: ...} — which prior turns this role sees
- any format-specific placeholders you invent
```

Output contract: describe what parses / what's free text. If structured, show the fenced json schema inline.

## Termination

When does the debate end? Fixed rounds, convergence check, explicit concession, judge ruling, ...

## Synthesis

Which role produces `verdict.md`, with what prompt and what sections. Paste the prompt template inline.

## Defaults

- **Rounds**: default and cap.
- **Roster size**: min and max.
- **Agent failure**: what happens if a participant fails a turn twice.
- **Edge cases**: ties, forfeitures, unexpected role invocations.

---

**Checklist before shipping a new format:**

- [ ] Every phase declares parallel vs sequential.
- [ ] Every prompt template is self-contained (orchestrator can fill it without reading other files).
- [ ] At least one phase has a structured-output contract so the termination check is mechanical.
- [ ] Synthesis produces a markdown verdict with the same top-level shape as other formats.
- [ ] Added a row to `SKILL.md`'s format table.
