# Clarification — when and how to ask the user

The planner's first instinct should be to plan, not to ask. Most well-formed user requests give enough information to produce a reasonable agenda; the `## Open questions` section captures whatever residual uncertainty remains, and the moderator handles it adaptively.

Ask only when the answer **materially changes the agenda**.

## Ask when

- **Task is genuinely vague.** "Help me think about X" with no artifact or decision attached → ask what the deliverable is (a decision, a doc, a list of options).
- **Two interleaved questions.** "Should we migrate to Rust, and if so, what's the migration plan?" → ask which one first; offer to make it a two-stage agenda.
- **Single vs. multi-stage ambiguous.** "Run an RFC on this design" — could be a single `rfc` debate or the full `rfc-pipeline` (multi-stage). Ask which.
- **Composition gestured at but not pinned.** "I want a debate where the jury is multiple agents" — ask for the child format (consensus? committee?) and child roster.
- **Roster missing for ≥4-role formats.** Single 3-CLI default works for most formats; for `rfc`, `committee` with editor, or composed roles, ask if the user has a preferred roster.

## Don't ask when

- **Format is unspecified for a clear task** → pick per `format-selection.md`, surface the rationale, move on.
- **Roster is unspecified for a 3-role format** → default `codex, gemini, claude`, surface the choice, move on.
- **Rounds are unspecified** → use the format's default.
- **Budget is unspecified** → use defaults from `../../moderate-debate/references/budget.md`.
- **Checkpoints are unspecified** → default to `none` for autonomous runs.

If a default is wrong, the user will say so — and the moderator can re-plan via `stages.md` re-planning.

## Question budget

**At most two questions** before producing the agenda. If still ambiguous, write the best-fit agenda with `status: pending_clarification` and list the remaining ambiguity in `## Open questions`. The caller (`senate`) decides whether to surface those questions or proceed.

## Question shape

Questions should be:

- **Concrete.** "Should this be one debate or a draft → review pipeline?" — not "tell me more about your goal".
- **Bounded.** Offer options the user can pick from. Open-ended questions invite long replies that don't help planning.
- **One sentence each.** Don't bundle multiple questions into one paragraph.

### Examples

Good:

> Two ways to structure this — one debate, or a draft → review pipeline. Which do you want?

> Default roster is codex / gemini / claude. Want to swap any of those out, or add kimi / cursor for more breadth?

> The jury could be a single CLI or a small consensus debate. Which?

Bad:

> Could you tell me more about what you're trying to accomplish here, and what models you'd like to use, and how many rounds, and whether you want any checkpoints?

(Five questions in one. Pick the most load-bearing one.)

## After the user answers

Update the working agenda in memory, validate it, and return `status: ready`. Do not loop back for a second round of questions unless the user's answer surfaces a new ambiguity.

## When the user is silent or terse

If the user says "you decide" or "whatever you think", produce the best-fit agenda with `status: ready` and proceed. The user has explicitly delegated the choice. Surface what you chose in the agenda body so they can correct it mid-run if needed.
