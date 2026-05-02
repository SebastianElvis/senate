# Branching — parallel sub-pipelines within an agenda

A multi-stage agenda may fan out into parallel branches and merge their verdicts before proceeding. Use when the same input needs independent evaluation along different dimensions — e.g., a PR reviewed in parallel by a security team and a perf team, or a design reviewed independently for both correctness and usability.

Branching is strictly more powerful than sequential stages, but adds complexity. Use it when sequential stages would impose artificial ordering on genuinely independent concerns.

## When to branch

Good reasons:

- **Independence of concerns:** security review and performance review are genuinely independent; running them in parallel is faster and reduces cross-contamination.
- **Multiple stakeholders:** different teams evaluate the same proposal through different lenses.
- **Robustness via redundancy:** run the same review twice with different rosters, use both verdicts to gauge confidence.

Bad reasons:

- "Speed" when the branches aren't actually independent — you'll just collide on the merge.
- "Coverage" when one well-designed stage would suffice.

## Agenda syntax

Declare a branch as a stage with a `branches` array:

```yaml
- index: 2
  name: parallel-reviews
  parallel: true
  branches:
    - name: security
      format: red-team
      roster:
        - { role: attacker, cli: codex }
        - { role: attacker, cli: kimi }
        - { role: defender, cli: claude }
        - { role: judge, cli: gemini }
      input_bindings: [draft_doc]
      output_bindings:
        - { name: security_verdict, source: "verdict.md body" }
        - { name: security_ruling, source: "fenced-json.ruling" }

    - name: peer-review
      format: peer-review
      roster:
        - { role: author, cli: claude }
        - { role: reviewer, cli: codex }
        - { role: reviewer, cli: gemini }
        - { role: editor, cli: kimi }
      input_bindings: [draft_doc]
      output_bindings:
        - { name: pr_verdict, source: "verdict.md body" }
        - { name: pr_decision, source: "fenced-json.decision" }
  merge_policy: wait_all
```

Each branch has a unique `name` (becomes a directory), its own format and roster, its own input and output bindings, and runs concurrently with its peers.

## Merge policies

### `wait_all` (default)

Wait for every branch to complete. All branches' bindings are available downstream. If **any** branch fails, the stage's status is `failed` (the moderator pauses for user intervention); only `wait_quorum_<n>` / `wait_majority` / `wait_first` policies tolerate partial branch failure (see "Failure in branches" below).

### `wait_first`

Proceed as soon as the first branch completes. Remaining branches are cancelled (SIGTERM). Useful only when branches answer the same question and any answer is acceptable — rare.

### `wait_quorum_<n>`

Proceed once N branches have completed. Remaining are cancelled. Useful when running redundant branches for robustness.

### `wait_majority`

Wait for a strict majority of branches (`ceil(n/2) + 1`). Used with redundant branches.

## Synthesis after a branch

The next stage usually needs to **combine** the parallel verdicts. Two common idioms:

### Pass all bindings downstream

The next stage's prompt includes each branch's verdict as a separate binding. Let the next stage's format (often `committee` or `parliament`) reason about them.

### Insert a trivial collapse stage

Insert a single-member `committee` stage between the branch and the next substantive stage. Stage indices are integers (per `agenda-schema.md`), so renumber the remaining stages rather than using a decimal index:

```yaml
- index: 3
  name: synthesize-reviews
  format: committee
  roster:
    - { role: member, cli: claude }
    - { role: editor, cli: claude }
  input_bindings: [security_verdict, pr_verdict]
  output_bindings:
    - { name: combined_reviews, source: "verdict.md body" }
```

Prefer this when downstream stages should see a single coherent review rather than raw branch output.

## Budget split

Each branch gets an equal share of the parent stage's budget by default. Override per branch:

```yaml
branches:
  - name: security
    budget_weight: 2.0    # gets 2/(2+1) = 2/3 of the stage budget
    ...
  - name: perf
    budget_weight: 1.0
    ...
```

Sub-budgets are computed as `parent_budget * weight / sum(weights)`.

## Failure in branches

The merge policy decides how branch failures roll up to the stage:

- **`wait_all`** — if any branch fails, the stage's status is `failed`. The moderator pauses for user intervention; downstream stages do not run.
- **`wait_first`, `wait_quorum_<n>`, `wait_majority`** — once enough branches have completed cleanly to satisfy the policy, remaining failures don't fail the stage. The stage's status is `partial`. Downstream stages run; they can check per-branch status via `bindings.<branch_binding>.status == "failed"`.
- **All branches fail** under any policy — stage status is `failed`. Moderator pauses for user intervention.
- **Budget overrun in one branch** — cancelled. Record `cancelled: true` in its branch artifact and apply the same per-policy roll-up.

In every case, individual branch verdicts (or partial verdicts) stay on disk under `<stage>/branches/<name>/`.

## Determinism

Branches run concurrently, but their verdicts are recorded in the **declaration order** (not completion order) in the bindings table. This makes replay deterministic.

## Branch identity

Each branch has a `name`. Names must be unique within the stage, become directory names under `<stage>/branches/<name>/`, and are referenced in output bindings. Keep them short, lowercase, hyphen-separated.

## Nesting

A branch is itself a single-stage primitive invocation at the moment. It may use `composition` (a role filled by a sub-debate) but it cannot itself contain further `branches`. Two-level nesting is a later horizon.
