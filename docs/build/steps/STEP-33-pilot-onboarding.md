# STEP-33 Pilot onboarding on production

Track: build. Lane: platform. Gate kind: production_job. Size: S. Runs only if STEP-21 recorded GO.
Depends on: STEP-05 notice given, acknowledged on paper, posted; STEP-07 Design Partner Agreement and pass line signed; STEP-13 production environment; STEP-21 go/no-go decision recorded (GO); STEP-28 console shift windows and digest settings; STEP-32 roster-read job and acknowledgment mapping. Done requires: none.
Blocks: STEP-34 30-day history pull, STEP-43 pilot-readiness gate.
Sources: Slide 16 (SHF "v1 windows set by owner"), Slide 21 (notice workflow steps 3 and 5; owner-only access; "Us (vendor): support access only when the owner allows it, and every access is in the audit log"), Slide 26 (before day one), Slide 29 (TD1, TD5), Slide 30 (T14, T16), ADR-006, ADR-007; BUILD_PLAN §1 (T16 paper, T14 owner sets windows), design choices 13, 14, 18, 19, 25, 29; D7; T17a code `roster_read_scope_approved`.

## Outcome
**Code.** The step PR extends `tillowl/jobs/onboarding_report.py`. Its default mode (no flag) prints `count: N shift_windows`, `count: N acks_entered`, `count: N acks_mapped`, `count: N acks_unmapped` and `count: N logins_total`, in that order, then `exit_code: N`. It exits 1 if `shift_windows` is 0 or `acks_unmapped` is above 0. STEP-17's `--expect-2fa` mode is unchanged, and STEP-34 adds `--history`.

**Production**, after that PR merges, in order:
1. The founder deploys the release holding STEP-27, 28, 32 and this PR by hand, and runs `migrate`.
2. If STEP-20's evidence says `oauth_connection: revoked` (D7), the owner reconnects Square in the console.
3. The founder runs `roster_read`.
4. The founder enrolls the production support sign-in once with `python -m tillowl.jobs.provision_support_user` (Render one-off job; STEP-27), then the owner grants time-boxed support access in the console.
5. The owner sets the shift windows, or the founder does under the grant.
6. The founder enters each paper acknowledgment and maps it to a login.
7. The founder runs `onboarding_report`.

Only `refresh_tokens` (with `watchdog`) stays scheduled (design choice 25).

## Acceptance criteria
1. **Counts** (`test_onboarding_counts.py`, on `fresh_db`). The cases cover 0 or 2 windows, all acknowledgments mapped or one unmapped, and logins with display names. Each case prints exactly the five lines above, in order, plus `exit_code`, with the exit code the rule gives. No display name, team-member id or date is printed, and the `--expect-2fa` output is unchanged.
2. **Production gate.** Both gate jobs exit 0 on production. The founder compares `acks_entered` with STEP-05's `staff_signed` count plus staff hired since, and explains any gap in the PR as counts only.
3. **Grant and audit.** The founder enters and maps acknowledgments only while the owner's grant is active, and access after it ends is refused. Every grant, entry, mapping and window change writes an audit row (code from STEP-27 and STEP-28).
4. **No order data.** Nothing in this step reads orders: `nightly_pull`, `history_pull` and `run_rules` are not run, and `TILLOWL_JOBS_ENABLED` is unchanged.
5. **Counsel branch.** If `roster_read_scope_approved: NO`, the founder first types each login code and Square team-member id from the Square dashboard into the mapping screen. `roster_read` then makes no Square call and counts those logins.
6. **No staff names.** None appears in the session, PR, evidence or job output. The founder reads the paper acknowledgments in person and never pastes them.

## V-item branches
- **No order fields.** This step reads none, and roster fields are not V-items. Shift windows are needed in every branch: even when V2 is NOT_RETURNED, the fallback sentence still names the shift ("9 checks cancelled during shift Y").
- **Login-bearing items** (V2, V7, and V3–V6 where they carry a login). If any is RETURNED: the mappings made here decide which logins can appear in flags. If none is RETURNED (shift-level-only GO): acknowledgments are still entered and mapped, and the exit rule is unchanged, but no login reaches a flag (STEP-31 strips them all).

