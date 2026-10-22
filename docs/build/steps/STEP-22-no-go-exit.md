# STEP-22 No-go exit (runs only on NO-GO)

Track: build. Lane: platform. Gate kind: production_job. Size: M.
Depends on: STEP-21 Go/no-go decision recorded, with `decision: NO-GO` (`runs_if: "NO-GO"`). Done requires: none.
Blocks: none. On GO this step never starts and stays `not_started`.
Sources: Slide 17 (data rules: "CSV of all flagged events for 30 days, then deletion per contract"; retention beyond that TBD), Slide 21 (exit rights, audit log, vendor support access, notice records belong to the employer), Slide 26 (DPA, 10–20% up front), Slide 29 (RK1), Slide 30 (T15), ADR-003, ADR-007; BUILD_PLAN design choices 9, 11, 25, 28, 29, 34; D7, D8, D9; `docs/build/go-no-go-criteria.md` §4.

## Outcome
`tillowl/jobs/exit_tenant.py` (`python -m tillowl.jobs.exit_tenant --tenant pilot`) does, in this order:
1. **Preflight.** Refuses (exit 1, nothing changed) unless `docs/build/status/STEP-21.json` in the deployed release records `NO-GO`.
2. **Revoke** the pilot's Square OAuth authorization with the revoke call in `tillowl/square/oauth.py` (STEP-11; exercised in STEP-16) and delete the encrypted token row. If the revoke fails, it stops before deleting anything.
3. **Notice and acknowledgment export.** Counts the pilot's notice and acknowledgment rows. With paper T16 they are entered only in STEP-33, after GO, so on NO-GO the count is 0: the owner keeps the paper originals. If any rows exist, the job refuses before deleting and names the code `notice_rows_present`; an export path then needs its own reviewed change.
4. **Delete** every pilot-tenant row in every tenant table. It keeps only the `audit_log` rows for the spike (V-item results, spike deletion) and for this exit, plus the tenant key row they point to with its name cleared. They are kept for D9's period (T15).
5. **Audit-log** the revoke and the deletion through `audit()`, with counts only.
6. **Record** `backup_expires`: the deletion date plus the production backup retention set in `tillowl/config.py` (STEP-13: 7-day PITR, an unverified candidate). The job refuses if that retention exceeds the 14-day cap in the owner's authorization.

It prints only evidence-grammar lines: `oauth_connection: revoked`, `count: 1 revokes`, `count: 0 acks_entered`, `count: N rows` (rows deleted), `backup_expires: YYYY-MM-DD`, `exit_code: N`.

Then `verify_deleted --tenant pilot --scope tenant`, implemented and frozen in STEP-19 (not edited here), proves `count: 0 rows_remaining`. The founder settles the up-front fee as the signed DPA says (`invoice_settlement`), and the owner signs a receipt for the notice and acknowledgment records (`notice_export`).

## Acceptance criteria
1. Given `tests/gates/step_22/test_exit_tenant.py`, `pytest -c pytest.ini --rootdir=. tests/gates/step_22` passes on the local database fixture:
   - seed two synthetic tenants with rows in every tenant table of the STEP-08 schema;
   - stub the Square revoke;
   - run `exit_tenant` for `pilot`.
   For every tenant table, zero pilot rows remain except the kept audit rows and the cleared tenant key row. The other tenant's rows are unchanged, row for row.
2. The job refuses, changing nothing, when the release's decision is GO or unset, when the revoke stub fails, when notice or acknowledgment rows exist, or when retention exceeds 14 days.
3. A second run after a successful one exits 0 with `count: 0 rows` and changes nothing.
4. Every stdout line matches the grammar in `docs/build/evidence/README.md`: no names, values, ids or tokens. The job deletes through its own role, and the audit role stays insert-only.
5. The kept audit rows are exactly what STEP-19's `verify_deleted --scope tenant` exempts; the test runs it and expects `count: 0 rows_remaining`. If STEP-19's scope disagrees, set `blocked` (see below), never edit `verify_deleted`.
6. Nothing writes to Square beyond the revoke, and nothing touches the POS, payroll or schedules.

