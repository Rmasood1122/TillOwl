# TillOwl: rules for every Claude Code session

You run one step from `docs/build/steps/STEP-NN-*.md`. Follow it; the rules below always apply.

## Setup (run first in every fresh worktree)
`python3 -m venv .venv && if [ -f pyproject.toml ]; then .venv/bin/pip install -q -e '.[dev]'; else .venv/bin/pip install -q 'pytest==8.*'; fi`

## Test command
`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -c pytest.ini --rootdir=. tests`
A gate is the same command with the paths in the step's status file. Never add other pytest config.

## Evidence rule
- A step is done only when `docs/build/evidence/STEP-NN.md` passes `python tools/check_evidence.py validate --step STEP-NN`.
- Evidence holds only the gate command, its exit code and allowlisted lines (counts, hashes, run or job ids, field names); see `docs/build/evidence/README.md`. Never names, values, staff identifiers or raw output.
- Show the command you ran and its output. Never claim success without it.

## Gate-edit rule
- Never edit or delete a gate check to make it pass: `tests/gates/` of a done step, `docs/build/gates/`, `tools/`, `conftest.py`, `pytest.ini`, `.github/`, `.claude/`, this file, the go/no-go criteria, the template manifest, or the RLS and audit-role migrations.
- Never use `--no-verify`, skip CI, or disable a check. If a gate is wrong, set your step to `blocked` with a `blocked_reason` and stop.
- Gate changes go in a separate PR on a branch made with `git switch -c gate-change/step-NN-reason`; the founder approves it.
- Edit only your own step's status file.
- If you stop after writing the failing test, print `RED TEST (intentional)`.

## Human-confirmation rule
Before anything that touches the friend's live account, real staff data or production secrets, or that sends to a real phone or email:
1. Print the exact command the founder runs in their own terminal, with absolute paths written out.
2. Print `AWAITING HUMAN CONFIRMATION` and stop until the founder answers with the pasted output.
- Never run `tools/check_artifact.py`, read `$PRIVATE_EVIDENCE_DIR`, use the Render CLI, or hold production credentials.
- Never approve, merge or push to main.

## On failure
Revert to the last green commit, set the step to `blocked` with the failing output summarised (no names or values), and after two failed attempts restart in a fresh session with a narrower prompt.
