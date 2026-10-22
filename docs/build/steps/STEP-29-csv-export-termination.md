# STEP-29 CSV export of flagged events and the termination path

Track: build. Lane: console. Gate kind: ci_fixture. Size: M.
Depends on: STEP-10 owner sign-in with TOTP two-factor. Done requires: none.
Blocks: STEP-30 audit coverage.
Sources: Slide 6–7 (CON: "30-day CSV export"; B1), Slide 17–18 (EXJ "PostgreSQL table + file", "all flagged events; kept 30 days after end"; Q10, Q11; the data rules: "After termination or shutdown: CSV of all flagged events for 30 days, then deletion per contract", "Retention periods beyond that: TBD"), Slide 21 (exit rights; "who sees what": the owner gets the CSV export), Slide 25 (ADR-005: "detail comes as a CSV export"), Slide 29 (RK7), Slide 30 (T15); BUILD_PLAN §9, design choice 28; D9.

## Outcome
- `tillowl/console/export.py`, run on the owner's request in the console:
  - streams a CSV of every `flag` row of the owner's tenant, one row per flag: flag id, business day, shift name, login code (empty when the flag names none), metric, value, baseline range, evidence (check ids and times), and created_at;
  - login codes only, never display names. Any cell starting with `=`, `+`, `-` or `@` is prefixed with `'`, so a spreadsheet won't run it as a formula;
  - the file is streamed to the owner's browser and not kept on the host (design choice proposed here, for Slide 18's "table + file");
  - each export writes one `csv_export` row (requested_at, row count, the SHA-256 of the bytes sent) and one `export` audit row whose target is that row (Q11).
  Only the owner may export; support access never can (STEP-27).
- `tillowl/console/termination.py`:
  - `record_termination(conn, tenant_id, reason, terminated_on)`, with reason `owner_cancelled | term_ended | vendor_shutdown` (Slide 21: "the same if we shut down", so `vendor_shutdown` runs it for every active tenant). It:
    - sets the tenant `terminated`;
    - revokes the Square OAuth connection through an injected `revoke` callable. That is STEP-11's revoke when wired up (STEP-29 doesn't depend on STEP-11), and a stub in the tests;
    - makes every job skip the tenant;
    - opens a 30-day export window, counted in local calendar days of the restaurant's time zone. In that window the owner can still sign in, and can reach only the flag CSV and a CSV of the notice versions and acknowledgments (login codes, version, signed_at, method; design choice proposed here, since the employer keeps those records).
  - `delete_tenant_data(conn, tenant_id, now)`:
    - refuses before the window ends;
    - after it ends, deletes every row of the tenant in every table that carries `tenant_id`, except `audit_log`, and reduces the tenant row to its id and status `deleted`;
    - checks the result with STEP-19's `verify_deleted` tenant-scope check;
    - writes audit rows `tenant_terminated` and `tenant_deleted`, plus `backup_expires` (the deletion date + the PITR length from config: 7 days under design choice 28, an unverified candidate).
  - `tillowl/jobs/terminate_tenant.py --tenant <own|pilot> --reason owner_cancelled|term_ended|vendor_shutdown [--delete]` is the founder-launched production command: without `--delete` it records the termination and starts the 30-day export window; with `--delete` (refused before the window ends) it deletes and verifies. It prints only `count:`, `backup_expires:` and `exit_code:` lines.
  - Audit rows are never deleted here. The insert-only audit role can't delete, and how long they're kept is D9.

