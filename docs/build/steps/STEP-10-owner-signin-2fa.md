# STEP-10 Owner sign-in with TOTP two-factor (no staff accounts)

Track: build. Lane: console. Gate kind: ci_fixture. Size: M.
Depends on: STEP-08 Repo skeleton. Done requires: none.
Blocks: STEP-11 Square OAuth connect, STEP-27 console notices and acknowledgments, STEP-28 shift windows, STEP-29 CSV export, STEP-42 billing.
Sources: Slide 21 (owner-only access: "One owner sign-in per restaurant with two-factor (design choice); no staff accounts"; audit log of every sign-in; who sees what), Slides 17–18 (Owner user "the only sign-in", Q1, Q5), Slide 24 (scenario 3: "staff have no accounts; the attempt goes in the audit log"), Slides 22–23 (D1 signs in over HTTPS), ADR-006; BUILD_PLAN §7, design choices 1, 4, 5.

## Outcome
- **The sign-in flow** lives in `tillowl/console/app.py` (FastAPI, server-rendered HTML) and `tillowl/console/auth.py`:
  - `create_owner_invite(conn, tenant_id, email)` returns a one-time invite token (only its hash is stored, with an expiry). It is refused for a tenant that already has an enrolled owner. STEP-14 and STEP-17's `provision_tenant` call it.
  - `/invite/{token}` sets a password, then enrolls TOTP with `pyotp` (design choice 4). It shows the `otpauth://` URI and the base32 secret, and is confirmed by one valid code. It then shows 10 single-use recovery codes, once.
  - `/signin` takes email and password. `/signin/2fa` then takes a TOTP code, or one recovery code instead, and starts a session. `/signout` ends it.
  - `PUBLIC_PATHS = {"/healthz", "/signin", "/signin/2fa", "/invite/{token}"}`. Every other route needs an owner session and runs inside that owner's tenant (`tenant_tx` with the session's tenant).
  - The email lookup before a tenant is known runs as `tillowl_signin` (STEP-08).
- **`tillowl/crypto.py`.** AES-256-GCM `encrypt`/`decrypt`, with the key from `TILLOWL_AES_KEY` in the host's secret store; tests generate a key (design choice 5). TOTP secrets are stored only encrypted. STEP-11 reuses this module for OAuth tokens.
- **Stored secrets.** Passwords are hashed with the standard library's `hashlib.scrypt` and a per-owner salt (design choice proposed here). Recovery codes and session tokens are stored only as SHA-256 hashes.
- **Sessions** are server-side rows in `owner_session`. The cookie is HttpOnly, Secure and SameSite=Lax. Sessions expire after lengths set in config. Every POST form carries a CSRF token.
- **`migrations/0004_owner_auth.sql`** adds the auth columns to `owner_user` and holds nothing else: no tables, grants, roles or policies. Those exist from STEP-08.
- **Audit actions** added to `AUDIT_ACTIONS`: `signin_success`, `signin_failed`, `signin_locked`, `signin_denied`, `totp_enrolled`, `recovery_code_used`, `signout`, `access_denied`.

## Acceptance criteria
1. **`tests/gates/step_10/test_owner_signin_totp.py`**, given an owner invited on `fresh_db` (the TOTP clock is injected, so tests never sleep):
   - Enrollment works. Sign-in needs both the right password and a current TOTP code.
   - Sign-in is refused for a wrong password, a wrong code, a code outside one step either side, or a code already used.
   - Each recovery code works exactly once, and the codes appear in exactly one HTTP response.
   - No column of `owner_user`, `owner_recovery_code` or `owner_session` holds a plaintext password, TOTP secret, recovery code or session token.
   - After 5 failed attempts for one owner within 15 minutes, sign-in is refused for 15 minutes even with the right credentials. These numbers are a design choice proposed here.
   - An expired or revoked session redirects to `/signin`. The cookie flags are set.
