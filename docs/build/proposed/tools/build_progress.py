#!/usr/bin/env python3
"""Validate docs/build/status/STEP-NN.json files and generate docs/build/progress.json.

Standard library only. Installs to tools/build_progress.py (G1-protected).

  python tools/build_progress.py            # validate, then write docs/build/progress.json
  python tools/build_progress.py --check    # validate only
  python tools/build_progress.py --root DIR # run against another checkout

Exit 0 when every status file is valid (including when there are none yet), 1 otherwise.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

STATUS_DIR = "docs/build/status"
PROGRESS_PATH = "docs/build/progress.json"

REQUIRED = (
    "id", "title", "track", "lane", "assignee", "status", "depends_on",
    "done_requires", "gate_kind", "gate", "evidence_path",
)
OPTIONAL = ("runs_if", "decision", "findings_path", "blocked_reason")
TRACKS = {"build", "human"}
STATUSES = {"not_started", "in_progress", "blocked", "done"}
GATE_KINDS = {"ci_fixture", "ci_staging", "production_job", "sandbox_spike", "human"}
LANES = {"legal", "vendor", "connector", "platform", "console", "digest", "explain", "rules", "gate"}
DECISION_STEP = "STEP-21"
ID_RE = re.compile(r"^STEP-\d{2}$")


def load_statuses(root: Path) -> tuple[dict[str, dict], list[str]]:
    """Return ({id: status}, errors) for every status file under root."""
    errors: list[str] = []
    statuses: dict[str, dict] = {}
    folder = root / STATUS_DIR
    if not folder.is_dir():
        return statuses, errors
    for path in sorted(folder.glob("*.json")):
        name = path.name
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            errors.append(f"{name}: not valid JSON ({exc.__class__.__name__})")
            continue
        errors.extend(f"{name}: {e}" for e in validate_status(data, name))
        if isinstance(data, dict) and isinstance(data.get("id"), str):
            statuses[data["id"]] = data
    errors.extend(validate_graph(statuses))
    return statuses, errors


def validate_status(data: object, filename: str) -> list[str]:
    errs: list[str] = []
    if not isinstance(data, dict):
        return ["top level must be an object"]
    missing = [k for k in REQUIRED if k not in data]
    if missing:
        errs.append(f"missing fields: {', '.join(missing)}")
    unknown = [k for k in data if k not in REQUIRED and k not in OPTIONAL]
    if unknown:
        errs.append(f"unknown fields: {', '.join(unknown)}")
    sid = data.get("id")
    if not isinstance(sid, str) or not ID_RE.match(sid):
        errs.append("id must look like STEP-NN")
    elif filename != f"{sid}.json":
        errs.append(f"file name must be {sid}.json")
    for key in ("title", "lane", "assignee", "gate", "evidence_path"):
        if key in data and not isinstance(data[key], str):
            errs.append(f"{key} must be a string")
    if not str(data.get("title", "")).strip():
        errs.append("title must not be empty")
    if not str(data.get("gate", "")).strip():
        errs.append("gate must not be empty")
    if data.get("track") not in TRACKS:
        errs.append(f"track must be one of {sorted(TRACKS)}")
    if data.get("lane") not in LANES:
        errs.append(f"lane must be one of {sorted(LANES)}")
    if data.get("status") not in STATUSES:
        errs.append(f"status must be one of {sorted(STATUSES)}")
    if data.get("gate_kind") not in GATE_KINDS:
        errs.append(f"gate_kind must be one of {sorted(GATE_KINDS)}")
    for key in ("depends_on", "done_requires"):
        val = data.get(key)
        if not isinstance(val, list) or not all(isinstance(x, str) and ID_RE.match(x) for x in val):
            errs.append(f"{key} must be a list of STEP-NN ids")
        elif sid in val:
            errs.append(f"{key} must not contain the step itself")
    if isinstance(sid, str) and data.get("evidence_path") != f"docs/build/evidence/{sid}.md":
        errs.append(f"evidence_path must be docs/build/evidence/{sid}.md")
    if data.get("status") == "blocked":
        reason = data.get("blocked_reason")
        if not isinstance(reason, str) or not reason.strip():
            errs.append("blocked steps need a non-empty blocked_reason")
        elif len(reason) > 300 or not reason.isascii():
            errs.append("blocked_reason must be ASCII and at most 300 characters")
    if "runs_if" in data and data["runs_if"] not in ("GO", "NO-GO"):
        errs.append("runs_if must be GO or NO-GO")
    if "decision" in data:
        if sid != DECISION_STEP:
            errs.append(f"only {DECISION_STEP} may carry decision")
        elif data["decision"] not in ("", "GO", "NO-GO"):
            errs.append("decision must be '', GO or NO-GO")
        elif data.get("status") == "done" and data["decision"] not in ("GO", "NO-GO"):
            errs.append("a done decision step needs decision GO or NO-GO")
    if "findings_path" in data:
        fp = data["findings_path"]
        if not (isinstance(fp, str) and fp.startswith("docs/build/findings/") and fp.endswith(".md")):
            errs.append("findings_path must be docs/build/findings/<name>.md")
    return errs


def validate_graph(statuses: dict[str, dict]) -> list[str]:
    errs: list[str] = []
    for sid, st in statuses.items():
        for key in ("depends_on", "done_requires"):
            for dep in st.get(key) or []:
                if isinstance(dep, str) and dep not in statuses:
                    errs.append(f"{sid}: {key} names unknown step {dep}")
    # cycle check over depends_on + done_requires
    WHITE, GREY, BLACK = 0, 1, 2
    colour = {s: WHITE for s in statuses}

    def visit(node: str, trail: list[str]) -> None:
        colour[node] = GREY
        st = statuses[node]
        for dep in list(st.get("depends_on") or []) + list(st.get("done_requires") or []):
            if dep not in statuses:
                continue
            if colour[dep] == GREY:
                errs.append("dependency cycle: " + " -> ".join(trail + [node, dep]))
            elif colour[dep] == WHITE:
                visit(dep, trail + [node])
        colour[node] = BLACK

    for sid in sorted(statuses):
        if colour[sid] == WHITE:
            visit(sid, [])
    return errs


def decision(statuses: dict[str, dict]) -> str:
    return str(statuses.get(DECISION_STEP, {}).get("decision", "") or "")


def effective_state(sid: str, statuses: dict[str, dict]) -> str:
    st = statuses[sid]
    runs_if = st.get("runs_if")
    dec = decision(statuses)
    if runs_if and dec and runs_if != dec:
        return "not_applicable"
    if st["status"] != "not_started":
        return st["status"]
    deps_done = all(statuses.get(d, {}).get("status") == "done" for d in st["depends_on"])
    return "ready" if deps_done else "waiting"


def remaining_critical_path(statuses: dict[str, dict]) -> list[str]:
    """Longest chain (by step count) of steps that are not done, along depends_on."""
    open_steps = {
        s for s in statuses
        if statuses[s]["status"] != "done" and effective_state(s, statuses) != "not_applicable"
    }
    memo: dict[str, list[str]] = {}

    def longest(node: str) -> list[str]:
        if node in memo:
            return memo[node]
        best: list[str] = []
        for dep in statuses[node]["depends_on"]:
            if dep in open_steps:
                cand = longest(dep)
                if len(cand) > len(best):
                    best = cand
        memo[node] = best + [node]
        return memo[node]

    path: list[str] = []
    for s in sorted(open_steps):
        cand = longest(s)
        if len(cand) > len(path):
            path = cand
    return path


def build_progress(statuses: dict[str, dict]) -> dict:
    steps = []
    for sid in sorted(statuses):
        st = statuses[sid]
        steps.append({
            "id": sid,
            "title": st["title"],
            "track": st["track"],
            "lane": st["lane"],
            "assignee": st["assignee"],
            "status": st["status"],
            "state": effective_state(sid, statuses),
            "gate_kind": st["gate_kind"],
        })
    totals: dict[str, int] = {}
    lanes: dict[str, dict[str, int]] = {}
    for s in steps:
        totals[s["state"]] = totals.get(s["state"], 0) + 1
        lane = lanes.setdefault(s["lane"], {})
        lane[s["state"]] = lane.get(s["state"], 0) + 1
    return {
        "step_count": len(steps),
        "totals": totals,
        "decision": decision(statuses),
        "lanes": lanes,
        "remaining_critical_path": remaining_critical_path(statuses),
        "steps": steps,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", default=".", help="repository root (default: current directory)")
    parser.add_argument("--check", action="store_true", help="validate only; do not write progress.json")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    statuses, errors = load_statuses(root)
    if errors:
        for e in errors:
            print(f"error: {e}", file=sys.stderr)
        print(f"status files: {len(statuses)} read, {len(errors)} errors", file=sys.stderr)
        return 1
    progress = build_progress(statuses)
    if not args.check:
        out = root / PROGRESS_PATH
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(progress, indent=2) + "\n", encoding="utf-8")
    print(f"count: {progress['step_count']} steps")
    for state in sorted(progress["totals"]):
        print(f"count: {progress['totals'][state]} {state}")
    if progress["remaining_critical_path"]:
        print("remaining critical path: " + " -> ".join(progress["remaining_critical_path"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