## Human confirmation
"Founder: confirm that the owner has agreed to onboarding on production now (the roster read of team-member ids and display names, the support-access grant, the shift windows), whether STEP-20 kept or revoked the OAuth connection (D7), and that you will enter and map the paper acknowledgments yourself in the console, outside this session, never pasting a staff name here."

Print AWAITING HUMAN CONFIRMATION and wait.

## Out of scope
The history pull (STEP-34); enabling any job besides `refresh_tokens`; changing the console screens built in STEP-27, 28 and 32; any staff name in the repo or the session.

## Gate
`python -m tillowl.jobs.roster_read --tenant pilot && python -m tillowl.jobs.onboarding_report --tenant pilot` (exact, from the status file). The gate files are listed in `docs/build/gates/STEP-33.txt`: `tillowl/jobs/roster_read.py` (built in STEP-32, frozen once this step is done) and `tests/gates/step_33/test_onboarding_counts.py`. The founder launches each command as a Render one-off job from their own terminal: `render jobs create <production service id> --start-command "<command>"` (unverified candidate, BUILD_PLAN §10).

`docs/build/evidence/STEP-33.md` holds one block per command: `command:`, `exit_code: 0`, `job_id:`, the job's `count:` lines and `date:`.

## If the gate fails
Revert to the last green commit for code failures. Set the status to `blocked` with a `blocked_reason`, such as `acks_unmapped` or `shift_windows_missing`, with no names. After two failed attempts, restart in a fresh session with a narrower prompt. If `onboarding_report` exits 1, finish the mapping or the windows in the console and re-run the report, which only reads counts. If `roster_read` fails, never retry against the live account without the owner's OK.

## Prompt (paste into a fresh Claude Code session, run from an engineer's account)
```text
You are running STEP-33 "Pilot onboarding on production" for TillOwl. Follow @CLAUDE.md throughout.
Start:
1. git fetch && git rebase origin/main
2. Confirm STEP-05, 07, 13, 21, 28 and 32 are "done" in docs/build/status/, and that STEP-21's "decision" is "GO". If not, stop and say which.
3. Read git log -5.
4. Run CLAUDE.md's setup command.
5. Read @docs/build/steps/STEP-33-pilot-onboarding.md, @docs/build/evidence/STEP-20.md (oauth_connection line), @docs/build/evidence/STEP-05.md (staff_signed count), @docs/build/findings/counsel-t17a-answers.md, and Slides 16, 21, 26, 29 and 30 in @docs/architecture-pack-part1.md and @docs/architecture-pack-part2.md.
6. Print the human-confirmation line and AWAITING HUMAN CONFIRMATION, then wait.
Work, test first:
- Set docs/build/status/STEP-33.json status to "in_progress".
- Write tests/gates/step_33/test_onboarding_counts.py and run it. It fails (print RED TEST (intentional) if you stop here).
- Extend jobs/onboarding_report.py's default mode to the acceptance criteria. Run the test and CLAUDE.md's test command, and show both outputs.
- Commit, then open the step PR with gh. It merges on review.
Production (after merge):
- Print the founder's checklist from the Outcome, in order, with the reconnect step if D7 was revoked and the counsel NO branch if it applies.
- Print both commands, each wrapped as: render jobs create <production service id> --start-command "<command>"
- Print AWAITING HUMAN CONFIRMATION, then wait for the pasted job id, exit code and output.
Done PR: from the pasted output only, write docs/build/evidence/STEP-33.md (one block per command, with job_id and exit_code: 0) and set the status to "done". Run python tools/check_evidence.py validate --step STEP-33, show the output, and open the PR with gh. Its description says the founder approves, then re-runs founder-approval. Never claim success without output.
Out of scope: the history pull, enabling jobs, staff names anywhere.
Use a subagent to review the diff against this step file and report only gaps that affect correctness or the stated acceptance criteria.
```
