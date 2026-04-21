# Branching — parallel sub-pipelines

A workflow can fan out into multiple parallel branches and merge their verdicts before proceeding. Use when the same input needs independent evaluation along different dimensions — e.g., a PR reviewed in parallel by a security team and a perf team, or a design reviewed independently for both correctness and usability.

Branching is strictly more powerful than sequential stages, but adds orchestration complexity. Use it when sequential stages would impose artificial ordering.

## When to branch

Good reasons:

- **Independence of concerns**: security review and performance review are genuinely independent; running them in parallel is faster and reduces cross-contamination.
- **Multiple stakeholders**: different teams evaluate the same proposal through different lenses.
- **Robustness via redundancy**: run the same review twice with different rosters, use both verdicts to gauge confidence.

Bad reasons:

- "Speed" when the branches aren't actually independent — you'll just collide on the merge.
- "Coverage" when one well-designed stage would suffice.

## Workflow file syntax

Declare a branch as an ordered list of parallel stages under a single numeric position:

```markdown
### 2. parallel reviews

- **Parallel:** true
- **Branches:**

  - **security**
    - Format: red-team
    - Roster: attackers=[codex, kimi], defender=author, judge=gemini
    - Input: `draft_doc`
    - Output binding: `security_verdict` ← `verdict.md body`, `security_ruling` ← `fenced-json.ruling`

  - **perf**
    - Format: oracle
    - Roster: questioner=author, experts=[codex, gemini], synthesizer=kimi
    - Input: `draft_doc`
    - Output binding: `perf_verdict` ← `verdict.md body`

- **Merge:**
  - Next stage: 3. decide
  - Merge policy: wait_all
```

## Execution

1. Orchestrator reads the branch declaration.
2. For each branch, mint a sub-run directory:
   ```
   stages/2-parallel-reviews/
     branches/
       security/   # full senate run layout
       perf/
   ```
3. **Launch branches concurrently**, respecting the `Parallel: true` flag. Each branch runs as an independent senate invocation with its own budget.
4. **Budget split**: each branch gets an equal share of the parent stage's budget, unless overridden per-branch (`budget_weight: 2.0`).
5. **Collect verdicts** per the merge policy. See policies below.
6. Record the merged bindings in `bindings.json` and proceed to the next stage.

## Merge policies

### `wait_all` (default)

Wait for every branch to complete. All branches' bindings are available downstream. If any branch fails, the stage fails; downstream stages can check individual branch statuses.

### `wait_first`

Proceed as soon as the first branch completes. Remaining branches are cancelled (SIGTERM their subprocesses). Useful only when branches answer the same question and any answer is acceptable — rare.

### `wait_quorum_<n>`

Proceed once N branches have completed. Remaining are cancelled. Useful when running redundant branches for robustness and you want to take a majority.

### `wait_majority`

Wait for a strict majority of branches (`ceil(n/2) + 1`). Used with redundant branches.

## Synthesis of branch verdicts

The next stage after a branch merge typically needs to **combine** the parallel verdicts. Common idioms:

### Pass all bindings downstream

Next stage's prompt includes each branch's verdict as a separate binding. Let the next stage's format (often `committee` or `parliament`) reason about them.

### Collapse via an explicit synthesis stage

Insert a trivial stage between the branch and the next substantive stage:

```markdown
### 2.5. synthesize reviews

- Format: committee (single member + editor)
- Roster: member=claude, editor=claude
- Input: `security_verdict`, `perf_verdict`
- Output binding: `combined_reviews` ← `verdict.md body`
```

Prefer this when downstream stages should see a single coherent review rather than raw branch output.

## Failure in branches

- **One branch fails (budget, contracts)**: stage status is `partial` in `workflow_state.json`. Downstream can check per-branch status: `bindings.security_verdict.status == "failed"`. Policy `wait_all` marks the stage failed; others may still proceed.
- **All branches fail**: stage is `failed`. Orchestrator pauses for user intervention.
- **Budget overrun in one branch**: cancelled. Record `cancelled: true` in its stage artifact.

## Nesting

A branch may itself be a workflow (H4+). At H3, branches are always a single format invocation, not a nested pipeline.

## Determinism

Branches run concurrently, but their verdicts are recorded in the branch declaration order (not completion order) in `bindings.json`. This makes replay deterministic.

## Branch identity

Each branch has a name (`security`, `perf`). Names must be unique within the stage, become directory names, and are referenced in output bindings. Keep them short, lowercase, hyphen-separated.
