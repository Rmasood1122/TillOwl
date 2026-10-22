# STEP-27 Console: notice records, acknowledgment entry and mapping, support-access grant

Track: build. Lane: console. Gate kind: ci_fixture. Size: M.
Depends on: STEP-10 owner sign-in with TOTP two-factor. Done requires: none.
Blocks: STEP-30 audit coverage, STEP-31 Square event ingestion, STEP-32 roster-read job and acknowledgment mapping.
Sources: Slide 6–7 (CON; B1, B2, B6), Slide 10–11 (V1, V2, V6), Slide 15–16 (EMP: login_id, Square team member, display name), Slide 17–18 (NOT, ACK, AUD; Q2–Q5: `staff_notice.tenant_id`, `acknowledgment.notice_version`, `acknowledgment.login_id`), Slide 21 (staff notice control, notice workflow 1–5, "who sees what"), Slide 29 (RK9, TD5), Slide 30 (T16), ADR-006; BUILD_PLAN §1 (T16 = paper), design choices 13, 14, 16, 33; STEP-02 code `support_access_permission_approved`.

## Outcome
Console slices in `tillowl/console/`, on synthetic data only. Deploying them to staging and production comes later (production in STEP-33).
- `notices.py`: the owner records each `staff_notice` version (an increasing version number, the text, and `posted_at` for workflow step 4). Versions are immutable: a correction is a new version.
- Acknowledgment entry (paper T16):
  - each `acknowledgment` row holds the notice version, `login_id` (empty until mapped), `signed_at`, `method` (`paper`), and who entered it;
  - mapping sets or corrects `login_id` to an Employee login of the same tenant. Each mapping is its own audit row, holding the old and new login codes;
  - Q4: one acknowledgment per login per notice version.
