---
fixture_id: consensus-api-design
format: consensus
roster:
  - {role: contributor, cli: codex}
  - {role: contributor, cli: gemini}
  - {role: contributor, cli: kimi}
  - {role: arbiter, cli: claude}
max_rounds: 3
---

# Task

Design a minimal HTTP API for a "paste service": users POST text, receive a short URL, and GETting the URL returns the text. Constraints: single-tenant, no auth, no UI, text only (no binaries), pastes expire after 7 days.

Produce the agreed API specification — endpoints, methods, request/response schemas, error codes — as a markdown document. All three contributors must converge on one spec.

# Expected verdict shape

- `## Artifact` section contains **exactly two** HTTP endpoints (one POST, one GET).
- Artifact specifies a response JSON schema for the POST (or declares plain-text) with at minimum a URL / ID field.
- Artifact specifies error behavior for at least 2 cases (e.g., paste too large, paste expired / not found).
- `## Confidence` is one of: `converged`, `partial`, `stalled`.
- `## Remaining concerns` section is present (may be empty list).
- `## Process notes` section cites number of refine rounds used.
- At least 2 of 3 contributors ended with `"changed": false` in their final refine turn.

# Notes

This fixture tests convergence. A well-functioning consensus should settle in ≤ 2 refine rounds for a task this small. If it needs 3 or stalls, the format is wasting tokens or the contract is too lax.
