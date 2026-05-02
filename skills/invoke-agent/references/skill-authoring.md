# skill-authoring — Agent Skills spec & best practices

**Load this file only when the prompt you're sending to a CLI is asking it to author or revise an Agent Skill.** For ordinary debate turns, this content is irrelevant context — leave it out.

Claude Code (and most CLIs in this bundle) is itself an Agent Skills host. When the artifact under review is a skill, point the CLI at the canonical sources and the rules below.

## Canonical references

- Spec: https://agentskills.io/specification
- Best practices: https://agentskills.io/skill-creation/best-practices
- Optimizing descriptions: https://agentskills.io/skill-creation/optimizing-descriptions

## Spec essentials (validation must pass)

- Directory: `skill-name/SKILL.md` (required); optional `scripts/`, `references/`, `assets/`. `name` field must equal parent directory name.
- `name`: 1–64 chars, lowercase `a-z` + digits + hyphens; no leading/trailing/consecutive hyphens.
- `description`: 1–1024 chars; non-empty; should describe both *what the skill does* and *when to use it*; include keywords that help the agent identify relevant tasks.
- Optional frontmatter: `license`, `compatibility` (≤500 chars; only if the skill has real environment requirements), `metadata` (string→string map; namespace your keys), `allowed-tools` (experimental; space-separated).
- Body has no format constraints; loaded fully when the skill activates. Keep it under ~500 lines / 5000 tokens; move detail to `references/` and tell the agent **when** to load each file.

## Best-practice rules to apply when revising a skill

- Ground skills in real expertise (extract from a hands-on task or synthesize from real project artifacts — runbooks, code-review comments, fix history). Avoid generic LLM-generated procedures.
- Refine with execution: read traces, not just outputs. Vague instructions cause wandering; over-comprehensive instructions cause unproductive paths.
- Spend context on what the agent *wouldn't* know: project-specific conventions, non-obvious edge cases, exact APIs/tools to use. Cut generic explanations.
- Calibrate prescriptiveness to fragility: prescriptive (exact commands) for fragile or order-sensitive ops; flexible (with *why*) where multiple approaches work.
- Provide a default, not a menu. Mention alternatives briefly with an escape hatch.
- Teach procedures, not specific answers. The approach should generalize even when details are specific.
- Useful patterns: **Gotchas** (concrete corrections to mistakes the agent will otherwise make), **output-format templates**, **checklists** for multi-step workflows, **validation loops** (do → validate → fix → repeat), **plan-validate-execute** for batch/destructive ops, **bundled scripts** when you see the agent reinventing the same logic.

## Optimizing the `description` field

The description is the only thing loaded at startup — it carries all triggering.

- Use imperative phrasing: "Use this skill when…" not "This skill does…".
- Focus on user intent, not internal mechanics.
- Be pushy: list contexts where the skill applies, including phrasings where the user doesn't name the domain directly ("even if they don't explicitly mention X").
- Keep it concise; specification caps at 1024 chars but most should be a few sentences.
- To test triggering: build ~20 eval queries (8–10 should-trigger, 8–10 should-not-trigger near-misses sharing keywords); run each ~3 times; pass if trigger-rate is on the right side of 0.5. Use a 60/40 train/validation split to avoid overfitting. The `skill-creator` skill (https://github.com/anthropics/skills/tree/main/skills/skill-creator) automates this loop.

## Prompt-side checklist

When `claude -p` (or any CLI) is the synthesizer or editor in a debate stage and the artifact under review is a skill, include a short instruction in the prompt to validate against the spec checklist above before emitting changes.