## Acceptance criteria
1. `test_csv_export.py`, for generated flag sets across two tenants:
   - tenant A's export holds exactly A's flags (row count = A's `flag` rows) and none of B's, under RLS as the application role;
   - every cell round-trips through Python's `csv` module;
   - no display name from the Employee login rows appears (placeholders like `DN-L07` in the fixture);
   - every generated cell that starts with `=`, `+`, `-` or `@` comes out prefixed;
   - each export writes exactly one `csv_export` row and one `export` audit row, and the recorded SHA-256 equals the hash of the bytes the client received;
   - a support session, even under an active grant, gets 403 and an `access_denied` audit row.
2. `test_termination_path.py`, with an injectable clock:
   - Revoke and access. `record_termination` calls the stubbed Square revoke exactly once. Before the window ends, the owner can download both CSVs, and every other tenant route returns no data.
   - Too early. `delete_tenant_data` refuses on every day before the window ends and deletes nothing.
   - Deletion. On or after the end, every tenant table found through `information_schema` (all tables with a `tenant_id` column except `audit_log`) has 0 rows for the tenant. Its audit rows are all still there, plus the deletion rows. Tenant B's row counts are unchanged.
   - Shutdown. `vendor_shutdown` terminates every active tenant.
   - A window that ends across a DST change is counted in local days.
3. Tests run on `fresh_db` as the application role, with synthetic data only, and make no network calls (the Square revoke is stubbed).

## Out of scope
- Running the deletion on production after a real termination. BUILD_PLAN §7 names no job for it; this is reported to the founder as a gap.
- The NO-GO exit (STEP-22's `exit_tenant`, which may reuse `delete_tenant_data`).
- Audit-row retention (D9). Billing and cancel (STEP-42). Any retention beyond the 30-day export (T15).

## Gate
`pytest -c pytest.ini --rootdir=. tests/gates/step_29`, exact, from `docs/build/status/STEP-29.json`; the gate files are in `docs/build/gates/STEP-29.txt`. `docs/build/evidence/STEP-29.md` holds one block: `command:` (the gate), `exit_code: 0`, `count: N passed`, `run_id:` (the green `ci` push run on main for the evidence commit's parent), `date:`.

## If the gate fails
Revert to the last green commit. Set the status to `blocked` with a `blocked_reason` that holds no names or values (for example `rows_remaining_after_delete`). After two failed attempts, restart in a fresh session with a narrower prompt. Never weaken the "0 rows remaining" check to make the gate pass.

## Prompt (paste into a fresh Claude Code session)
```text
You are running STEP-29 "CSV export and termination path" for TillOwl. Follow @CLAUDE.md throughout.
Start:
1. git fetch && git rebase origin/main
2. Confirm STEP-10 is "done" in docs/build/status/STEP-10.json; if not, stop and say so. Read git log -5.
3. Run CLAUDE.md's setup command.
4. Read @docs/build/steps/STEP-29-csv-export-termination.md, @docs/build/BUILD_PLAN.md §7, §9, §11 and §12 (D9), @tillowl/audit.py, @tillowl/console/, the schema in @migrations/, and Slides 6, 7, 17, 18, 21, 25, 29, 30 in @docs/architecture-pack-part1.md and @docs/architecture-pack-part2.md. If STEP-19's verify_deleted isn't merged yet, write the same 0-rows check inside termination.py and note it in the PR.
Work, test first:
- Set docs/build/status/STEP-29.json status to "in_progress".
- Write the gate files exactly as listed in docs/build/gates/STEP-29.txt, with synthetic flags built in the tests (login codes like L07, shift "Dinner", counts like 9). Run them: they fail (print RED TEST (intentional) if you stop here).
- Implement export.py and termination.py to the acceptance criteria. No CSV file is written to disk on the host. If STEP-11's revoke exists in tillowl/square/oauth.py, wire it up as the default revoke callable; if not, leave the parameter required.
- Verify with CLAUDE.md's test command and with: PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -c pytest.ini --rootdir=. tests/gates/step_29. Commit; open the step PR with gh (status in_progress). It merges when CI is green.
Done PR: one commit on top of main holding only docs/build/evidence/STEP-29.md and the status set to "done". The run_id is the green "ci" push run on main for that commit's parent, and count: N passed comes from that run. Run python tools/check_evidence.py validate --step STEP-29, show the output, and open it with gh. Show every command and its output; never claim success.
Out of scope: a production termination job (gap reported), the NO-GO exit (STEP-22), audit retention (D9), billing (STEP-42).
Use a subagent to review the diff against this step file and report only gaps that affect correctness or the stated acceptance criteria.
```
