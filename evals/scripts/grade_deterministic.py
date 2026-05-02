#!/usr/bin/env python3
"""Deterministic grader for a single senate run.

Inputs:  fixture file + run directory.
Output:  one JSON object on stdout with per-check pass/fail and aggregate metrics.

Checks fall into two groups:
  1. Universal contract — applies to every run, derived from workspace.md.
  2. Fixture-specific assertions — declared in the fixture's `assertions` frontmatter.

The grader is intentionally independent of the LLM judge. If a structural
predicate fails here, the run is flagged regardless of how the judge scores it.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

VALID_TERMINAL_STATES = {"completed", "stalled", "aborted"}
VALID_ERROR_CODES = {
    None, "auth", "rate_limit", "timeout", "contract_violation",
    "refusal", "unknown", "budget_exhausted",
}
TRANSCRIPT_REQUIRED_FIELDS = {"turn", "stage", "role", "cli", "ts", "exit_code"}
STATE_REQUIRED_FIELDS = {"run_id", "status", "started_at", "stages"}
SECTION_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)


def load_fixture(path: Path) -> tuple[dict, str]:
    text = path.read_text()
    if not text.startswith("---\n"):
        raise ValueError(f"fixture missing frontmatter: {path}")
    _, fm, body = text.split("---\n", 2)
    return yaml.safe_load(fm), body


def split_sections(md: str) -> dict[str, str]:
    """Map heading text -> body until next same-or-higher heading."""
    sections: dict[str, str] = {}
    matches = list(SECTION_HEADING_RE.finditer(md))
    for i, m in enumerate(matches):
        name = m.group(2).strip()
        body_start = m.end()
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(md)
        sections[name] = md[body_start:body_end].strip()
    return sections


def _roster_entries(fm: dict) -> list:
    """Extract roster entries regardless of shape.

    Spec says roster is a list of {role, cli} under stages[].roster, but
    planners sometimes flatten to top-level (single-stage agendas) and
    sometimes use a dict-of-roles instead of a list. Tolerate all four
    shapes; the agenda judge can score whether the chosen shape was correct.
    """
    candidates = []
    if "roster" in fm:
        candidates.append(fm["roster"])
    for stage in fm.get("stages") or []:
        if isinstance(stage, dict) and "roster" in stage:
            candidates.append(stage["roster"])
    entries: list = []
    for c in candidates:
        if isinstance(c, list):
            entries.extend(c)
        elif isinstance(c, dict):
            entries.extend({"role": k, **(v if isinstance(v, dict) else {})} for k, v in c.items())
    return entries


def check_agenda(run_dir: Path) -> dict:
    p = run_dir / "agenda.md"
    if not p.exists():
        return {"check": "agenda_present", "pass": False, "details": "agenda.md missing"}
    text = p.read_text()
    if not text.startswith("---\n"):
        return {"check": "agenda_schema", "pass": False, "details": "no YAML frontmatter"}
    try:
        _, fm_text, _ = text.split("---\n", 2)
        fm = yaml.safe_load(fm_text) or {}
    except Exception as e:
        return {"check": "agenda_schema", "pass": False, "details": f"frontmatter parse error: {e}"}
    issues = []
    fmt = fm.get("format")
    if not fmt:
        # Format may live under stages[0].format.
        for stage in fm.get("stages") or []:
            if isinstance(stage, dict) and stage.get("format"):
                fmt = stage["format"]
                break
    if not fmt:
        issues.append("missing format")
    roster = _roster_entries(fm)
    if len(roster) < 2:
        issues.append(f"roster has {len(roster)} entries (need >=2)")
    return {
        "check": "agenda_schema",
        "pass": not issues,
        "details": "; ".join(issues) or "ok",
        "metrics": {"format": fmt, "roster_size": len(roster)},
    }


def check_transcript(run_dir: Path) -> dict:
    p = run_dir / "transcript.jsonl"
    if not p.exists():
        return {"check": "transcript_present", "pass": False, "details": "transcript.jsonl missing"}
    issues = []
    turns = 0
    errors = 0
    by_cli: dict[str, dict] = {}
    last_turn = 0
    for ln, line in enumerate(p.read_text().splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except Exception as e:
            issues.append(f"line {ln}: invalid JSON ({e})")
            continue
        if "action" in obj:
            continue  # ledger line, not a turn
        missing = TRANSCRIPT_REQUIRED_FIELDS - obj.keys()
        if missing:
            issues.append(f"line {ln}: missing {sorted(missing)}")
            continue
        turns += 1
        t = obj["turn"]
        if not isinstance(t, int) or t <= last_turn:
            issues.append(f"line {ln}: turn {t} not monotonic (last={last_turn})")
        else:
            last_turn = t
        err = obj.get("error")
        if err not in VALID_ERROR_CODES:
            issues.append(f"line {ln}: invalid error code {err!r}")
        if err is not None:
            errors += 1
        cli = obj["cli"]
        rec = by_cli.setdefault(cli, {"attempts": 0, "first_try": 0, "retried": 0, "failed": 0})
        rec["attempts"] += 1
        retries = obj.get("retry_count", 0) or 0
        if err is not None:
            rec["failed"] += 1
        elif retries == 0:
            rec["first_try"] += 1
        else:
            rec["retried"] += 1
    return {
        "check": "transcript_schema",
        "pass": not issues and turns > 0,
        "details": "; ".join(issues[:5]) or "ok",
        "metrics": {"turns": turns, "errors": errors, "by_cli": by_cli},
    }


def check_state(run_dir: Path, expected_terminal: str | None = "completed") -> dict:
    p = run_dir / "state.json"
    if not p.exists():
        return {"check": "state_present", "pass": False, "details": "state.json missing"}
    try:
        obj = json.loads(p.read_text())
    except Exception as e:
        return {"check": "state_schema", "pass": False, "details": f"invalid JSON: {e}"}
    issues = []
    missing = STATE_REQUIRED_FIELDS - obj.keys()
    if missing:
        issues.append(f"missing fields {sorted(missing)}")
    status = obj.get("status")
    if expected_terminal and status != expected_terminal:
        issues.append(f"status={status!r}, expected {expected_terminal!r}")
    elif status not in VALID_TERMINAL_STATES:
        issues.append(f"status={status!r} not terminal")
    return {
        "check": "state_terminal",
        "pass": not issues,
        "details": "; ".join(issues) or "ok",
        "metrics": {"status": status},
    }


def check_artifact_present(run_dir: Path, name: str) -> dict:
    p = run_dir / name
    exists = p.exists() and p.stat().st_size > 0
    return {
        "check": f"{name.replace('.', '_')}_present",
        "pass": exists,
        "details": "ok" if exists else f"{name} missing or empty",
    }


def apply_assertion(rule: dict, run_dir: Path) -> tuple[bool, str]:
    """Check one fixture assertion. Returns (pass, message)."""
    kind = rule.get("kind")
    target = rule.get("target", "verdict.md")
    md = (run_dir / target).read_text() if (run_dir / target).exists() else ""
    sections = split_sections(md)

    if kind == "section_present":
        name = rule["section"]
        ok = name in sections and len(sections[name].strip()) > 0
        return ok, f"section {name!r} {'present' if ok else 'missing/empty'}"

    if kind == "section_contains_one_of":
        name = rule["section"]
        values = [str(v).lower() for v in rule["values"]]
        body = sections.get(name, "").lower()
        ok = any(v in body for v in values)
        return ok, f"section {name!r}: {'contains' if ok else 'missing'} one of {values}"

    if kind == "section_regex":
        name = rule["section"]
        pattern = rule["pattern"]
        flags = re.MULTILINE | (re.IGNORECASE if rule.get("ignore_case") else 0)
        body = sections.get(name, "")
        matches = re.findall(pattern, body, flags)
        min_count = rule.get("min_count", 1)
        ok = len(matches) >= min_count
        return ok, f"section {name!r}: regex {pattern!r} matched {len(matches)}/{min_count}"

    if kind == "section_regex_count":
        # Bounded count: min/max/exact. At least one must be supplied.
        name = rule["section"]
        pattern = rule["pattern"]
        flags = re.MULTILINE | (re.IGNORECASE if rule.get("ignore_case") else 0)
        body = sections.get(name, "")
        n = len(re.findall(pattern, body, flags))
        ok = True
        bounds = []
        if "exact" in rule:
            ok = ok and n == rule["exact"]
            bounds.append(f"exact={rule['exact']}")
        if "min" in rule:
            ok = ok and n >= rule["min"]
            bounds.append(f"min={rule['min']}")
        if "max" in rule:
            ok = ok and n <= rule["max"]
            bounds.append(f"max={rule['max']}")
        return ok, f"section {name!r}: regex {pattern!r} matched {n} ({', '.join(bounds) or 'no bounds'})"

    if kind == "section_turn_refs":
        name = rule["section"]
        body = sections.get(name, "")
        refs = re.findall(r"\bT(\d+)\b", body)
        min_count = rule.get("min", 2)
        ok = len(refs) >= min_count
        details = f"section {name!r}: {len(refs)} turn refs (need {min_count})"

        # Optional cross-check: do the cited turn numbers actually exist in the
        # transcript? Catches hallucinated citations.
        if rule.get("validate_against_transcript"):
            tp = run_dir / "transcript.jsonl"
            if not tp.exists():
                return False, f"{details}; transcript missing for cross-check"
            real_turns = set()
            for line in tp.read_text().splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                t = obj.get("turn")
                if isinstance(t, int):
                    real_turns.add(t)
            cited = {int(r) for r in refs}
            missing = sorted(cited - real_turns)
            if missing:
                return False, f"{details}; cited turns not in transcript: {missing}"
            details += f"; all cited turns exist"

        return ok, details

    if kind == "section_mentions_any":
        name = rule["section"]
        terms = [t.lower() for t in rule["terms"]]
        body = sections.get(name, "").lower()
        hits = [t for t in terms if t in body]
        ok = len(hits) > 0
        return ok, f"section {name!r}: matched {hits or 'none'}"

    if kind == "text_mentions_any":
        terms = [t.lower() for t in rule["terms"]]
        body = md.lower()
        hits = [t for t in terms if t in body]
        ok = len(hits) > 0
        return ok, f"document: matched {hits or 'none'}"

    if kind == "transcript_turn_regex":
        # Look at the Nth turn for a given role; require regex matches in `text`.
        role = rule["role"]
        nth = rule.get("nth", 1)
        pattern = rule["pattern"]
        min_count = rule.get("min_count", 1)
        tp = run_dir / "transcript.jsonl"
        if not tp.exists():
            return False, "transcript.jsonl missing"
        seen = 0
        for line in tp.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            if "action" in obj:
                continue
            if obj.get("role") != role:
                continue
            seen += 1
            if seen == nth:
                text = obj.get("text", "") or ""
                matches = re.findall(pattern, text, re.MULTILINE)
                ok = len(matches) >= min_count
                return ok, f"role={role!r} nth={nth}: regex matched {len(matches)}/{min_count}"
        return False, f"role={role!r} nth={nth}: turn not found"

    return False, f"unknown rule kind {kind!r}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixture", required=True, type=Path)
    ap.add_argument("--run-dir", required=True, type=Path)
    args = ap.parse_args()

    fm, _ = load_fixture(args.fixture)
    fixture_id = fm.get("fixture_id", args.fixture.stem)

    checks: list[dict] = []
    checks.append(check_agenda(args.run_dir))
    checks.append(check_transcript(args.run_dir))
    checks.append(check_state(args.run_dir))
    checks.append(check_artifact_present(args.run_dir, "verdict.md"))
    checks.append(check_artifact_present(args.run_dir, "meeting-notes.md"))

    rule_results = []
    for rule in fm.get("assertions", []) or []:
        try:
            ok, msg = apply_assertion(rule, args.run_dir)
        except Exception as e:
            ok, msg = False, f"rule error: {e}"
        rule_results.append({"rule": rule, "pass": ok, "details": msg})
    checks.append({
        "check": "fixture_assertions",
        "pass": all(r["pass"] for r in rule_results) if rule_results else True,
        "details": f"{sum(r['pass'] for r in rule_results)}/{len(rule_results)} passed",
        "rules": rule_results,
    })

    out = {
        "fixture_id": fixture_id,
        "run_dir": str(args.run_dir),
        "deterministic_pass": all(c["pass"] for c in checks),
        "checks": checks,
    }
    print(json.dumps(out, indent=2))
    return 0 if out["deterministic_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
