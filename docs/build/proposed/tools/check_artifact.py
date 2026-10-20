#!/usr/bin/env python3
"""Hash a signed artifact in $PRIVATE_EVIDENCE_DIR for a human-track gate.

Standard library only. Installs to tools/check_artifact.py (G1-protected).
The FOUNDER runs this in their own terminal, never inside a Claude session (G5).

The founder keeps a copy of each signed document at
    $PRIVATE_EVIDENCE_DIR/STEP-NN/<label>.<extension>
(one file per label; the owner keeps the signed original). This script checks that
the file exists, is a regular non-empty file inside $PRIVATE_EVIDENCE_DIR, and prints
only lines in the evidence grammar: the command, exit code, SHA-256, signer role,
counts and date. It never prints a file name, a path, a person's name or file content.

Example (the founder writes the absolute path out):
  PRIVATE_EVIDENCE_DIR=/Users/rehan/TillOwl-private-evidence \\
    python tools/check_artifact.py --step STEP-05 --label ack_batch --role staff \\
    --count 12 --absent 1 --refused 0 --date 2026-11-02

Paste the printed block into docs/build/evidence/STEP-NN.md in the engineer's session.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import os
import re
import stat
import sys
from pathlib import Path

LABELS = {
    "counsel_t17a", "counsel_t17b", "sms_optin", "tendlc_approval", "terms_t5", "terms_t6",
    "terms_t8", "t8_template_only", "notice", "ack_batch", "posting", "authorization",
    "support_permission", "dpa", "pass_line", "upfront_invoice", "t1_approval",
    "t1_not_required", "invoice_settlement", "notice_export",
}
ROLES = {"owner", "counsel", "vendor", "staff", "founder"}
STEP_RE = re.compile(r"^STEP-\d{2}$")


def fail(message: str) -> int:
    # Messages never include paths or file names.
    print(f"error: {message}", file=sys.stderr)
    print("exit_code: 1")
    return 1


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Hash a signed artifact for a human-track gate.")
    parser.add_argument("--step", required=True)
    parser.add_argument("--label", required=True, choices=sorted(LABELS))
    parser.add_argument("--role", required=True, choices=sorted(ROLES))
    parser.add_argument("--date", help="date the artifact was signed or issued, YYYY-MM-DD (default: today)")
    parser.add_argument("--count", type=int, help="staff only: number of staff who signed")
    parser.add_argument("--absent", type=int, help="staff only: current staff who were absent")
    parser.add_argument("--refused", type=int, help="staff only: current staff who refused")
    args = parser.parse_args(argv)

    if not STEP_RE.match(args.step):
        return fail("--step must look like STEP-NN")
    staff_counts = (args.count, args.absent, args.refused)
    if args.role == "staff":
        if any(c is None for c in staff_counts):
            return fail("role staff needs --count, --absent and --refused (counts only, never names)")
        if any(c < 0 for c in staff_counts):
            return fail("counts must be zero or more")
    elif any(c is not None for c in staff_counts):
        return fail("--count, --absent and --refused are only for role staff")

    try:
        date = dt.date.fromisoformat(args.date) if args.date else dt.date.today()
    except ValueError:
        return fail("--date must be YYYY-MM-DD")
    if date > dt.date.today():
        return fail("--date is in the future")

    raw = os.environ.get("PRIVATE_EVIDENCE_DIR", "")
    if not raw:
        return fail("PRIVATE_EVIDENCE_DIR is not set; write the absolute path before the command")
    base = Path(raw)
    if not base.is_absolute():
        return fail("PRIVATE_EVIDENCE_DIR must be an absolute path")
    base = base.resolve()
    if not base.is_dir():
        return fail("PRIVATE_EVIDENCE_DIR is not a directory")
    root = repo_root()
    if base == root or root in base.parents or base in root.parents:
        return fail("PRIVATE_EVIDENCE_DIR must be outside the repository")
    if any((p / ".git").exists() for p in [base, *base.parents]):
        return fail("PRIVATE_EVIDENCE_DIR must not be inside any git checkout")

    folder = base / args.step
    if not folder.is_dir():
        return fail(f"no folder for {args.step} in PRIVATE_EVIDENCE_DIR")
    matches = [p for p in folder.iterdir() if p.name.split(".", 1)[0] == args.label]
    if len(matches) != 1:
        return fail(f"expected exactly one artifact named {args.label}.<ext> for {args.step}, found {len(matches)}")
    artifact = matches[0]
    info = os.lstat(artifact)
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        return fail("artifact must be a regular file, not a link or folder")
    if info.st_size == 0:
        return fail("artifact is empty")
    if base not in artifact.resolve().parents:
        return fail("artifact resolves outside PRIVATE_EVIDENCE_DIR")

    digest = hashlib.sha256()
    with open(artifact, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)

    command = f"python tools/check_artifact.py --step {args.step} --label {args.label} --role {args.role}"
    if args.role == "staff":
        command += f" --count {args.count} --absent {args.absent} --refused {args.refused}"
    command += f" --date {date.isoformat()}"
    print(f"command: {command}")
    print("exit_code: 0")
    print(f"sha256: {digest.hexdigest()} label={args.label}")
    print(f"role: {args.role}")
    if args.role == "staff":
        print(f"count: {args.count} staff_signed")
        print(f"count: {args.absent} staff_absent")
        print(f"count: {args.refused} staff_refused")
    print(f"date: {date.isoformat()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
