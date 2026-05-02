#!/usr/bin/env python3
"""Run one fixture end-to-end through the senate skill, then grade.

Pipeline per fixture:
  1. Create a fresh tmp workspace.
  2. Symlink the senate skills bundle into ~/.claude/skills/ (or use existing).
  3. Invoke `claude -p "<orchestrator prompt>"` from the workspace.
  4. Locate the resulting `.senate/runs/<id>/` directory.
  5. Run deterministic grader.
  6. Run each judge listed in the fixture's `judge_rubrics`.
  7. Append one merged scorecard line to evals/.evals/scorecard.jsonl.

The senate skill must already be installed (or symlinked) into the user's
Claude skills directory. The harness does not install it for you.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
EVALS_DIR = REPO_ROOT / "evals"
SCRIPTS_DIR = EVALS_DIR / "scripts"
JUDGES_DIR = EVALS_DIR / "judges"
OUT_DIR = EVALS_DIR / ".evals"


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def git_commit() -> str | None:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT,
            capture_output=True, text=True, timeout=5,
        )
        return out.stdout.strip()[:12] if out.returncode == 0 else None
    except Exception:
        return None


def claude_version(claude_bin: str) -> str | None:
    try:
        out = subprocess.run(
            [claude_bin, "--version"], capture_output=True, text=True, timeout=5,
        )
        return out.stdout.strip() if out.returncode == 0 else None
    except Exception:
        return None


def load_fixture(path: Path) -> tuple[dict, str]:
    text = path.read_text()
    if not text.startswith("---\n"):
        raise ValueError(f"fixture missing frontmatter: {path}")
    _, fm, body = text.split("---\n", 2)
    return yaml.safe_load(fm), body


def extract_task(body: str) -> str:
    """Grab the body of the first `# Task` section."""
    in_task = False
    out: list[str] = []
    for line in body.splitlines():
        if line.strip().startswith("# "):
            if in_task:
                break
            in_task = line.strip().lower() == "# task"
            continue
        if in_task:
            out.append(line)
    return "\n".join(out).strip()


def build_orchestrator_prompt(fm: dict, task: str) -> str:
    fmt = fm.get("format")
    roster_lines = "\n".join(
        f"  - {r['role']}: {r['cli']}" for r in fm.get("roster", [])
    )
    rounds = fm.get("rounds") or fm.get("max_rounds") or 2
    return f"""Use the `senate` skill to run a debate on the task below. Produce verdict.md and meeting-notes.md as the skill defines.

Use these settings (the user has already chosen them; do not re-plan):
- Format: {fmt}
- Roster (role: cli):
{roster_lines}
- Rounds: {rounds}

Run the debate to completion. Do not stop at any optional checkpoints.

# Task