- `acknowledged_logins(conn, tenant_id)` returns the logins with a mapped acknowledgment of the tenant's current notice version. It is the single reader that STEP-31, 35 and 36 use for design choices 15 and 16. That a new notice version needs new acknowledgments is a design choice proposed here; counsel's T17a answer governs.
- `support.py`: the owner grants support access in the console. The grant is time-boxed: an explicit `expires_at`, at most `SUPPORT_GRANT_MAX_HOURS` (config; the value is TBD — not in sources, and follows the support-access permission counsel approved in STEP-02 and the owner signed in STEP-06). It is revocable at any moment and lives in the `support_access_grant` table.
- The founder signs in as a support user (`support_user` table, STEP-08), enrolled once per environment by `python -m tillowl.jobs.provision_support_user`, which this step builds (prints `count: 1 rows` and sends the single-use TOTP enrollment link to the founder's address from the secret store). It uses STEP-10's TOTP, belongs to no tenant, and can act on a tenant only under that tenant's active grant. Under a grant it passes the console's access check for two actions only: `acks.write` (entering and mapping acknowledgments) and `shift_windows.write` (STEP-28). It never sees flags, digests or CSV exports (design choice proposed here, Slide 21 "who sees what"). Every request it makes writes an audit row naming the grant.
- Display names: they appear only in the console's mapping screen. They are never written to audit rows, application logs, job output or anything sent to a vendor; audit rows carry ids and login codes.
- Staff see nothing: there are no staff accounts, and no route serves a notice, acknowledgment or anything else without an owner session, or a support session under an active grant.

## Acceptance criteria
1. `test_notice_versions.py`: for any sequence of notice records, versions strictly increase per tenant. No route or function updates or deletes a recorded version. Each record and each `posted_at` entry writes exactly one audit row (`notice_recorded`, `notice_posted`) through `audit()`.
2. `test_ack_entry_mapping.py`:
   - Entry needs an existing notice version of the same tenant and a `signed_at` not in the future. A second acknowledgment for the same login and version is refused.
   - A mapping to another tenant's login fails, under RLS and by foreign key.
   - For a generated set of logins, acknowledgments and versions, `acknowledged_logins` returns exactly the logins with a mapped acknowledgment of the current version. An unmapped acknowledgment, or one on an older version, never makes a login count.
   - Every entry and mapping writes one audit row (`ack_entered`, `ack_mapped`). With placeholder display names such as `DN-L07` in the login rows, no audit row and no captured log line contains a display name.
3. `test_support_access_grant.py`:
   - With an injectable clock and generated grant windows, a support request at time t is allowed if and only if `created_at ≤ t < expires_at` and the grant was not revoked before t.
   - Every other support request gets 403 and an `access_denied` audit row. Revoking takes effect on the next request.
   - Every allowed support action writes an audit row with the grant id. Under an active grant, the access check passes only `acks.write` and `shift_windows.write`. A support user reaching a flag, digest or export route still gets 403.
   - A grant longer than `SUPPORT_GRANT_MAX_HOURS` is refused. Creating and revoking a grant each write an audit row (actor: owner).
   - Every console route, requested without a session, redirects to owner sign-in and returns no tenant data. No user row exists for any staff login.
4. Tests run on `fresh_db`, connected as the application role, never as the superuser, so RLS applies. Data is synthetic only: login codes like `L07`, counts like 9.
5. If `support_access_grant` is missing from STEP-08's schema, its RLS migration needs a gate-change PR the founder approves before this step's PR (design choice 33). Stop and say so; don't add the policy in this PR.

## Out of scope
The roster read and the display names it brings in (STEP-32). Entering the real paper acknowledgments (STEP-33, on production). Shift-window screens (STEP-28). Console signing by staff (T16 is paper). Deploying to staging or production.

## Gate
`pytest -c pytest.ini --rootdir=. tests/gates/step_27`, exact, from `docs/build/status/STEP-27.json`; the gate files are in `docs/build/gates/STEP-27.txt`. `docs/build/evidence/STEP-27.md` holds one block: `command:` (the gate), `exit_code: 0`, `count: N passed`, `run_id:` (the green `ci` push run on main for the evidence commit's parent), `date:`.

## If the gate fails
Revert to the last green commit. Set the status to `blocked` with a `blocked_reason` that holds no names or values (for example `grant_expiry_not_enforced`). After two failed attempts, restart in a fresh session with a narrower prompt.

## Prompt (paste into a fresh Claude Code session)
```text
You are running STEP-27 "Console: notice records, acknowledgment entry and support access" for TillOwl. Follow @CLAUDE.md throughout.
Start:
1. git fetch && git rebase origin/main
2. Confirm STEP-10 is "done" in docs/build/status/STEP-10.json; if not, stop and say so. Read git log -5.
3. Run CLAUDE.md's setup command.
4. Read @docs/build/steps/STEP-27-console-notices-acks.md, @docs/build/BUILD_PLAN.md §1, §7 and §11, the STEP-10 sign-in code in @tillowl/console/, @tillowl/audit.py, the schema in @migrations/, and Slides 6, 7, 16, 17, 18, 21, 29, 30 in @docs/architecture-pack-part1.md and @docs/architecture-pack-part2.md.
Work, test first:
- Set docs/build/status/STEP-27.json status to "in_progress".
- Check that the support_access_grant table and its RLS policy exist; if not, stop, set blocked_reason "support_access_grant_schema_missing", and tell the founder a gate-change PR is needed.
- Write the gate files exactly as listed in docs/build/gates/STEP-27.txt, with synthetic data built in the tests (login codes like L07, placeholder display names like DN-L07). Run them: they fail (print RED TEST (intentional) if you stop here).
- Implement notices.py, the acknowledgment entry and mapping screens, acknowledged_logins, support.py and the support sign-in to the acceptance criteria.
- Verify with CLAUDE.md's test command and with: PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -c pytest.ini --rootdir=. tests/gates/step_27. Commit; open the step PR with gh (status in_progress). It merges when CI is green.
Done PR: one commit on top of main holding only docs/build/evidence/STEP-27.md and the status set to "done". The run_id is the green "ci" push run on main for that commit's parent, and count: N passed comes from that run (gh run view <id> --log or the JUnit summary). Run python tools/check_evidence.py validate --step STEP-27, show the output, and open it with gh. Show every command and its output; never claim success.
Out of scope: roster read (STEP-32), real acknowledgments (STEP-33), shift windows (STEP-28), staff signing, deployment.
Use a subagent to review the diff against this step file and report only gaps that affect correctness or the stated acceptance criteria.
```
