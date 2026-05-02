#!/usr/bin/env python3
"""Invoke a Claude-CLI LLM judge against an artifact in a run directory.

Usage:
  run_judge.py --rubric verdict --fixture <path> --run-dir <path> [--model <id>]
  run_judge.py --rubric pairwise --fixture <path> --run-dir-a <path> --run-dir-b <path>

Calls a non-interactive judge CLI (`claude` by default, or `codex`). Parses the
judge's JSON, validates against a minimal schema, prints the combined record on
stdout.

The judge model is pinned via --model (default `claude-opus-4-7`). The model id
is recorded in the output so scorecard rows are reproducible.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
EVALS_DIR = REPO_ROOT / "evals"
JUDGES_DIR = EVALS_DIR / "judges"

ARTIFACT_FOR_RUBRIC = {
    "verdict": ["notes.md"],
    "agenda": ["agenda.md"],
    "meeting_notes": ["notes.md"],
    "transcript_quality": ["transcript.jsonl"],
}

# Required keys per rubric. Validated after JSON parse so a malformed judge
# response is caught instead of silently passing.
RUBRIC_SCHEMAS: dict[str, dict] = {
    "verdict": {
        "required": ["scores", "overall_score", "pass", "failure_modes", "reasoning"],
        "score_keys": ["addresses_task", "faithful_to_debate", "surfaces_dissent", "actionable", "concision"],
    },
    "agenda": {
        "required": ["scores", "overall_score", "pass", "failure_modes", "reasoning"],
        "score_keys": ["format_fit", "roster_diversity", "stage_scoping", "roles_named_clearly"],
    },
    "meeting_notes": {
        "required": ["scores", "overall_score", "pass", "failure_modes", "reasoning"],
        "score_keys": ["tl_dr_fidelity", "readable_under_60s", "preserves_disagreement", "adds_value_over_verdict"],
    },
    "transcript_quality": {
        "required": ["scores", "overall_score", "pass", "failure_modes", "reasoning"],
        "score_keys": ["roles_in_character", "turns_advance", "responds_to_peers", "no_padding"],
    },
    "pairwise": {
        "required": ["scores_a", "scores_b", "winner", "reasoning"],
        "score_keys": [],  # validated separately
    },
}


def validate_judgement(rubric: str, judgement: dict) -> list[str]:
    """Return a list of validation errors (empty list = OK)."""
    schema = RUBRIC_SCHEMAS.get(rubric)
    if not schema:
        return [f"no schema registered for rubric {rubric!r}"]
    errors = []
    for key in schema["required"]:
        if key not in judgement:
            errors.append(f"missing required field {key!r}")
    scores = judgement.get("scores")
    if schema["score_keys"]:
        if not isinstance(scores, dict):
            errors.append("`scores` must be an object")
        else:
            for k in schema["score_keys"]:
                v = scores.get(k)
                if not isinstance(v, (int, float)) or not (1 <= v <= 5):
                    errors.append(f"scores.{k} must be number in [1,5], got {v!r}")
    if "pass" in schema["required"] and not isinstance(judgement.get("pass"), bool):
        errors.append(f"`pass` must be boolean, got {type(judgement.get('pass')).__name__}")
    return errors


def read_task(fixture_path: Path) -> str:
    text = fixture_path.read_text()
    if not text.startswith("---\n"):
        raise ValueError("fixture missing frontmatter")
    _, _, body = text.split("---\n", 2)
    # The fixture body has a "# Task" section; return the next section's body.
    lines = body.splitlines()
    out: list[str] = []
    in_task = False
    for ln in lines:
        if ln.strip().startswith("# "):
            if in_task:
                break
            in_task = ln.strip().lower() == "# task"
            continue
        if in_task:
            out.append(ln)
    return "\n".join(out).strip()


def build_prompt(rubric: str, fixture: Path, run_dir: Path | None,
                 run_dir_a: Path | None, run_dir_b: Path | None) -> str:
    rubric_text = (JUDGES_DIR / f"{rubric}.md").read_text()
    task = read_task(fixture)

    parts = [
        rubric_text,
        "",
        "---",
        "",
        "# Task",
        "",
        task,
        "",
    ]

    if rubric == "pairwise":
        if not (run_dir_a and run_dir_b):
            raise ValueError("pairwise judge needs --run-dir-a and --run-dir-b")
        a = (run_dir_a / "notes.md").read_text()
        b = (run_dir_b / "notes.md").read_text()
        parts += ["# Notes A", "", a, "", "# Notes B", "", b, ""]
    else:
        artifacts = ARTIFACT_FOR_RUBRIC[rubric]
        for name in artifacts:
            p = (run_dir or Path()) / name
            if not p.exists():
                content = f"<{name} missing>"
            else:
                content = p.read_text()
            parts += [f"# {name}", "", content, ""]

    parts += [
        "---",
        "",
        "Now produce the JSON object specified in the rubric. Output ONLY the JSON, no prose.",
    ]
    return "\n".join(parts)


JUDGE_ENV_WHITELIST = {
    "PATH", "HOME", "USER", "LOGNAME", "SHELL",
    # Claude Code auth/session essentials:
    "ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN",
    "CLAUDE_CONFIG_DIR", "XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_CACHE_HOME",
    # macOS keychain support (OAuth tokens live here):
    "SSH_AUTH_SOCK",
}


def judge_env() -> dict:
    """Whitelist env to keep judge runs reproducible across machines."""
    env = {k: v for k, v in os.environ.items() if k in JUDGE_ENV_WHITELIST}
    env["TZ"] = "UTC"
    env["LANG"] = "C.UTF-8"
    env["LC_ALL"] = "C.UTF-8"
    return env


def invoke_claude(prompt: str, model: str, claude_bin: str) -> dict:
    # Sandboxing: tmp cwd (no senate CLAUDE.md or repo auto-memory leakage),
    # whitelist env (drops ad-hoc shell vars that cause cross-machine drift).
    # Using OAuth (no --bare) so no API key is required.
    cmd = [
        claude_bin, "-p",
        "--output-format", "json",
        "--model", model,
        "--disable-slash-commands",
    ]
    with tempfile.TemporaryDirectory(prefix="evals-judge-") as tmp:
        proc = subprocess.run(
            cmd, input=prompt, capture_output=True, text=True,
            timeout=240, cwd=tmp, env=judge_env(),
        )
    if proc.returncode != 0:
        raise RuntimeError(
            f"claude exited {proc.returncode}; stderr={proc.stderr[-400:]}"
        )
    try:
        wrapper = json.loads(proc.stdout)
    except Exception as e:
        raise RuntimeError(f"non-JSON wrapper from claude: {e}; raw={proc.stdout[:400]}")
    return wrapper


def invoke_codex(prompt: str, model: str, codex_bin: str) -> dict:
    cmd = [
        codex_bin, "exec",
        "--model", model,
        "--sandbox", "danger-full-access",
        "--dangerously-bypass-approvals-and-sandbox",
        "--json",
        "--output-last-message", "last-message.txt",
        "--skip-git-repo-check",
        "-",
    ]
    with tempfile.TemporaryDirectory(prefix="evals-judge-codex-") as tmp:
        tmp_path = Path(tmp)
        proc = subprocess.run(
            cmd, input=prompt, capture_output=True, text=True,
            timeout=240, cwd=tmp, env=judge_env(),
        )
        last_path = tmp_path / "last-message.txt"
        last = last_path.read_text() if last_path.exists() else ""
    if proc.returncode != 0:
        raise RuntimeError(
            f"codex exited {proc.returncode}; stderr={proc.stderr[-400:]}; stdout={proc.stdout[-400:]}"
        )
    return {"result": last, "usage": _codex_usage(proc.stdout)}


def _codex_usage(events: str) -> dict:
    usage: dict = {}
    for line in events.splitlines():
        try:
            obj = json.loads(line)
        except Exception:
            continue
        if obj.get("type") == "turn.completed" and isinstance(obj.get("usage"), dict):
            usage = obj["usage"]
    return usage


def extract_judge_json(wrapper: dict) -> dict:
    """Pull the judge's JSON object out of the wrapper's `result` field.

    Claude returns {result: "<assistant text>", ...}; the Codex invoker adapts
    its last-message file into the same shape. The assistant text should be
    JSON only (we asked for that), but models sometimes wrap it in code fences.
    Strip those.
    """
    text = wrapper.get("result")
    if text is None:
        raise RuntimeError(f"no 'result' field in wrapper: keys={list(wrapper)}")
    text = text.strip()
    if text.startswith("```"):
        # strip ```json ... ``` fences
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
        text = text.strip().rstrip("`").strip()
    try:
        return json.loads(text)
    except Exception as e:
        raise RuntimeError(f"judge produced non-JSON: {e}; text={text[:400]}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rubric", required=True,
                    choices=["verdict", "agenda", "meeting_notes",
                             "transcript_quality", "pairwise"])
    ap.add_argument("--fixture", required=True, type=Path)
    ap.add_argument("--run-dir", type=Path)
    ap.add_argument("--run-dir-a", type=Path)
    ap.add_argument("--run-dir-b", type=Path)
    ap.add_argument("--model", default="claude-opus-4-7")
    ap.add_argument("--judge-cli", choices=["claude", "codex"], default="claude")
    ap.add_argument("--claude-bin",
                    default=os.environ.get("EVALS_CLAUDE_BIN") or shutil.which("claude") or "claude")
    ap.add_argument("--codex-bin",
                    default=os.environ.get("EVALS_CODEX_BIN") or shutil.which("codex") or "codex")
    args = ap.parse_args()

    def invoke(prompt: str) -> dict:
        if args.judge_cli == "codex":
            return invoke_codex(prompt, args.model, args.codex_bin)
        return invoke_claude(prompt, args.model, args.claude_bin)

    schema_errors: list[str] = []
    if args.rubric == "pairwise":
        # Counterbalance: judge once with (A,B), once with (B,A). Only accept
        # the winner if both passes agree; otherwise call it a tie. Mitigates
        # position bias more reliably than a textual reminder alone.
        prompt_ab = build_prompt(args.rubric, args.fixture, args.run_dir,
                                 args.run_dir_a, args.run_dir_b)
        prompt_ba = build_prompt(args.rubric, args.fixture, args.run_dir,
                                 args.run_dir_b, args.run_dir_a)
        wrap_ab = invoke(prompt_ab)
        wrap_ba = invoke(prompt_ba)
        j_ab = extract_judge_json(wrap_ab)
        j_ba = extract_judge_json(wrap_ba)
        # Translate B/A winner back into A/B frame.
        flip = {"A": "B", "B": "A", "tie": "tie"}
        winner_ab = j_ab.get("winner")
        winner_ba_in_ab_frame = flip.get(j_ba.get("winner"), j_ba.get("winner"))
        if winner_ab == winner_ba_in_ab_frame:
            consensus_winner = winner_ab
            consistent = True
        else:
            consensus_winner = "tie"
            consistent = False
        judgement = {
            "winner": consensus_winner,
            "consistent_across_orderings": consistent,
            "ab": j_ab,
            "ba": j_ba,
        }
        wrapper = wrap_ab  # primary wrapper for usage stats
    else:
        prompt = build_prompt(args.rubric, args.fixture, args.run_dir,
                              args.run_dir_a, args.run_dir_b)
        wrapper = invoke(prompt)
        judgement = extract_judge_json(wrapper)
        schema_errors = validate_judgement(args.rubric, judgement)
        if schema_errors:
            # Schema violations force pass=False so the harness treats this
            # rubric as failed instead of silently letting a malformed judge
            # response through.
            judgement["pass"] = False
            judgement["schema_errors"] = schema_errors

    out = {
        "rubric": args.rubric,
        "fixture": str(args.fixture),
        "run_dir": str(args.run_dir) if args.run_dir else None,
        "run_dir_a": str(args.run_dir_a) if args.run_dir_a else None,
        "run_dir_b": str(args.run_dir_b) if args.run_dir_b else None,
        "model": args.model,
        "judge_cli": args.judge_cli,
        "ts": datetime.now(timezone.utc).isoformat(),
        "judgement": judgement,
        "wrapper_meta": {
            k: wrapper.get(k) for k in ("usage", "duration_ms", "session_id")
            if k in wrapper
        },
    }
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