{task}
"""


def find_run_dir(workspace: Path, started: datetime) -> Path:
    """Locate the run directory created by the orchestrator.

    Prefer dirs that have a parseable state.json with `started_at` >= the
    harness start time (excludes stale runs from prior eval invocations or
    other workspaces). Fall back to the most recently modified directory if
    no state.json was written (the orchestrator may have crashed early).
    """
    base = workspace / ".senate" / "runs"
    if not base.exists():
        raise RuntimeError(f"no .senate/runs/ created at {base}")
    candidates = [p for p in base.iterdir() if p.is_dir()]
    if not candidates:
        raise RuntimeError(f"no run subdir under {base}")

    scored: list[tuple[int, Path]] = []
    for p in candidates:
        state_path = p / "state.json"
        score = 0
        if state_path.exists():
            try:
                state = json.loads(state_path.read_text())
                ts = state.get("started_at", "")
                # Cheap lexical compare of ISO 8601 strings is correct.
                if ts and ts >= started.isoformat()[:19]:
                    score = 2
                else:
                    score = 1
            except Exception:
                pass
        scored.append((score, p))
    # Highest score wins; ties broken by mtime.
    scored.sort(key=lambda x: (x[0], x[1].stat().st_mtime), reverse=True)
    return scored[0][1]


def run_orchestrator(prompt: str, workspace: Path, model: str,
                     claude_bin: str, log_path: Path, timeout: int,
                     plugin_dir: Path) -> int:
    cmd = [
        claude_bin, "-p",
        "--model", model,
        "--output-format", "json",
        # Load the senate skills bundle as a plugin for this session only,
        # so we don't depend on the user having `npx skills add` installed it.
        "--plugin-dir", str(plugin_dir),
        # The orchestrator must be allowed to do everything in the workspace —
        # it shells out to other CLIs and writes to .senate/.
        "--dangerously-skip-permissions",
    ]
    with log_path.open("w") as log:
        proc = subprocess.run(
            cmd, input=prompt, stdout=log, stderr=subprocess.STDOUT,
            text=True, cwd=workspace, timeout=timeout,
        )
    return proc.returncode


def grade_deterministic(fixture: Path, run_dir: Path) -> dict:
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "grade_deterministic.py"),
         "--fixture", str(fixture), "--run-dir", str(run_dir)],
        capture_output=True, text=True,
    )
    # Grader returns nonzero when checks fail; the JSON is still on stdout.
    try:
        return json.loads(proc.stdout)
    except Exception as e:
        return {"error": f"grader output not JSON: {e}", "stderr": proc.stderr[-400:]}


def run_judge(rubric: str, fixture: Path, run_dir: Path,
              judge_model: str) -> dict:
    if rubric == "pairwise":
        # Pairwise requires two run dirs (A and B). It's a regression-detection
        # operation across runs, not a per-fixture quality check, so it cannot
        # be wired into a fixture's `judge_rubrics:` list. Invoke run_judge.py
        # directly with --run-dir-a and --run-dir-b instead.
        return {"rubric": rubric, "error": "pairwise is not invocable per-fixture; use run_judge.py directly"}
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "run_judge.py"),
         "--rubric", rubric,
         "--fixture", str(fixture),
         "--run-dir", str(run_dir),
         "--model", judge_model],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        return {"rubric": rubric, "error": proc.stderr[-400:] or "judge failed"}
    try:
        return json.loads(proc.stdout)
    except Exception as e:
        return {"rubric": rubric, "error": f"judge output not JSON: {e}"}


def evaluate_fixture(fixture: Path, orchestrator_model: str,
                     judge_model: str, claude_bin: str, timeout: int,
                     keep_workspace: bool) -> dict:
    fixture = fixture.resolve()
    fm, body = load_fixture(fixture)
    task = extract_task(body)
    fixture_id = fm.get("fixture_id", fixture.stem)
    started = datetime.now(timezone.utc)

    workspace = Path(tempfile.mkdtemp(prefix=f"evals-{fixture_id}-"))
    log_path = workspace / "orchestrator.log"

    try:
        rel_fixture = str(fixture.relative_to(REPO_ROOT))
    except ValueError:
        rel_fixture = str(fixture)

    record: dict = {
        "fixture_id": fixture_id,
        "fixture_path": rel_fixture,
        "fixture_sha256": sha256_file(fixture),
        "repo_commit": git_commit(),
        "claude_cli_version": claude_version(claude_bin),
        "started_at": started.isoformat(),
        "orchestrator_model": orchestrator_model,
        "judge_model": judge_model,
        "workspace": str(workspace),
    }

    try:
        prompt = build_orchestrator_prompt(fm, task)
        rc = run_orchestrator(prompt, workspace, orchestrator_model,
                              claude_bin, log_path, timeout, REPO_ROOT)
        record["orchestrator_exit"] = rc
        if rc != 0:
            record["error"] = f"orchestrator exited {rc}; see {log_path}"
            return record

        run_dir = find_run_dir(workspace, started)
        record["run_dir"] = str(run_dir)

        record["deterministic"] = grade_deterministic(fixture, run_dir)

        judges = fm.get("judge_rubrics") or ["verdict"]
        record["judges"] = {}
        for r in judges:
            judge_record = run_judge(r, fixture, run_dir, judge_model)
            judge_record["rubric_sha256"] = sha256_file(JUDGES_DIR / f"{r}.md")
            record["judges"][r] = judge_record

        # Roll-up. Require EVERY expected rubric to produce a parseable
        # judgement with `pass=True`. A missing or errored judge counts as a
        # fail — otherwise a silent judge outage would let runs pass on
        # deterministic checks alone.
        det_pass = bool(record["deterministic"].get("deterministic_pass"))
        judge_failures: list[str] = []
        for r in judges:
            j = record["judges"].get(r) or {}
            if "error" in j:
                judge_failures.append(f"{r}: {j['error'][:80]}")
                continue
            jud = j.get("judgement") or {}
            if jud.get("pass") is not True:
                judge_failures.append(f"{r}: pass={jud.get('pass')}")
        record["judge_failures"] = judge_failures
        record["pass"] = det_pass and not judge_failures

    except Exception as e:
        record["error"] = f"{type(e).__name__}: {e}"
    finally:
        record["completed_at"] = datetime.now(timezone.utc).isoformat()
        record["wall_clock_sec"] = (
            datetime.now(timezone.utc) - started
        ).total_seconds()
        if not keep_workspace and "error" not in record:
            # Keep workspace on error so the user can inspect.
            shutil.rmtree(workspace, ignore_errors=True)
            record["workspace"] = "<cleaned>"

    return record


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("fixtures", nargs="+", type=Path,
                    help="Fixture files (or globs) to evaluate.")
    ap.add_argument("--orchestrator-model", default="claude-sonnet-4-6",
                    help="Model the senate orchestrator uses (default: sonnet 4.6).")
    ap.add_argument("--judge-model", default="claude-opus-4-7",
                    help="Model the LLM judges use (default: opus 4.7).")
    ap.add_argument("--claude-bin",
                    default=os.environ.get("EVALS_CLAUDE_BIN") or shutil.which("claude") or "claude")
    ap.add_argument("--timeout", type=int, default=1800,
                    help="Per-fixture orchestrator timeout in seconds.")
    ap.add_argument("--keep-workspace", action="store_true",
                    help="Don't delete the tmp workspace after a successful run.")
    ap.add_argument("--scorecard", type=Path, default=OUT_DIR / "scorecard.jsonl")
    args = ap.parse_args()

    args.scorecard.parent.mkdir(parents=True, exist_ok=True)

    # Expand globs (caller may pass shell-glob already expanded; also support fixture dirs).
    fixtures: list[Path] = []
    for p in args.fixtures:
        if p.is_dir():
            fixtures.extend(sorted(p.glob("*.md")))
        else:
            fixtures.append(p)

    if not fixtures:
        print("no fixtures matched", file=sys.stderr)
        return 2

    print(f"# Evaluating {len(fixtures)} fixture(s)", file=sys.stderr)
    print(f"# Orchestrator: {args.orchestrator_model}", file=sys.stderr)
    print(f"# Judge: {args.judge_model}", file=sys.stderr)
    print(f"# Scorecard: {args.scorecard}", file=sys.stderr)

    fail = 0
    with args.scorecard.open("a") as out:
        for fx in fixtures:
            print(f"\n## {fx.name}", file=sys.stderr)
            rec = evaluate_fixture(
                fx, args.orchestrator_model, args.judge_model,
                args.claude_bin, args.timeout, args.keep_workspace,
            )
            out.write(json.dumps(rec) + "\n")
            out.flush()
            status = "PASS" if rec.get("pass") else "FAIL"
            print(f"  {status} ({rec.get('wall_clock_sec', 0):.0f}s)", file=sys.stderr)
            if rec.get("error"):
                print(f"  error: {rec['error']}", file=sys.stderr)
            if not rec.get("pass"):
                fail += 1

    print(f"\n# Done. {len(fixtures) - fail}/{len(fixtures)} passed.", file=sys.stderr)
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
