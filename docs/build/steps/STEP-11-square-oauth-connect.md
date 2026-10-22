# STEP-11 Square OAuth connect (authorize, exchange, refresh, encrypted storage, scenario 4)

Track: build. Lane: connector. Gate kind: ci_staging. Size: M.
Depends on: STEP-01 Square-sandbox spike, STEP-09 staging deploy, STEP-10 owner sign-in with TOTP. Done requires: none. If STEP-01's findings say `sandbox_oauth_flow: NO`, D6 must be recorded in BUILD_PLAN §12 before this step starts.
Blocks: STEP-12 sandbox consent, STEP-13 production environment, STEP-19 live-spike code, STEP-20 live spike, STEP-26 digest delivery, STEP-31 ingestion.
Sources: Slide 3 (T1, P3), Slides 6–7 (B3, B4, B6, B7), Slides 10–11 (V3, V4, V6), Slide 13 (flow step 1), Slides 15–16 (OAU, R1), Slides 19–20 (I1), Slide 21 (encrypted OAuth tokens, owner-only access), Slide 24 (scenario 4), Slide 29 (RK8), ADR-003; BUILD_PLAN §7, design choices 4, 5, 14; D6.

## Outcome
The Square Connector's real auth code, not throwaway code:
- `tillowl/square/oauth.py`: `authorize_url()`, `handle_callback()`, `exchange_code()`, `refresh()`, `revoke()` (STEP-16 and STEP-22 reuse it) and `get_valid_token()` (STEP-31's nightly pull calls it first, Slide 13 step 1).
- `tillowl/crypto.py`: AES-256-GCM with the key from `TILLOWL_AES_KEY` in the host's secret store.
- Console routes `/oauth/square/start` and `/oauth/square/callback` (path held once in `tillowl/config.py` as `SQUARE_REDIRECT_PATH`), both behind STEP-10's owner sign-in.
- Table `oauth_connection` (one per tenant, R1): `merchant_id`, encrypted access and refresh tokens, `expires_at`, `refreshed_at`, `scopes`, `status` (`active`, `reconnect_needed`, `revoked`), `reconnect_flagged_at`. Add a migration only for columns STEP-08 lacks; it touches no RLS, policy, grant or role (design choice 33).
- Jobs `refresh_tokens` and `oauth_status` (STEP-12 runs both).
- The reconnect flag that STEP-26 turns into one reconnect text.

## Acceptance criteria
1. **Authorize.** `/oauth/square/start` serves only a signed-in owner. It redirects to `<host>/oauth2/authorize`:
   - The host is `https://connect.squareupsandbox.com` on staging and `https://connect.squareup.com` on production (Square docs, unverified candidates: [OAuth overview](https://developer.squareup.com/docs/oauth-api/overview)); any other host is refused.
   - The scope list is `SQUARE_SCOPES` in `tillowl/config.py`, and it must equal the `scope:` lines in `docs/build/findings/square-sandbox.md`, including the roster-read scope at first connect (design choice 14). A test fails if they drift.
   - `state` is at least 32 random bytes. It is stored only as its SHA-256, bound to the owner's session and tenant, single-use, and expires after 10 minutes (design choice). Square's docs say to verify `state` against the CSRF token you generated ([move to production](https://developer.squareup.com/docs/oauth-api/movetoprod), unverified candidate).
2. **Callback.** For every request, the code is exchanged only if all of these hold: an owner is signed in, and `state` matches an unused, unexpired state of the same session and tenant. Otherwise:
   - the response is 400;
   - no Square call is made and nothing is stored;
   - an `oauth_state_rejected` audit row is written.
   An `error=access_denied` callback shows a plain failure page, stores nothing and writes `oauth_denied`. A good callback hands the code to `oauth.py` (B3), exchanges it (B4), and upserts the tenant's single `oauth_connection`. Reconnecting replaces the tokens and clears `reconnect_needed`; each outcome is audit-logged.
3. **Encryption.** `crypto.py` uses AES-256-GCM with a fresh 96-bit nonce per call, and associated data binding `tenant_id` and the column name. The key is 32 bytes from `TILLOWL_AES_KEY` only. A missing or wrong-length key stops the process at startup. For every token string in the fixture and in generated cases:
   - decrypt(encrypt(x)) == x;
   - two encryptions differ;
   - a ciphertext moved to another tenant's row or column fails to decrypt;
   - no database column, audit row, log line or exception text holds the plaintext token or the key (`test_token_encryption.py` scans captured logs and every column).
4. **Refresh.** `python -m tillowl.jobs.refresh_tokens --env staging|production [--force]` refreshes every `active` connection whose `refreshed_at` is older than 6 days, or every active one with `--force`. Under a nightly schedule no token is ever older than 7 days. A simulated 60-night clock in `test_token_refresh.py` proves this for every start offset. The job prints `count: N refreshes`, `count: N connections`, `date:` and `exit_code:`. Any failed connection makes it exit 1, so Render's cron-failure email reaches the founder.
5. **Scenario 4** (`test_scenario4_refresh_failure.py`, on the staging schema):
   - A token 29 days old (near its 30-day expiry, Slide 3 T1) is refreshed on the next run.
   - A failed refresh (the fixture's 401 and repeated 5xx cases, after 2 in-run retries, design choice) sets `reconnect_needed` and `reconnect_flagged_at` once. Later failing nights leave `reconnect_flagged_at` unchanged, so STEP-26 sends one text. Each failure writes an audit row.
   - `get_valid_token()` never returns an expired token, and no night finds an expired token without the flag already set. So the owner hears the same night, and after reconnecting the next nightly run proceeds: no gap longer than one night (Slide 24).
6. **Status.** `python -m tillowl.jobs.oauth_status --env staging --expect-connections N` prints `count: N connections` and `count: N scopes`. It exits 0 only if the active count equals N and every active connection decrypts with the current key, was refreshed within 7 days, and holds exactly `SQUARE_SCOPES`.
7. **Read-only and test-only.**
   - `oauth.py` calls Square only at the authorize, token and revoke endpoints, with a timeout. No other Square write path exists (P3).
   - Gate tests replace Square with `httpx.MockTransport` built from `fixtures/square_oauth_responses.json`. Its response shapes are copied from Square's reference pages, cited in a `_source` key, with fake token strings only. A guard fails any real request to a Square host. CI never touches the friend's account or any real seller.
8. **Deployed route.** Against `STAGING_URL`, an unsigned-in GET of the callback is sent to sign-in and never exchanges a code (`test_oauth_connect.py`).

## Out of scope
Any consent click (STEP-12), production Square (STEP-16), reading orders or the roster (STEP-19, 31, 32), the reconnect text itself (STEP-26), personal access tokens.

## Gate
`pytest -c pytest.ini --rootdir=. tests/gates/step_11` (exact, from `docs/build/status/STEP-11.json`). Gate files: `docs/build/gates/STEP-11.txt` (four tests and `fixtures/square_oauth_responses.json`). It runs as job `gate STEP-11` in the `staging` workflow on `main`, against a per-run schema.

`docs/build/evidence/STEP-11.md` holds the command, `exit_code: 0`, `count: N passed`, `run_id:` of that green staging run, and `date:`.

## If the gate fails
Revert to the last green commit. Set `blocked` with a `blocked_reason` (no tokens, keys, names or values). After two failed attempts, restart in a fresh session with a narrower prompt. A red staging job blocks only this step. Never point a test at a real Square seller to make it pass.

## Prompt (paste into a fresh Claude Code session)
```text
You are running STEP-11 "Square OAuth connect" for TillOwl. Follow @CLAUDE.md throughout.
Start:
1. git fetch && git rebase origin/main
2. Confirm STEP-01, STEP-09 and STEP-10 are "done" in docs/build/status/ (stop and say which if not). If @docs/build/findings/square-sandbox.md says sandbox_oauth_flow: NO, confirm D6 is recorded in BUILD_PLAN §12; stop if not. Read git log -5.
3. Run CLAUDE.md's setup command.
4. Read @docs/build/steps/STEP-11-square-oauth-connect.md, @docs/build/findings/square-sandbox.md, BUILD_PLAN §7, and Slides 3, 6, 7, 10, 11, 13, 15, 16, 19, 20, 21, 24, 25, 29 in @docs/architecture-pack-part1.md and @docs/architecture-pack-part2.md.
Work, test first:
- Set docs/build/status/STEP-11.json status to "in_progress".
- Write the files listed in docs/build/gates/STEP-11.txt, exactly those. Use WebFetch on Square's OAuth reference pages for the response shapes in the fixture, and cite each URL in its _source key. The tests use the staging_schema fixture; run what can run locally and show that they fail (RED TEST (intentional) if you stop here).
- Implement tillowl/square/oauth.py, tillowl/crypto.py, the two console routes, the refresh_tokens and oauth_status jobs, and any migration for missing oauth_connection columns (no RLS, policy, grant or role changes). Meet every acceptance criterion for all valid inputs, not only the fixture.
- Run CLAUDE.md's test command and show the output. Commit; open the step PR with gh (status in_progress).
Done PR (after the step PR merges and the staging workflow's job "gate STEP-11" is green on main): one commit on top of main with only docs/build/evidence/STEP-11.md (the gate command, exit_code: 0, count: N passed and run_id from that staging run, date) and status "done". Run python tools/check_evidence.py validate --step STEP-11 and show the output; never claim success without it.
Out of scope: consent clicks, production Square, orders, roster, reconnect text, personal tokens.
Use a subagent to review the diff against this step file and report only gaps that affect correctness or the stated acceptance criteria.
```
