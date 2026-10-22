# STEP-30 Audit-log coverage and scenario 3 (tenant isolation, owner-only access)

Track: build. Lane: platform. Gate kind: ci_staging. Size: S.
Depends on: STEP-19 live-spike job code (V-item audit rows), STEP-26 digest build and delivery, STEP-27 console notices, acknowledgments and support access, STEP-28 shift windows and digest settings, STEP-29 CSV export and termination path. Done requires: none.
Blocks: STEP-43 pilot-readiness gate (scenario 3 must be green on staging).
Sources: Slide 17–18 (AUD "append-only"; Q5 "has every sign-in, change and export written to"; Q11; "Every table carries tenant_id, and the owner sees only their own tenant"), Slide 21 (tenant isolation: "automated tests try to read across tenants"; audit log; owner-only access; "who sees what"), Slide 24 (scenario 3: "Row-level security returns nothing; staff have no accounts; the attempt goes in the audit log"), Slide 30 ("Each test result goes into the audit log"), ADR-007; BUILD_PLAN §7 (`FORCE ROW LEVEL SECURITY`, `migrations/0002_rls.sql`, `migrations/0003_audit_role.sql`), design choice 33.

## Outcome
`tillowl/audit.py` holds one authoritative `EVENT_TYPES` list, and two gate files prove on the staging schema that every listed event writes its audit row and that no tenant can see another's data. The list covers:
- sign-in: `sign_in`, `sign_in_failed`;
- failed or denied access: `access_denied`;
- settings: `settings_changed`;
- exports: `export`, `tenant_terminated`, `tenant_deleted`;
- digests sent: `digest_sent`, `digest_skipped`, `reconnect_sent`;
- notices and acknowledgments entered: `notice_recorded`, `notice_posted`, `ack_entered`, `ack_mapped`;
- V-item results: STEP-19's per-item rows;
- support access: `support_grant_created`, `support_grant_revoked`, and every support action, which carries its grant id.
Code fixes found here go in this step's PR: a missing `audit()` call, or a route that leaks.

## Acceptance criteria
1. `test_audit_coverage.py` is parametrized over `EVENT_TYPES`, so adding a type without a covering case fails it. For each type, it drives the real code path on `staging_schema`: the console's FastAPI test client, `run_digest` with stubbed vendors, and `square_live_report` against STEP-19's stubbed fixtures (read, not copied). It asserts exactly one new `audit_log` row with the right actor, action, target, `tenant_id` and a time inside the test's clock window. The founder entering a shift window under a grant (STEP-27 with STEP-28) logs the grant id.
2. A static scan of `tillowl/` finds no `audit(` call whose action is outside `EVENT_TYPES`. The application role and the audit role each get "permission denied" on `UPDATE` and `DELETE` of `audit_log`. No audit row's text holds a fixture display name (placeholders like `DN-L07`).
3. `test_scenario3_isolation.py`, on `staging_schema`, with two synthetic tenants that have rows in every table carrying `tenant_id` (found through `information_schema`, so a new table is covered without editing the test):
   - every such table has both `relrowsecurity` and `relforcerowsecurity` true;
   - as the application role with tenant A set: zero rows of B from every table; `UPDATE` and `DELETE` aimed at B's rows touch 0 rows; an `INSERT` carrying B's `tenant_id` is rejected;
   - with no tenant set: zero rows from every tenant table (fail closed);
   - as the table-owning role (the staging URL's user, which applied the migrations): the same zero-row results, because of `FORCE ROW LEVEL SECURITY`. The test first asserts this role is neither superuser nor `BYPASSRLS` in `pg_roles`, and fails loudly if it is, since such a role bypasses RLS even when forced.
4. Console probes in the same file:
   - owner A requesting B's flag, export or settings gets a response with no B data, and exactly one `access_denied` row is written;
   - a sign-in with any staff login code (for example `L07`) fails and writes `sign_in_failed`;
   - no user row exists for any staff login (staff have no accounts).
5. The tests send nothing real (vendors stubbed; the staging gate job holds no vendor keys) and use synthetic data only. Locally, tests that need `staging_schema` fail with that fixture's "runs only in the CI staging workflow" message by design (G4).

## Out of scope
New features. Audit-row retention (D9). Production audit review. Load or penetration testing.

## Gate
`pytest -c pytest.ini --rootdir=. tests/gates/step_30`, exact, from `docs/build/status/STEP-30.json`; the gate files are in `docs/build/gates/STEP-30.txt`. It runs in the `staging` workflow's job `gate STEP-30` on `main` after the step PR merges. `docs/build/evidence/STEP-30.md` holds one block: `command:` (the gate), `exit_code: 0`, `count: N passed` (from that job's JUnit summary), `run_id:` (that `staging` run), `date:`. STEP-43's `pilot-gate` also checks this job in the latest push run.

## If the gate fails
Revert to the last green commit. Set the status to `blocked` with a `blocked_reason` that holds no names or values (for example `rls_not_forced_on_table` or `owner_role_bypasses_rls`). After two failed attempts, restart in a fresh session with a narrower prompt. An RLS or role fix touches `migrations/0002_rls.sql` territory, so it goes in a gate-change PR the founder approves (design choice 33), never in this PR.

## Prompt (paste into a fresh Claude Code session)
```text
You are running STEP-30 "Audit-log coverage and scenario 3" for TillOwl. Follow @CLAUDE.md throughout.
Start:
1. git fetch && git rebase origin/main
2. Confirm STEP-19, STEP-26, STEP-27, STEP-28 and STEP-29 are "done" in docs/build/status/; if any is not, stop and say which. Read git log -5.
3. Run CLAUDE.md's setup command.
4. Read @docs/build/steps/STEP-30-audit-coverage.md, @docs/build/BUILD_PLAN.md §7 and §11, @tillowl/audit.py, @migrations/, @conftest.py (staging_schema), the console, digest and live_report code, and Slides 17, 18, 21, 24, 30 in @docs/architecture-pack-part2.md.
Work, test first:
- Set docs/build/status/STEP-30.json status to "in_progress".
- Write the gate files exactly as listed in docs/build/gates/STEP-30.txt (synthetic data only; database tests use staging_schema). Locally, show that the pure-Python parts pass (the static audit() scan and the EVENT_TYPES parametrization), and that the database tests fail only on the staging_schema message. Print RED TEST (intentional) if you stop here.
- Add the authoritative EVENT_TYPES list and fix any missing audit() call or leaking route the tests reveal. If RLS, policies, grants or roles need changing, stop, set blocked with a reason, and tell the founder a gate-change PR is needed.
- Verify with CLAUDE.md's test command; commit; open the step PR with gh (status in_progress).
After merge: the staging workflow runs job "gate STEP-30" on main. Done PR: one commit on top of main holding only docs/build/evidence/STEP-30.md (command, exit_code 0, count N passed and run_id from that green staging run, date) and the status set to "done"; run python tools/check_evidence.py validate --step STEP-30, show the output, and open it with gh. Show every command and its output; never claim success.
Out of scope: new features, audit retention (D9), RLS changes (gate-change PR only).
Use a subagent to review the diff against this step file and report only gaps that affect correctness or the stated acceptance criteria.
```
