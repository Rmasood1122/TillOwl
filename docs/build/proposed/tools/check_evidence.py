#!/usr/bin/env python3
"""Gate integrity (G1), done-means-evidence (G3) and founder approval (G2) checks.

Standard library only. Installs to tools/check_evidence.py (G1-protected).
CI runs the copy from the BASE branch against the PR checkout (--root), so a PR
cannot weaken the check that judges it.

Subcommands (all accept --root DIR, default "."):
  validate [--step STEP-NN | --all]   evidence grammar + status files (local, no network)
  ci --base REF [--head REF] --branch NAME [--repo O/R] [--verify-runs]
                                      G1 path rules + G3 done rules for a PR
  gate-files --kind KIND [--format list|ignore] [--states in_progress,done]
                                      gate test files, for the workflow to pass to pytest
  junit --report FILE [--step STEP-NN]
                                      fail on any skip, xfail, failure or empty gate file
  staging-matrix                      JSON matrix of ci_staging steps to run on main
  criteria                            hash the accepted go/no-go criteria (STEP-18)
  decision                            check and print the go/no-go record (STEP-21)
  manifest                            check the template manifest (and T17b hashes)
  pilot-gate [--repo O/R]             check the STEP-43 conditions (founder's terminal)
  approval --pr N --repo O/R --founder LOGIN --second LOGIN
                                      G2: founder approval on the head commit where needed
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_progress as bp  # noqa: E402  (sibling tool, standard library only)

# ---------------------------------------------------------------- constants

STATUS_DIR = "docs/build/status"
EVIDENCE_DIR = "docs/build/evidence"
FINDINGS_DIR = "docs/build/findings"
GATES_DIR = "docs/build/gates"
CRITERIA = "docs/build/go-no-go-criteria.md"
TEMPLATE_DIR = "tillowl/digest/templates"
MANIFEST = f"{TEMPLATE_DIR}/MANIFEST.json"
CRITERIA_STEP, SPIKE_STEP, DECISION_STEP = "STEP-18", "STEP-20", "STEP-21"
T17B_STEP, PILOT_STEP = "STEP-40", "STEP-43"
SCENARIO_STAGING_STEPS = ("STEP-11", "STEP-24", "STEP-26", "STEP-30", "STEP-31")  # scenarios 4, 2, 4, 3, 1
EARLIEST_DATE = dt.date(2026, 10, 1)

ALWAYS_PROTECTED_PREFIXES = ("tools/", ".github/", ".claude/", f"{GATES_DIR}/")
ALWAYS_PROTECTED_FILES = {
    "conftest.py", "pytest.ini", "CLAUDE.md", "CODEOWNERS", "docs/CODEOWNERS",
    "docs/build/PLANNING_PROMPT.md", CRITERIA,
}
PROTECTED_MIGRATION_RE = re.compile(r"^migrations/\d{4}_(rls|audit_role)[a-z0-9_]*\.sql$")
SECURITY_DDL_RE = re.compile(
    r"\b(ROW\s+LEVEL\s+SECURITY|POLICY|GRANT|REVOKE|BYPASSRLS|CREATE\s+ROLE|ALTER\s+ROLE|DROP\s+ROLE|"
    r"SET\s+ROLE|SECURITY\s+DEFINER|audit_log)\b", re.I)
SKELETON_STEP = "STEP-08"
GATE_TEST_RE = re.compile(r"^tests/gates/step_\d{2}/test_[^/]+\.py$")
GATE_DIR_RE = re.compile(r"^tests/gates/step_(\d{2})/")
SCAN_SKIP = ("docs/build/proposed/",)

LABELS = {
    "counsel_t17a", "counsel_t17b", "sms_optin", "tendlc_approval", "terms_t5", "terms_t6",
    "terms_t8", "t8_template_only", "notice", "ack_batch", "posting", "authorization",
    "support_permission", "dpa", "pass_line", "upfront_invoice", "t1_approval",
    "t1_not_required", "invoice_settlement", "notice_export",
    "findings", "criteria", "template_manifest", "restore_canary",
}
COUNT_UNITS = {
    "passed", "rows", "tenants", "connections", "refreshes", "revokes", "logins_hashed",
    "logins_distinct", "logins_total", "staff_signed", "staff_absent", "staff_refused",
    "acks_entered", "acks_mapped", "acks_unmapped", "shift_windows", "events", "orders",
    "days", "v_items", "flags", "digests", "sms_segments", "tokens_in", "tokens_out",
    "tokens_thinking", "health_checks", "rows_remaining", "owners_2fa", "templates",
    "sample_flags", "scopes", "steps_done",
    "cancelled_orders", "comps", "discounts", "refunds", "no_sale_opens", "item_voids",
}
USD_UNITS = {
    "total", "tokens", "sms", "hosting_web", "hosting_cron", "db_staging", "db_production",
    "email", "lean_line",
}
LINE_RULES: list[tuple[str, re.Pattern]] = [
    ("command", re.compile(r"^command: (?P<v>\S.{0,400})$")),
    ("exit_code", re.compile(r"^exit_code: (?P<v>\d{1,3})$")),
    ("sha256", re.compile(r"^sha256: (?P<v>[0-9a-f]{64}) label=(?P<label>[a-z0-9_]{1,40})$")),
    ("count", re.compile(r"^count: (?P<v>\d{1,9}) (?P<unit>[a-z0-9_]{1,40})$")),
    ("role", re.compile(r"^role: (?P<v>owner|counsel|vendor|staff|founder)$")),
    ("date", re.compile(r"^date: (?P<v>\d{4}-\d{2}-\d{2})$")),
    ("run_id", re.compile(r"^run_id: (?P<v>\d{5,20})$")),
    ("job_id", re.compile(r"^job_id: (?P<v>[A-Za-z0-9][A-Za-z0-9_-]{2,63})$")),
    ("field", re.compile(
        r"^field: (?P<v>[A-Za-z_][A-Za-z0-9_.\[\]]{0,80}) "
        r"type=(?P<type>string|integer|money|timestamp|boolean|enum|object|array|absent)$")),
    ("v_item", re.compile(
        r"^v_item: (?P<v>V[1-8](?:\.[a-z0-9_]{1,30})?) (?P<result>RETURNED|NOT_RETURNED|PARTIAL)$")),
    ("v_shape", re.compile(
        r"^v_shape: (?P<v>V[1-8](?:\.[a-z0-9_]{1,30})?) "
        r"(?P<result>CAN_RETURN|CANNOT_RETURN|NOT_OBSERVABLE_IN_SANDBOX)$")),
    ("scope", re.compile(r"^scope: (?P<v>[A-Z][A-Z0-9_]{2,60})$")),
    ("decision", re.compile(r"^decision: (?P<v>GO|NO-GO)$")),
    ("backup_expires", re.compile(r"^backup_expires: (?P<v>\d{4}-\d{2}-\d{2})$")),
    ("oauth_connection", re.compile(r"^oauth_connection: (?P<v>kept|revoked)$")),
    ("model_id", re.compile(r"^model_id: (?P<v>claude-[a-z0-9-]{3,40})$")),
    ("usd_month", re.compile(r"^usd_month: (?P<v>\d{1,5}\.\d{2}) (?P<unit>[a-z0-9_]{1,40})$")),
    ("release", re.compile(r"^release: (?P<v>[0-9a-f]{40})$")),
    ("passline", re.compile(r"^passline: (?P<v>PASS|FAIL|T11_ZONE|INCOMPLETE)$")),
]
ARTIFACT_EXTRA_FLAGS = {"--date", "--count", "--absent", "--refused"}


class CheckError(Exception):
    pass


# ---------------------------------------------------------------- helpers

def git(root: Path, *args: str, check: bool = True) -> str:
    proc = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise CheckError(f"git {' '.join(args[:2])} failed: {proc.stderr.strip()[:200]}")
    return proc.stdout


def git_show(root: Path, ref: str, path: str) -> str | None:
    proc = subprocess.run(["git", "show", f"{ref}:{path}"], cwd=root, capture_output=True, text=True)
    return proc.stdout if proc.returncode == 0 else None


def gh_json(*args: str) -> object:
    proc = subprocess.run(["gh", *args], capture_output=True, text=True)
    if proc.returncode != 0:
        raise CheckError(f"gh {' '.join(args[:2])} failed: {proc.stderr.strip()[:200]}")
    return json.loads(proc.stdout or "null")


def gh_lines(*args: str) -> list[object]:
    """Run gh with --jq '.[]' style output: one JSON value per line (handles pagination)."""
    proc = subprocess.run(["gh", *args], capture_output=True, text=True)
    if proc.returncode != 0:
        raise CheckError(f"gh {' '.join(args[:2])} failed: {proc.stderr.strip()[:200]}")
    return [json.loads(line) for line in proc.stdout.splitlines() if line.strip()]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_gates_text(text: str) -> set[str]:
    out = set()
    for line in text.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            out.add(line)
    return out


def gates_at_head(root: Path) -> dict[str, set[str]]:
    gates: dict[str, set[str]] = {}
    folder = root / GATES_DIR
    if folder.is_dir():
        for path in sorted(folder.glob("STEP-*.txt")):
            gates[path.stem] = parse_gates_text(path.read_text(encoding="utf-8"))
    return gates


def gates_at_ref(root: Path, ref: str) -> dict[str, set[str]]:
    gates: dict[str, set[str]] = {}
    listing = git(root, "ls-tree", "--name-only", f"{ref}", f"{GATES_DIR}/", check=False)
    for path in listing.split():
        name = Path(path).name
        if name.startswith("STEP-") and name.endswith(".txt"):
            text = git_show(root, ref, path) or ""
            gates[name[:-4]] = parse_gates_text(text)
    return gates


def statuses_at_ref(root: Path, ref: str) -> dict[str, dict]:
    out: dict[str, dict] = {}
    listing = git(root, "ls-tree", "--name-only", f"{ref}", f"{STATUS_DIR}/", check=False)
    for path in listing.split():
        if path.endswith(".json"):
            text = git_show(root, ref, path)
            try:
                data = json.loads(text or "")
            except ValueError:
                continue
            if isinstance(data, dict) and isinstance(data.get("id"), str):
                out[data["id"]] = data
    return out


def load_head(root: Path) -> tuple[dict[str, dict], list[str]]:
    return bp.load_statuses(root)


def gate_commands(status: dict) -> list[str]:
    return [c.strip() for c in status["gate"].split(" && ") if c.strip()]


def normalize_command(cmd: str) -> str:
    """Strip the per-run flags check_artifact.py adds, so the command matches the gate."""
    if not cmd.startswith("python tools/check_artifact.py"):
        return cmd
    try:
        parts = shlex.split(cmd)
    except ValueError:
        return cmd
    kept: list[str] = []
    i = 0
    while i < len(parts):
        part = parts[i]
        if part in ARTIFACT_EXTRA_FLAGS:
            value = parts[i + 1] if i + 1 < len(parts) else ""
            pattern = r"^\d{4}-\d{2}-\d{2}$" if part == "--date" else r"^\d{1,6}$"
            if not re.match(pattern, value):
                return "<invalid artifact flag value>"
            i += 2
            continue
        kept.append(part)
        i += 1
    return " ".join(kept)


def command_kind(cmd: str) -> str:
    if cmd.startswith("pytest ") or cmd.startswith("python -m pytest "):
        return "pytest"
    if cmd.startswith("python tools/check_artifact.py"):
        return "artifact"
    if cmd.startswith("python tools/check_evidence.py"):
        return "tool"
    if cmd.startswith("python -m tillowl.jobs."):
        return "job"
    if cmd.startswith("python spikes/"):
        return "spike"
    return "unknown"


def flag_value(cmd: str, flag: str) -> str | None:
    try:
        parts = shlex.split(cmd)
    except ValueError:
        return None
    for i, part in enumerate(parts[:-1]):
        if part == flag:
            return parts[i + 1]
    return None


# ---------------------------------------------------------------- evidence grammar

def parse_evidence(text: str, sid: str) -> tuple[list[dict], list[str]]:
    """Return (blocks, errors). A block is a command plus the lines after it."""
    errors: list[str] = []
    blocks: list[dict] = []
    lines = text.splitlines()
    if not lines or lines[0] != f"# {sid} evidence":
        errors.append(f"first line must be '# {sid} evidence'")
    for number, line in enumerate(lines[1:], start=2):
        if not line.strip():
            continue
        for kind, rule in LINE_RULES:
            match = rule.match(line)
            if match:
                break
        else:
            errors.append(f"line {number} is not in the evidence grammar")
            continue
        entry = {"kind": kind, **match.groupdict()}
        if kind == "command":
            blocks.append({"command": entry["v"], "lines": []})
            continue
        if not blocks:
            errors.append(f"line {number}: every line must follow a 'command:' line")
            continue
        if kind == "sha256" and entry["label"] not in LABELS:
            errors.append(f"line {number}: sha256 label not allowed")
        if kind == "count" and entry["unit"] not in COUNT_UNITS:
            errors.append(f"line {number}: count unit not allowed")
        if kind == "usd_month" and entry["unit"] not in USD_UNITS:
            errors.append(f"line {number}: usd_month unit not allowed")
        if kind in ("date", "backup_expires"):
            try:
                day = dt.date.fromisoformat(entry["v"])
            except ValueError:
                errors.append(f"line {number}: not a real date")
            else:
                if kind == "date" and not (EARLIEST_DATE <= day <= dt.date.today()):
                    errors.append(f"line {number}: date must be between {EARLIEST_DATE} and today")
        blocks[-1]["lines"].append(entry)
    return blocks, errors


def lines_of(blocks: list[dict], kind: str) -> list[dict]:
    return [e for b in blocks for e in b["lines"] if e["kind"] == kind]


def validate_evidence(root: Path, sid: str, status: dict) -> list[str]:
    path = root / status["evidence_path"]
    if not path.is_file():
        return [f"{sid}: evidence file {status['evidence_path']} is missing"]
    blocks, errors = parse_evidence(path.read_text(encoding="utf-8"), sid)
    errors = [f"{sid}: {e}" for e in errors]
    expected = gate_commands(status)
    got = [normalize_command(b["command"]) for b in blocks]
    if got != expected:
        errors.append(f"{sid}: evidence commands must match the gate exactly, in order "
                      f"({len(expected)} expected, {len(got)} found)")
    for block in blocks:
        cmd, entries = block["command"], block["lines"]
        kinds = [e["kind"] for e in entries]
        exits = [e for e in entries if e["kind"] == "exit_code"]
        if len(exits) != 1:
            errors.append(f"{sid}: each command needs exactly one exit_code line")
        elif exits[0]["v"] != "0":
            errors.append(f"{sid}: exit_code must be 0 for a done step")
        kind = command_kind(cmd)
        if kind == "unknown":
            errors.append(f"{sid}: command kind not recognised")
        if kind == "pytest":
            if "run_id" not in kinds:
                errors.append(f"{sid}: pytest gates need run_id (the green CI run)")
            passed = [int(e["v"]) for e in entries if e["kind"] == "count" and e["unit"] == "passed"]
            if not passed or passed[0] < 1:
                errors.append(f"{sid}: pytest gates need 'count: N passed' with N >= 1")
        if kind == "job" and status["gate_kind"] == "production_job" and "job_id" not in kinds:
            errors.append(f"{sid}: production job commands need job_id")
        if kind == "artifact":
            label, role = flag_value(cmd, "--label"), flag_value(cmd, "--role")
            shas = [e for e in entries if e["kind"] == "sha256"]
            if not shas or shas[0]["label"] != label:
                errors.append(f"{sid}: artifact block needs 'sha256: ... label={label}'")
            roles = [e["v"] for e in entries if e["kind"] == "role"]
            if roles != [role]:
                errors.append(f"{sid}: artifact block needs exactly 'role: {role}'")
            if "date" not in kinds:
                errors.append(f"{sid}: artifact block needs a date line")
            if role == "staff":
                units = {e["unit"] for e in entries if e["kind"] == "count"}
                if not {"staff_signed", "staff_absent", "staff_refused"} <= units:
                    errors.append(f"{sid}: staff acknowledgments need signed, absent and refused counts")
    all_kinds = {e["kind"] for b in blocks for e in b["lines"]}
    if "date" not in all_kinds:
        errors.append(f"{sid}: evidence needs at least one date line")
    gk = status["gate_kind"]
    if gk in ("ci_fixture", "ci_staging") and not any(command_kind(b["command"]) == "pytest" for b in blocks):
        errors.append(f"{sid}: {gk} evidence needs a pytest block")
    if gk == "production_job" and not any(command_kind(b["command"]) == "job" for b in blocks):
        errors.append(f"{sid}: production_job evidence needs a job block")
    signed = any(command_kind(b["command"]) in ("artifact", "tool") for b in blocks)
    if gk == "human" and signed and "role" not in all_kinds:
        errors.append(f"{sid}: human evidence needs a role line")
    if gk == "sandbox_spike" and "findings_path" not in status:
        errors.append(f"{sid}: sandbox_spike steps need findings_path in the status file")
    if "findings_path" in status:
        fpath = root / status["findings_path"]
        shas = [e["v"] for e in lines_of(blocks, "sha256") if e["label"] == "findings"]
        if not fpath.is_file():
            errors.append(f"{sid}: findings file is missing")
        elif shas != [sha256_file(fpath)]:
            errors.append(f"{sid}: 'sha256: ... label=findings' must equal the findings file's SHA-256")
    if sid == PILOT_STEP:
        releases = {e["v"] for e in lines_of(blocks, "release")}
        if len(releases) != 1 or len(lines_of(blocks, "release")) < 2:
            errors.append(f"{sid}: pilot-gate and health_check must print the same release commit")
    if sid == DECISION_STEP:
        decisions = [e["v"] for e in lines_of(blocks, "decision")]
        if decisions != [status.get("decision")]:
            errors.append(f"{sid}: evidence decision must equal the status file's decision")
    return errors


def validate_all(root: Path, only: str | None = None) -> list[str]:
    statuses, errors = load_head(root)
    folder = root / EVIDENCE_DIR
    present = {p.stem for p in folder.glob("STEP-*.md")} if folder.is_dir() else set()
    for sid in sorted(present):
        if only and sid != only:
            continue
        st = statuses.get(sid)
        if st is None:
            errors.append(f"{sid}: evidence file has no status file")
        elif st["status"] != "done":
            errors.append(f"{sid}: evidence exists but the step is not done")
    for sid, st in sorted(statuses.items()):
        if only and sid != only:
            continue
        if st["status"] == "done":
            errors.extend(validate_evidence(root, sid, st))
    return errors


# ---------------------------------------------------------------- repo-wide scans

def scan_pytest_config(root: Path) -> list[str]:
    errors: list[str] = []
    skip_dirs = {".git", ".venv", "venv", "node_modules", "__pycache__"}
    for dirpath, dirnames, filenames in os.walk(root):
        rel_dir = Path(dirpath).relative_to(root).as_posix()
        rel_dir = "" if rel_dir == "." else rel_dir + "/"
        dirnames[:] = [d for d in dirnames if d not in skip_dirs
                       and not f"{rel_dir}{d}/".startswith(SCAN_SKIP)]
        for name in filenames:
            rel = f"{rel_dir}{name}"
            if name == "pytest.ini" and rel != "pytest.ini":
                errors.append(f"{rel}: only the root pytest.ini is allowed")
            elif name == "conftest.py" and rel != "conftest.py" and not rel.startswith("tests/gates/"):
                errors.append(f"{rel}: conftest.py is allowed only at the root and under tests/gates/")
            elif name in ("tox.ini", "setup.cfg", "pyproject.toml"):
                text = (Path(dirpath) / name).read_text(encoding="utf-8", errors="replace")
                if re.search(r"^\[(tool:pytest|pytest|tool\.pytest[^\]]*)\]", text, re.M):
                    errors.append(f"{rel}: must not hold pytest configuration")
    return errors


def check_manifest(root: Path, statuses: dict[str, dict]) -> tuple[str | None, list[str]]:
    errors: list[str] = []
    mpath = root / MANIFEST
    t17b_done = statuses.get(T17B_STEP, {}).get("status") == "done"
    if not mpath.is_file():
        if t17b_done:
            errors.append("template manifest is missing but T17b is done")
        return None, errors
    try:
        files = json.loads(mpath.read_text(encoding="utf-8"))["files"]
        assert isinstance(files, dict)
    except (ValueError, KeyError, AssertionError):
        return None, ["template manifest must be JSON {\"files\": {path: sha256}}"]
    tdir = root / TEMPLATE_DIR
    on_disk = {
        p.relative_to(tdir).as_posix() for p in tdir.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts and p.name != "MANIFEST.json"
    }
    for rel in sorted(on_disk - set(files)):
        errors.append(f"template file {rel} is not in the manifest")
    for rel, digest in sorted(files.items()):
        fpath = tdir / rel
        if not fpath.is_file():
            errors.append(f"manifest lists missing file {rel}")
        elif sha256_file(fpath) != digest:
            errors.append(f"template file {rel} does not match its manifest hash")
    manifest_sha = sha256_file(mpath)
    if t17b_done:
        ev = root / statuses[T17B_STEP]["evidence_path"]
        blocks, _ = parse_evidence(ev.read_text(encoding="utf-8"), T17B_STEP) if ev.is_file() else ([], [])
        recorded = [e["v"] for e in lines_of(blocks, "sha256") if e["label"] == "template_manifest"]
        if recorded != [manifest_sha]:
            errors.append("template manifest changed since counsel review T17b; reopen T17b")
    return manifest_sha, errors


# ---------------------------------------------------------------- CI: G1 + G3

def diff_entries(root: Path, base: str, head: str) -> list[tuple[str, str]]:
    out = git(root, "diff", "--name-status", "-M", f"{base}...{head}")
    entries: list[tuple[str, str]] = []
    for line in out.splitlines():
        parts = line.split("\t")
        code = parts[0][0]
        if code == "R" and len(parts) == 3:
            entries += [("D", parts[1]), ("A", parts[2])]
        elif len(parts) >= 2:
            entries.append((code, parts[1]))
    return entries


def run_ci(root: Path, base: str, head: str, branch: str, repo: str | None, verify: bool) -> list[str]:
    errors: list[str] = []
    gate_change = branch.startswith("gate-change/")
    entries = diff_entries(root, base, head)
    changed = {p for _, p in entries}
    base_st = statuses_at_ref(root, base)
    head_st, st_errors = load_head(root)
    errors += st_errors
    base_gates, head_gates = gates_at_ref(root, base), gates_at_head(root)
    base_done = {s for s, st in base_st.items() if st.get("status") == "done"}
    need_gc = "use a gate-change/ branch approved by the founder"

    for code, path in entries:
        if path in ALWAYS_PROTECTED_FILES or path.startswith(ALWAYS_PROTECTED_PREFIXES):
            if not gate_change:
                errors.append(f"{path}: protected path changed; {need_gc}")
            continue
        if path.startswith("tests/gates/"):
            match = GATE_DIR_RE.match(path)
            if not match:
                if not gate_change:
                    errors.append(f"{path}: shared gate file changed; {need_gc}")
                continue
            sid = f"STEP-{match.group(1)}"
            if code != "D" and path not in head_gates.get(sid, set()):
                errors.append(f"{path}: not named in {GATES_DIR}/{sid}.txt")
            if sid in base_done and not gate_change:
                errors.append(f"{path}: gate file of done step {sid} changed; {need_gc}")
            continue
        owners = [s for s, files in base_gates.items() if path in files]
        if any(s in base_done for s in owners) and not gate_change:
            errors.append(f"{path}: gate-listed file of a done step changed; {need_gc}")
        if PROTECTED_MIGRATION_RE.match(path) and code != "A" and not gate_change:
            errors.append(f"{path}: RLS or audit-role migration changed; {need_gc}")
        if (path.startswith("migrations/") and path.endswith(".sql") and code != "D"
                and not PROTECTED_MIGRATION_RE.match(path) and SKELETON_STEP in base_done and not gate_change):
            text = (root / path).read_text(encoding="utf-8", errors="replace")
            if SECURITY_DDL_RE.search(text):
                errors.append(f"{path}: migration touches RLS, policies, grants, roles or audit_log; {need_gc}")
        if path == MANIFEST and code != "A" and T17B_STEP in base_done and not gate_change:
            errors.append(f"{path}: template manifest changed after T17b; {need_gc}")
        if path.startswith(f"{FINDINGS_DIR}/"):
            owner = [s for s, st in base_st.items() if st.get("findings_path") == path]
            if any(s in base_done for s in owner) and not gate_change:
                errors.append(f"{path}: findings of a done step changed; {need_gc}")

    errors += scan_pytest_config(root)

    status_changes = sorted(p for p in changed if p.startswith(f"{STATUS_DIR}/"))
    if len(status_changes) > 1 and not gate_change:
        errors.append("a PR may change only one status file (its own step's)")
    became_done: list[str] = []
    for path in status_changes:
        sid = Path(path).stem
        before, after = base_st.get(sid), head_st.get(sid)
        if after is None:
            if not gate_change:
                errors.append(f"{path}: status files are removed only by a gate-change PR")
            continue
        if before is None:
            if not gate_change:
                errors.append(f"{path}: new status files arrive only by a gate-change PR")
            continue
        loose = {"status", "assignee", "blocked_reason", "decision"}
        fixed_changed = [k for k in set(before) | set(after) if k not in loose and before.get(k) != after.get(k)]
        if fixed_changed and not gate_change:
            errors.append(f"{sid}: {', '.join(sorted(fixed_changed))} changed; {need_gc}")
        if before.get("decision", "") != after.get("decision", "") and after.get("status") != "done" and not gate_change:
            errors.append(f"{sid}: decision is set only in the done PR")
        b, a = before.get("status"), after.get("status")
        if b == a:
            continue
        if b == "done" and not gate_change:
            errors.append(f"{sid}: a done step changes only through a gate-change PR")
            continue
        deps_done = all(head_st.get(d, {}).get("status") == "done" for d in after.get("depends_on", []))
        runs_if = after.get("runs_if")
        decided = head_st.get(DECISION_STEP, {}).get("decision", "")
        if a in ("in_progress", "done") and runs_if and runs_if != decided:
            errors.append(f"{sid}: runs only on {runs_if}; the recorded decision is {decided or 'not set'}")
        if a == "in_progress" and not deps_done:
            errors.append(f"{sid}: cannot start; depends_on steps are not all done")
        if a == "done":
            if b == "not_started" and after.get("gate_kind") != "human":
                errors.append(f"{sid}: only human gates may go straight from not_started to done")
            became_done.append(sid)

    evidence_changes = sorted(p for p in changed if p.startswith(f"{EVIDENCE_DIR}/") and p.endswith(".md"))
    for path in evidence_changes:
        sid = Path(path).stem
        if sid not in became_done and not gate_change:
            errors.append(f"{path}: evidence changes only in the PR that marks {sid} done")

    for sid in became_done:
        st = head_st[sid]
        errors += validate_evidence(root, sid, st)
        for dep in st.get("depends_on", []) + st.get("done_requires", []):
            if head_st.get(dep, {}).get("status") != "done":
                errors.append(f"{sid}: {dep} must be done before this done PR merges")
        allowed = {f"{STATUS_DIR}/{sid}.json", st["evidence_path"]}
        extra = sorted(changed - allowed)
        if extra and not gate_change:
            errors.append(f"{sid}: a done PR changes only its status and evidence files")
        if st["gate_kind"] in ("ci_fixture", "ci_staging"):
            if verify:
                errors += verify_ci_run(root, sid, st, base, head, repo, head_gates)
            else:
                print(f"note: {sid}: run_id not verified (local run; CI passes --verify-runs)")
    return errors


def evidence_run_id(root: Path, st: dict) -> str | None:
    text = (root / st["evidence_path"]).read_text(encoding="utf-8")
    blocks, _ = parse_evidence(text, st["id"])
    ids = [e["v"] for e in lines_of(blocks, "run_id")]
    return ids[0] if len(ids) == 1 else None


def verify_ci_run(root: Path, sid: str, st: dict, base: str, head: str, repo: str | None,
                  head_gates: dict[str, set[str]]) -> list[str]:
    run_id = evidence_run_id(root, st)
    if run_id is None:
        return [f"{sid}: evidence needs exactly one run_id"]
    args = ["run", "view", run_id, "--json", "headSha,conclusion,workflowName,headBranch,event,jobs"]
    if repo:
        args += ["--repo", repo]
    try:
        run = gh_json(*args)
    except CheckError as exc:
        return [f"{sid}: {exc}"]
    errors: list[str] = []
    if st["gate_kind"] == "ci_fixture":
        commit = git(root, "log", "-1", "--format=%H", f"{base}..{head}", "--", st["evidence_path"]).strip()
        if not commit:
            return [f"{sid}: no commit in this PR adds the evidence file"]
        parent = git(root, "rev-parse", f"{commit}^").strip()
        touched = set(git(root, "diff", "--name-only", parent, commit).split())
        if touched - {st["evidence_path"], f"{STATUS_DIR}/{sid}.json"}:
            errors.append(f"{sid}: the evidence commit must change only this step's evidence and status")
        if run.get("workflowName") != "ci" or run.get("conclusion") != "success":
            errors.append(f"{sid}: run {run_id} is not a green 'ci' run")
        if run.get("headSha") != parent:
            errors.append(f"{sid}: run {run_id} must be on the evidence commit's parent")
        parent_status = json.loads(git_show(root, parent, f"{STATUS_DIR}/{sid}.json") or "{}")
        if parent_status.get("status") != "in_progress":
            errors.append(f"{sid}: the step must be in_progress on the commit the run tested")
    else:
        jobs = {j.get("name"): j.get("conclusion") for j in run.get("jobs") or []}
        if (run.get("workflowName") != "staging" or run.get("headBranch") != "main"
                or run.get("event") not in ("push", "workflow_dispatch")):
            errors.append(f"{sid}: run {run_id} is not a 'staging' push run on main")
        if jobs.get(f"gate {sid}") != "success":
            errors.append(f"{sid}: job 'gate {sid}' in run {run_id} is not green")
        sha = run.get("headSha") or ""
        ok = all(subprocess.run(["git", "merge-base", "--is-ancestor", sha, ref], cwd=root).returncode == 0
                 for ref in (base, head))
        if not ok:
            errors.append(f"{sid}: run {run_id} is not on main's history")
        else:
            files = sorted(head_gates.get(sid, set()))
            if files and subprocess.run(["git", "diff", "--quiet", sha, head, "--", *files], cwd=root).returncode != 0:
                errors.append(f"{sid}: gate files changed after run {run_id}")
    return errors


# ---------------------------------------------------------------- gate files, junit, matrix

def gate_test_files(gates: dict[str, set[str]], sid: str) -> list[str]:
    return sorted(p for p in gates.get(sid, set()) if GATE_TEST_RE.match(p))


def cmd_gate_files(root: Path, kind: str, states: set[str], fmt: str) -> int:
    statuses, errors = load_head(root)
    if errors:
        raise CheckError("; ".join(errors[:5]))
    gates = gates_at_head(root)
    files: list[str] = []
    for sid, st in sorted(statuses.items()):
        if st["gate_kind"] == kind and (not states or st["status"] in states):
            files += gate_test_files(gates, sid)
    if fmt == "ignore":
        print(" ".join(f"--ignore={f}" for f in files))
    else:
        print(" ".join(files))
    return 0


def cmd_junit(root: Path, report: Path, only: str | None) -> list[str]:
    statuses, errors = load_head(root)
    gates = gates_at_head(root)
    if only:
        targets = [only]
    else:
        targets = [s for s, st in statuses.items()
                   if st["gate_kind"] == "ci_fixture" and st["status"] in ("in_progress", "done")]
    tree = ET.parse(report)
    per_file: dict[str, dict[str, int]] = {}
    total_bad = 0
    for case in tree.iter("testcase"):
        file_attr = case.get("file") or ""
        if not file_attr:
            classname = case.get("classname") or ""
            file_attr = "/".join(classname.split(".")[:-1]) + ".py" if classname else ""
        counts = per_file.setdefault(file_attr, {"passed": 0, "bad": 0})
        if case.find("skipped") is not None or case.find("failure") is not None or case.find("error") is not None:
            counts["bad"] += 1
            total_bad += 1
        else:
            counts["passed"] += 1
    if total_bad:
        errors.append(f"{total_bad} test(s) skipped, xfailed, failed or errored")
    for sid in sorted(targets):
        files = gate_test_files(gates, sid)
        if not files:
            errors.append(f"{sid}: no gate test files listed in {GATES_DIR}/{sid}.txt")
        for f in files:
            counts = per_file.get(f, {"passed": 0, "bad": 0})
            if counts["passed"] == 0:
                errors.append(f"{sid}: {f} collected zero passing tests")
            if counts["bad"]:
                errors.append(f"{sid}: {f} has skipped, xfailed or failing tests")
    if not errors:
        print(f"count: {len(targets)} steps_done")
    return errors


def cmd_staging_matrix(root: Path) -> int:
    statuses, errors = load_head(root)
    if errors:
        raise CheckError("; ".join(errors[:5]))
    gates = gates_at_head(root)
    include = []
    for sid, st in sorted(statuses.items()):
        if st["gate_kind"] == "ci_staging" and st["status"] in ("in_progress", "done"):
            include.append({"step": sid, "files": " ".join(gate_test_files(gates, sid))})
    print(json.dumps({"any": bool(include), "matrix": {"include": include or [{"step": "none", "files": ""}]}}))
    return 0


# ---------------------------------------------------------------- criteria, decision, pilot gate

def criteria_sha(root: Path) -> str:
    path = root / CRITERIA
    if not path.is_file():
        raise CheckError(f"{CRITERIA} is missing")
    if re.search(r"\bDRAFT\b", path.read_text(encoding="utf-8")):
        raise CheckError(f"{CRITERIA} still says DRAFT; the founder accepts it by removing the marker")
    return sha256_file(path)


def evidence_blocks(root: Path, statuses: dict[str, dict], sid: str) -> list[dict]:
    st = statuses.get(sid)
    if not st or st.get("status") != "done":
        raise CheckError(f"{sid} is not done")
    path = root / st["evidence_path"]
    blocks, errs = parse_evidence(path.read_text(encoding="utf-8"), sid)
    if errs:
        raise CheckError(f"{sid} evidence is invalid")
    return blocks


def cmd_criteria(root: Path) -> int:
    digest = criteria_sha(root)
    print("command: python tools/check_evidence.py criteria")
    print("exit_code: 0")
    print(f"sha256: {digest} label=criteria")
    print("role: founder")
    print(f"date: {dt.date.today().isoformat()}")
    return 0


def cmd_decision(root: Path) -> int:
    statuses, errors = load_head(root)
    if errors:
        raise CheckError("; ".join(errors[:5]))
    dec = statuses.get(DECISION_STEP, {}).get("decision")
    if dec not in ("GO", "NO-GO"):
        raise CheckError(f"set decision to GO or NO-GO in {STATUS_DIR}/{DECISION_STEP}.json first")
    spike = evidence_blocks(root, statuses, SPIKE_STEP)
    items = {e["v"]: e["result"] for e in lines_of(spike, "v_item")}
    missing = [f"V{n}" for n in range(1, 9) if f"V{n}" not in items]
    if missing:
        raise CheckError(f"{SPIKE_STEP} evidence lacks results for {', '.join(missing)}")
    accepted = [e["v"] for e in lines_of(evidence_blocks(root, statuses, CRITERIA_STEP), "sha256")
                if e["label"] == "criteria"]
    current = criteria_sha(root)
    if accepted != [current]:
        raise CheckError("the go/no-go criteria changed after they were accepted")
    print("command: python tools/check_evidence.py decision")
    print("exit_code: 0")
    print(f"decision: {dec}")
    for item in sorted(items, key=lambda s: (int(s[1]), s)):
        print(f"v_item: {item} {items[item]}")
    print(f"sha256: {current} label=criteria")
    print("role: founder")
    print(f"date: {dt.date.today().isoformat()}")
    return 0


def cmd_manifest(root: Path) -> list[str]:
    statuses, errors = load_head(root)
    digest, m_errors = check_manifest(root, statuses)
    errors += m_errors
    if not errors:
        print("command: python tools/check_evidence.py manifest")
        print("exit_code: 0")
        if digest:
            print(f"sha256: {digest} label=template_manifest")
        print(f"date: {dt.date.today().isoformat()}")
    return errors


def cmd_pilot_gate(root: Path, repo: str | None, skip_runs: bool) -> list[str]:
    statuses, errors = load_head(root)
    pilot = statuses.get(PILOT_STEP)
    if not pilot:
        return errors + [f"{PILOT_STEP} status file is missing"]
    for dep in pilot["depends_on"]:
        if statuses.get(dep, {}).get("status") != "done":
            errors.append(f"{dep} is not done")
    if statuses.get(DECISION_STEP, {}).get("decision") != "GO":
        errors.append("the recorded decision is not GO")
    errors += check_manifest(root, statuses)[1]
    if statuses.get(T17B_STEP, {}).get("status") != "done":
        errors.append("counsel review T17b is not done")

    def labels(sid: str) -> set[str]:
        try:
            return {e["label"] for e in lines_of(evidence_blocks(root, statuses, sid), "sha256")}
        except CheckError as exc:
            errors.append(str(exc))
            return set()

    if not {"sms_optin", "tendlc_approval", "terms_t6"} <= labels("STEP-03"):
        errors.append("STEP-03 lacks the opt-in, 10DLC approval or Twilio terms")
    terms = labels("STEP-04")
    if "terms_t5" not in terms or not ({"terms_t8", "t8_template_only"} & terms):
        errors.append("STEP-04 lacks the email terms, or T8 terms / the template-only decision")
    staging_release = ""
    if skip_runs:
        errors.append("run checks skipped; this output cannot serve as evidence")
    else:
        repo_args = ["--repo", repo] if repo else []
        for workflow in ("ci", "staging"):
            runs = gh_json("run", "list", "--workflow", workflow, "--branch", "main", "--event", "push",
                           "--limit", "1",
                           "--json", "databaseId,conclusion,headSha", *repo_args)
            if not runs or runs[0].get("conclusion") != "success":
                errors.append(f"latest '{workflow}' run on main is not green")
            elif workflow == "staging":
                staging_release = runs[0].get("headSha", "")
                run = gh_json("run", "view", str(runs[0]["databaseId"]), "--json", "jobs", *repo_args)
                jobs = {j.get("name"): j.get("conclusion") for j in run.get("jobs") or []}
                for sid in SCENARIO_STAGING_STEPS:
                    if jobs.get(f"gate {sid}") != "success":
                        errors.append(f"scenario gate {sid} is not green in the latest staging run")
    if not errors:
        print("command: python tools/check_evidence.py pilot-gate")
        print("exit_code: 0")
        print(f"count: {len(pilot['depends_on'])} steps_done")
        print(f"release: {staging_release}")
        print("role: founder")
        print(f"date: {dt.date.today().isoformat()}")
    return errors


# ---------------------------------------------------------------- G2: founder approval

def needs_founder(root: Path, base: str, files: list[str], branch: str) -> list[str]:
    reasons: list[str] = []
    if branch.startswith("gate-change/"):
        reasons.append("gate-change branch")
    head_st, _ = load_head(root)
    base_st = statuses_at_ref(root, base)
    for path in files:
        if path in ALWAYS_PROTECTED_FILES or path.startswith(ALWAYS_PROTECTED_PREFIXES):
            reasons.append(f"protected path {path}")
        elif path.startswith((f"{EVIDENCE_DIR}/", f"{FINDINGS_DIR}/")):
            reasons.append(f"evidence or findings {path}")
        elif path.startswith(f"{STATUS_DIR}/"):
            sid = Path(path).stem
            kinds = {head_st.get(sid, {}).get("gate_kind"), base_st.get(sid, {}).get("gate_kind")}
            if kinds & {"human", "production_job", "sandbox_spike"}:
                reasons.append(f"status of founder-gated step {sid}")
    return reasons


def cmd_approval(root: Path, pr: int, repo: str, founder: str, second: str) -> list[str]:
    info = gh_json("api", f"repos/{repo}/pulls/{pr}")
    files = [str(f) for f in gh_lines("api", "--paginate", f"repos/{repo}/pulls/{pr}/files",
                                      "--jq", ".[].filename | @json")]
    head_sha, author = info["head"]["sha"], info["user"]["login"]
    branch, body = info["head"]["ref"], info.get("body") or ""
    base = f"origin/{info['base']['ref']}"
    reasons = needs_founder(root, base, files, branch)
    if not reasons:
        print("founder approval not required")
        return []
    reviews = gh_lines("api", "--paginate", f"repos/{repo}/pulls/{pr}/reviews", "--jq", ".[]")
    latest: dict[str, dict] = {}
    for review in reviews or []:
        if review.get("state") in ("APPROVED", "CHANGES_REQUESTED", "DISMISSED"):
            latest[review["user"]["login"].lower()] = review

    def approved_by(login: str) -> bool:
        r = latest.get(login.lower())
        return bool(r) and r.get("state") == "APPROVED" and r.get("commit_id") == head_sha

    print("founder approval required: " + "; ".join(sorted(set(reasons)))[:500])
    if author.lower() == founder.lower():
        if not re.search(r"^Founder sign-off: \d{4}-\d{2}-\d{2}\s*$", body, re.M):
            return ["the founder opened this PR: add a line 'Founder sign-off: YYYY-MM-DD' to the description"]
        if not approved_by(second):
            return [f"the founder opened this PR: {second} must approve the latest commit"]
        return []
    if not approved_by(founder):
        return [f"{founder} must approve the latest commit, then re-run this check"]
    return []


# ---------------------------------------------------------------- main

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="TillOwl gate integrity and evidence checks.")
    parser.add_argument("--root", default=".", help="checkout to check (default: current directory)")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("validate")
    p.add_argument("--step")
    p.add_argument("--all", action="store_true")
    p = sub.add_parser("ci")
    p.add_argument("--base", required=True)
    p.add_argument("--head", default="HEAD")
    p.add_argument("--branch", required=True)
    p.add_argument("--repo")
    p.add_argument("--verify-runs", action="store_true")
    p = sub.add_parser("gate-files")
    p.add_argument("--kind", required=True, choices=sorted(bp.GATE_KINDS))
    p.add_argument("--states", default="")
    p.add_argument("--format", default="list", choices=["list", "ignore"])
    p = sub.add_parser("junit")
    p.add_argument("--report", required=True)
    p.add_argument("--step")
    sub.add_parser("staging-matrix")
    sub.add_parser("criteria")
    sub.add_parser("decision")
    sub.add_parser("manifest")
    p = sub.add_parser("pilot-gate")
    p.add_argument("--repo")
    p.add_argument("--skip-run-check", action="store_true")
    p = sub.add_parser("approval")
    p.add_argument("--pr", required=True, type=int)
    p.add_argument("--repo", required=True)
    p.add_argument("--founder", required=True)
    p.add_argument("--second", required=True)
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()

    try:
        if args.cmd == "validate":
            if args.step and not bp.ID_RE.match(args.step):
                raise CheckError("--step must look like STEP-NN")
            errors = validate_all(root, args.step)
        elif args.cmd == "ci":
            errors = run_ci(root, args.base, args.head, args.branch, args.repo, args.verify_runs)
            errors += validate_all(root)
            errors += check_manifest(root, load_head(root)[0])[1]
        elif args.cmd == "gate-files":
            states = {s for s in args.states.split(",") if s}
            return cmd_gate_files(root, args.kind, states, args.format)
        elif args.cmd == "junit":
            errors = cmd_junit(root, Path(args.report), args.step)
        elif args.cmd == "staging-matrix":
            return cmd_staging_matrix(root)
        elif args.cmd == "criteria":
            return cmd_criteria(root)
        elif args.cmd == "decision":
            return cmd_decision(root)
        elif args.cmd == "manifest":
            errors = cmd_manifest(root)
        elif args.cmd == "pilot-gate":
            errors = cmd_pilot_gate(root, args.repo, args.skip_run_check)
        elif args.cmd == "approval":
            errors = cmd_approval(root, args.pr, args.repo, args.founder, args.second)
        else:  # pragma: no cover
            raise CheckError("unknown subcommand")
    except CheckError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    # de-duplicate while keeping order
    seen: set[str] = set()
    errors = [e for e in errors if not (e in seen or seen.add(e))]
    for e in errors:
        print(f"error: {e}", file=sys.stderr)
    if errors:
        print(f"{len(errors)} problem(s) found", file=sys.stderr)
        return 1
    if args.cmd in ("validate", "ci"):
        print("ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