2. **`test_no_staff_accounts.py`**:
   - A second `owner_user` row for the same tenant fails (Q1).
   - No table other than `owner_user` holds a password, TOTP or session-credential column.
   - An invite token works once, and an invite for a tenant with an enrolled owner is refused.
   - For every route registered on the app when the test runs, an unauthenticated request to a path outside `PUBLIC_PATHS` gets a redirect to `/signin` (or 401/403) and no data. This holds for routes later steps add.
   - `PUBLIC_PATHS` is exactly the four paths above.
   - Signing in with any `login` code (for example `L07`) or any email that isn't an owner's fails.
3. **`test_signin_audit.py`**:
   - Each of the eight actions above writes exactly one `audit_log` row through `audit()`. `access_denied` is written for an unauthenticated request to a protected path.
   - Rows for a known owner carry the `tenant_id` and the target `owner_user:<uuid>`. Rows for an unknown email carry a NULL `tenant_id` and no target.
   - No audit column holds the submitted email, password, code or IP address; the test scans every row as text.
4. Two-factor never depends on SMS or 10DLC (design choice 4). No staff route, table or role exists. A signed-in owner's requests run under RLS for their own tenant only; scenario 3 itself is tested in STEP-30.

## Out of scope
- The OAuth callback (STEP-11), console screens (STEP-27–29), provisioning jobs (STEP-14, 17).
- `/healthz` (STEP-09). If STEP-09 hasn't merged, add only the sign-in routes and rebase later.
- Account recovery beyond recovery codes (TBD — not in sources; raise it as a founder decision).
- Password reset by email.

## Gate
`pytest -c pytest.ini --rootdir=. tests/gates/step_10` (exact, from `docs/build/status/STEP-10.json`). Gate files: the three tests in `docs/build/gates/STEP-10.txt`; no other file goes under `tests/gates/step_10/`.

`docs/build/evidence/STEP-10.md` holds the pytest block: `exit_code: 0`, `count: N passed` and `run_id` from the green `ci` push run on main for the evidence commit's parent, and `date:`.

## If the gate fails
Revert to the last green commit. Set the status to `blocked` with a `blocked_reason` (no names, emails or secrets). After two failed attempts, restart in a fresh session with a narrower prompt. If the fix needs a new table, grant or policy, stop: that is a gate-change PR on STEP-08's migrations (design choice 33).

## Prompt (paste into a fresh Claude Code session)
```text
You are running STEP-10 "Owner sign-in with TOTP two-factor" for TillOwl. Follow @CLAUDE.md throughout.
Start: git fetch && git rebase origin/main; confirm STEP-08 is "done" in docs/build/status/STEP-08.json (stop and say so if not); read git log -5; run CLAUDE.md's setup command; read @docs/build/steps/STEP-10-owner-signin-2fa.md, @migrations/0001_schema.sql, @migrations/0003_audit_role.sql, @tillowl/audit.py, @tillowl/db.py, and Slides 17, 18, 21, 22, 24 in @docs/architecture-pack-part2.md.
Work, test first:
- Set docs/build/status/STEP-10.json status to "in_progress".
- Write the three gate tests named in docs/build/gates/STEP-10.txt, using fresh_db and FastAPI's TestClient with synthetic owners only. Run them; they fail. If you stop here, print RED TEST (intentional).
- Implement auth.py, the routes, crypto.py and migrations/0004_owner_auth.sql to the acceptance criteria. Add pyotp, cryptography and python-multipart to pyproject.toml (fastapi and httpx too, if STEP-09 hasn't added them).
- Run CLAUDE.md's test command and show the command and its output; commit; open the step PR with gh (status in_progress). It merges when CI is green and a reviewer approves.
Done PR, after the step PR merges: one commit on top of main holding only docs/build/evidence/STEP-10.md and the status set to "done". Take run_id from the green ci push run on main for that commit's parent, and "count: N passed" from gh run view <id> --log; add the date. Run python tools/check_evidence.py validate --step STEP-10, show the command and its output, and open the PR. Never claim success without output.
Out of scope: OAuth, other console screens, provisioning, account recovery beyond recovery codes.
Use a subagent to review the diff against this step file and report only gaps that affect correctness or the stated acceptance criteria.
```
