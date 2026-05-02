#!/usr/bin/env python3
"""Generic CLI stub used by the eval harness in replay mode.

The harness symlinks `claude`, `codex`, `gemini`, `cursor`, `kimi` to this
file. The stub:

1. Identifies which CLI it's pretending to be (from argv[0] basename).
2. Hashes the prompt (read from stdin or --input-file or first positional).
3. Looks up `<recordings_dir>/<cli>/<hash>.json`. If found, prints its
   `stdout` field and exits with `exit_code`.
4. If not found:
   - In record mode (EVALS_STUB_MODE=record): forwards to the REAL CLI
     (path in `EVALS_REAL_<CLI>` env var), captures its output to the
     recording, then prints it.
   - Otherwise: exits non-zero with a clear error so the harness can flag
     the missing recording.

Recordings dir defaults to `evals/stubs/recordings/`. Override with
`EVALS_RECORDINGS_DIR`.

The hash inputs are: prompt body + key arguments (--model, --output-format).
Volatile flags (--session-id, etc.) are stripped before hashing so the same
fixture replays consistently across runs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

VOLATILE_FLAGS = {"--session-id", "--debug-file", "--continue", "-c"}
DEFAULT_RECORDINGS_DIR = Path(__file__).resolve().parent / "recordings"

# Bump when the prompt-template / contract shape that the senate skill emits
# changes in a way that invalidates prior recordings. The version is part of
# the hash key, so old recordings stop matching automatically and you'll be
# prompted to re-record. Document each bump in a comment below.
RECORDING_VERSION = "v1"
# v1 — initial release.


def cli_name() -> str:
    return Path(sys.argv[0]).name


def read_prompt(args: list[str]) -> tuple[str, list[str]]:
    """Return (prompt_text, residual_args). Reads stdin if nothing else."""
    residual: list[str] = []
    prompt: str | None = None
    skip = False
    for i, a in enumerate(args):
        if skip:
            skip = False
            continue
        if a in VOLATILE_FLAGS:
            skip = True
            continue
        if a == "--input-file":
            prompt = Path(args[i + 1]).read_text()
            skip = True
            continue
        if not a.startswith("-") and prompt is None:
            # First positional is the prompt for most CLIs.
            prompt = a
            continue
        residual.append(a)
    if prompt is None:
        prompt = sys.stdin.read()
    return prompt, residual


def hash_key(cli: str, prompt: str, residual: list[str]) -> str:
    h = hashlib.sha256()
    h.update(RECORDING_VERSION.encode())
    h.update(b"\0")
    h.update(cli.encode())
    h.update(b"\0")
    # Sort residual args for stability.
    h.update("\0".join(sorted(residual)).encode())
    h.update(b"\0")
    h.update(prompt.encode())
    return h.hexdigest()[:16]


def replay(record: dict) -> int:
    sys.stdout.write(record.get("stdout", ""))
    sys.stderr.write(record.get("stderr", ""))
    return int(record.get("exit_code", 0))


def record_mode(cli: str, prompt: str, residual: list[str], record_path: Path) -> int:
    real = os.environ.get(f"EVALS_REAL_{cli.upper()}")
    if not real:
        sys.stderr.write(
            f"[stub] EVALS_REAL_{cli.upper()} not set; cannot record\n"
        )
        return 99
    proc = subprocess.run(
        [real, *residual], input=prompt,
        capture_output=True, text=True,
    )
    record = {
        "recording_version": RECORDING_VERSION,
        "cli": cli,
        "args": residual,
        "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest()[:16],
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "exit_code": proc.returncode,
    }
    record_path.parent.mkdir(parents=True, exist_ok=True)
    record_path.write_text(json.dumps(record, indent=2))
    sys.stdout.write(proc.stdout)
    sys.stderr.write(proc.stderr)
    return proc.returncode


def main() -> int:
    cli = cli_name()
    if cli == "_stub.py":
        sys.stderr.write("[stub] do not call _stub.py directly; symlink it\n")
        return 99
    args = sys.argv[1:]
    prompt, residual = read_prompt(args)
    key = hash_key(cli, prompt, residual)

    recordings_dir = Path(os.environ.get("EVALS_RECORDINGS_DIR", DEFAULT_RECORDINGS_DIR))
    record_path = recordings_dir / cli / f"{key}.json"

    if record_path.exists():
        record = json.loads(record_path.read_text())
        return replay(record)

    mode = os.environ.get("EVALS_STUB_MODE", "replay")
    if mode == "record":
        return record_mode(cli, prompt, residual, record_path)

    sys.stderr.write(
        f"[stub] no recording for {cli} at {record_path}\n"
        f"[stub] re-run with EVALS_STUB_MODE=record and "
        f"EVALS_REAL_{cli.upper()}=/path/to/real/{cli} to capture\n"
    )
    sys.stderr.write(f"[stub] prompt hash: {key}\n")
    sys.stderr.write(f"[stub] prompt[:200]: {prompt[:200]!r}\n")
    return 1


if __name__ == "__main__":
    sys.exit(main())
