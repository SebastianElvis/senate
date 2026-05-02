---
fixture_id: peer-review-rfc
format: peer-review
roster:
  - {role: author, cli: claude}
  - {role: reviewer, cli: codex}
  - {role: reviewer, cli: gemini}
  - {role: editor, cli: kimi}
rounds: 2
assertions:
  - {kind: section_present, section: Final document}
  - {kind: section_present, section: Reviewer comments}
  - {kind: section_present, section: Editor decision}
  - {kind: section_contains_one_of, section: Editor decision, values: ["accept", "revise", "reject"]}
  - {kind: section_turn_refs, section: Editor decision, min: 2}
judge_rubrics: [verdict, agenda, meeting_notes]
---

# Task

Author a brief RFC (≤400 words) proposing that the team adopt **structured logging with JSON output** across all backend services, replacing the current mix of plain-text logs. The team is small (8 engineers), has 12 services in production, and currently relies on grepping log files in incidents.

The author drafts the RFC. Two reviewers raise concerns blindly (each without seeing the other's comments). The author revises once. The editor rules `accept`, `revise`, or `reject`, citing which reviewer concerns drove the call.

# Expected verdict shape

- `## Final document` contains the (possibly revised) RFC.
- `## Reviewer comments` lists each reviewer's blind comments separately.
- `## Editor decision` is one of `accept`, `revise`, `reject` (case-insensitive).
- Editor cites at least two specific turn numbers in the form `T<N>`.

# Notes

Tests whether peer-review preserves the blind-comments invariant (reviewers shouldn't see each other's drafts before submitting).