## Human confirmation
"Founder: STEP-21 recorded NO-GO. Confirm that the owner has been told, that the release containing `exit_tenant` is deployed to production by you, and that I may print the commands that revoke Square access and delete the pilot tenant's data now." Print AWAITING HUMAN CONFIRMATION and wait.

## Out of scope
Deleting the kept audit rows (D9, later); the 30-day flagged-event CSV export (no flags exist before GO; STEP-29 covers termination after a pilot); editing `verify_deleted`; any GO-path step.

## Gate
Exact, from `docs/build/status/STEP-22.json`:
`python -m tillowl.jobs.exit_tenant --tenant pilot && python -m tillowl.jobs.verify_deleted --tenant pilot --scope tenant && python tools/check_artifact.py --step STEP-22 --label notice_export --role owner && python tools/check_artifact.py --step STEP-22 --label invoice_settlement --role founder`

Gate files: `docs/build/gates/STEP-22.txt` (`tillowl/jobs/exit_tenant.py`, `tests/gates/step_22/test_exit_tenant.py`).

`docs/build/evidence/STEP-22.md` holds four blocks in gate order:
- two job blocks, each with `job_id:` and `exit_code: 0` (plus the lines above, and `count: 0 rows_remaining`);
- two artifact blocks, each with `sha256: … label=notice_export` or `label=invoice_settlement`, `role:` and `date:`.

## If the gate fails
- Revert to the last green commit. Set `blocked` with a `blocked_reason` code (`revoke_failed`, `notice_rows_present`, `verify_scope_mismatch`, `retention_over_cap`); no names or values. After two failed attempts, restart in a fresh session with a narrower prompt.
- Never re-run a job against the live account or the production database without the owner's and the founder's OK.

## Prompt (paste into a fresh Claude Code session, run from an engineer's account)
```text
You are running STEP-22 "No-go exit" for TillOwl. Follow @CLAUDE.md throughout.
Start: git fetch && git rebase origin/main; confirm STEP-21 is "done" with "decision": "NO-GO" in docs/build/status/STEP-21.json (stop and say so if not); read git log -5; run CLAUDE.md's setup command; read @docs/build/steps/STEP-22-no-go-exit.md, @tillowl/jobs/verify_deleted.py, @tillowl/square/oauth.py, @tillowl/audit.py, @tillowl/config.py and Slides 17, 21, 26, 29, 30 in @docs/architecture-pack-part2.md.
Print the human-confirmation line and AWAITING HUMAN CONFIRMATION; wait.
Step PR, test first:
- Set docs/build/status/STEP-22.json status to "in_progress".
- Write tests/gates/step_22/test_exit_tenant.py to the acceptance criteria (synthetic tenants only; Square revoke stubbed; no network). Run it; it fails (print RED TEST (intentional) if you stop here).
- Write tillowl/jobs/exit_tenant.py. Run CLAUDE.md's test command and show the command and its output. Commit and open the step PR with gh; it merges on review.
After merge (founder only; you never hold production credentials or use the Render CLI):
- Print the two job commands for the founder to launch as Render one-off jobs from their own terminal (render jobs create, an unverified candidate), and the two check_artifact.py commands with the D4 absolute path from BUILD_PLAN §1 written out (PRIVATE_EVIDENCE_DIR=<path> python tools/check_artifact.py ... --date YYYY-MM-DD). Print AWAITING HUMAN CONFIRMATION; wait for the pasted job ids, exit codes and outputs.
Done PR: one commit on top of main with only docs/build/evidence/STEP-22.md (four blocks from the pasted output, nothing added) and status "done". Run python tools/check_evidence.py validate --step STEP-22 and show the output; never claim success without it. Open it with gh; the description says the founder approves and then re-runs founder-approval.
Out of scope: deleting kept audit rows (D9), editing verify_deleted, the flagged-event CSV export, any GO-path step.
Use a subagent to review the diff against this step file and report only gaps that affect correctness or the stated acceptance criteria.
```
