#!/usr/bin/env python3
"""Roll up scorecard.jsonl into a markdown report.

Reads `evals/.evals/scorecard.jsonl`, groups by fixture and CLI, and writes:
  - per-fixture pass/fail with deterministic + judge breakdown
  - per-CLI contract compliance aggregated across fixtures
  - judge score distribution per rubric
  - regression flags vs. the previous run of the same fixture (>=10pp drop in
    deterministic_pass rate)

Usage:
  python3 evals/scripts/report.py [--scorecard PATH] [--out PATH]
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SCORECARD = REPO_ROOT / "evals" / ".evals" / "scorecard.jsonl"
DEFAULT_OUT = REPO_ROOT / "evals" / ".evals"


def load(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(ln) for ln in path.read_text().splitlines() if ln.strip()]


def aggregate_cli(records: list[dict]) -> dict[str, dict]:
    agg: dict[str, dict] = defaultdict(lambda: {
        "attempts": 0, "first_try": 0, "retried": 0, "failed": 0,
    })
    for r in records:
        for c in r.get("deterministic", {}).get("checks", []):
            if c.get("check") != "transcript_schema":
                continue
            for cli, counts in c.get("metrics", {}).get("by_cli", {}).items():
                for k in ("attempts", "first_try", "retried", "failed"):
                    agg[cli][k] += counts.get(k, 0)
    return dict(agg)


def aggregate_judges(records: list[dict]) -> dict[str, dict]:
    by_rubric: dict[str, list[float]] = defaultdict(list)
    pass_count: dict[str, int] = defaultdict(int)
    total: dict[str, int] = defaultdict(int)
    for r in records:
        for rubric, j in (r.get("judges") or {}).items():
            jud = j.get("judgement") or {}
            score = jud.get("overall_score")
            if isinstance(score, (int, float)):
                by_rubric[rubric].append(float(score))
            if "pass" in jud:
                total[rubric] += 1
                if jud["pass"]:
                    pass_count[rubric] += 1
    out = {}
    for rubric in by_rubric.keys() | total.keys():
        scores = by_rubric.get(rubric, [])
        out[rubric] = {
            "n": len(scores),
            "mean_score": round(mean(scores), 2) if scores else None,
            "min_score": min(scores) if scores else None,
            "max_score": max(scores) if scores else None,
            "pass_rate": round(pass_count[rubric] / total[rubric], 2) if total[rubric] else None,
        }
    return out


def regression_flags(records: list[dict]) -> list[str]:
    """Flag fixtures whose latest deterministic_pass dropped vs. the previous."""
    by_fixture: dict[str, list[dict]] = defaultdict(list)
    for r in records:
        by_fixture[r.get("fixture_id", "")].append(r)
    flags: list[str] = []
    for fixture, runs in by_fixture.items():
        if len(runs) < 2:
            continue
        runs.sort(key=lambda x: x.get("started_at", ""))
        prev, latest = runs[-2], runs[-1]
        if prev.get("pass") and not latest.get("pass"):
            flags.append(f"{fixture}: regressed (was PASS → now FAIL)")
    return flags


def render(records: list[dict]) -> str:
    if not records:
        return "# Eval report\n\nNo scorecard data yet.\n"

    cli_agg = aggregate_cli(records)
    judge_agg = aggregate_judges(records)
    flags = regression_flags(records)
    latest_run_ts = max(r.get("started_at", "") for r in records)

    lines = [
        "# Eval report",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        f"Latest run: {latest_run_ts}",
        f"Total scorecard rows: {len(records)}",
        "",
        "## Latest fixture results",
        "",
        "| Fixture | Pass | Det. checks | Judge means | Wall (s) |",
        "| --- | --- | --- | --- | --- |",
    ]
    by_fixture: dict[str, list[dict]] = defaultdict(list)
    for r in records:
        by_fixture[r.get("fixture_id", "")].append(r)
    for fixture, runs in sorted(by_fixture.items()):
        latest = max(runs, key=lambda x: x.get("started_at", ""))
        det = latest.get("deterministic", {})
        n_pass = sum(1 for c in det.get("checks", []) if c.get("pass"))
        n_total = len(det.get("checks", []))
        judges = latest.get("judges") or {}
        judge_strs = []
        for rubric, j in judges.items():
            sc = (j.get("judgement") or {}).get("overall_score")
            if sc is not None:
                judge_strs.append(f"{rubric}={sc}")
        lines.append(
            f"| `{fixture}` "
            f"| {'✓' if latest.get('pass') else '✗'} "
            f"| {n_pass}/{n_total} "
            f"| {', '.join(judge_strs) or '—'} "
            f"| {latest.get('wall_clock_sec', 0):.0f} |"
        )

    lines += ["", "## Per-CLI contract compliance (aggregated)", "",
              "| CLI | Attempts | First-try | Retried | Failed | First-try rate |",
              "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for cli, c in sorted(cli_agg.items()):
        rate = c["first_try"] / c["attempts"] if c["attempts"] else 0
        lines.append(
            f"| `{cli}` | {c['attempts']} | {c['first_try']} | {c['retried']} "
            f"| {c['failed']} | {rate:.0%} |"
        )

    lines += ["", "## Judge score distribution", "",
              "| Rubric | N | Mean | Min | Max | Pass rate |",
              "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for rubric, j in sorted(judge_agg.items()):
        pr = j["pass_rate"]
        pr_str = f"{pr:.0%}" if pr is not None else "—"
        lines.append(
            f"| `{rubric}` | {j['n']} | {j['mean_score'] or '—'} "
            f"| {j['min_score'] or '—'} | {j['max_score'] or '—'} "
            f"| {pr_str} |"
        )

    lines += ["", "## Regressions"]
    if flags:
        lines += [f"- {f}" for f in flags]
    else:
        lines.append("None.")

    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scorecard", type=Path, default=DEFAULT_SCORECARD)
    ap.add_argument("--out", type=Path,
                    help="Write report to this path; default prints to stdout.")
    args = ap.parse_args()

    records = load(args.scorecard)
    report = render(records)

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(report)
    else:
        print(report)
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
