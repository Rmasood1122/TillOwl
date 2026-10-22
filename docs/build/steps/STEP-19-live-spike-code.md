# STEP-19 Live-spike job code (square_live_report and verify_deleted)

Track: build. Lane: connector. Gate kind: ci_fixture. Size: M.
Depends on: STEP-11 Square OAuth connect. Done requires: none.
Blocks: STEP-20 Run the read-only live spike, STEP-30 Audit-log coverage and scenario 3.
Sources: Slide 3 (T2: voided orders come back CANCELED), Slides 15–16 (entities marked "verify on live account"), Slide 21 (encrypted tokens; least data), Slide 30 (V1–V8; "Each test result goes into the audit log"), ADR-004; BUILD_PLAN §7 (live-spike counts), design choices 5, 9, 10, 18, 19, 25; D7.

## Outcome
**`tillowl/square/live_report.py`** turns Square response pages into observations. It runs on the production host through the tenant's OAuth token, which only that process decrypts. It returns:
- `field:` lines: field name and type only, with `type=absent` for a mapped field that never came back;
- `count:` lines: `orders`, `cancelled_orders`, `comps`, `discounts`, `refunds`, `no_sale_opens`, `item_voids`, `logins_hashed`, plus `days` (days with orders) and `v_items`;
- `v_item:` lines: one per V1–V8, each RETURNED, NOT_RETURNED or PARTIAL. A sub-field that passes on its own gets its own RETURNED line, for example `v_item: V2.opened_by RETURNED`.

**One config map** decides which API call and fields test each V-item and sub-field: `tillowl/config.py` `V_ITEM_FIELDS`, copied from STEP-01's `field:` and `v_shape:` lines. No call site hard-codes a field.
**Logins** (design choice 9): login ids are HMAC-SHA256 hashed in memory with `TILLOWL_HMAC_KEY`; only the set's size is kept. No per-login rows or values are stored or printed.

**`tillowl/jobs/square_live_report.py --tenant own|pilot --check`** runs through STEP-08's `run_job` wrapper. It:
- reads the 30 business days ending yesterday, in the restaurant's time zone (design choice 18), and writes one `audit()` row per V-item result (code and result only);
- prints the lines above, then `oauth_connection: kept|revoked` per `SPIKE_OAUTH_AFTER` (D7, design choice 19), and when that is revoke it calls `revoke()` in `tillowl/square/oauth.py`;
- ends with `date: YYYY-MM-DD` then `exit_code: N`; with `--check` it exits 1 unless all 8 items have a result.

**Settings.** `SPIKE_OAUTH_AFTER` and `BACKUP_RETENTION_DAYS` are read by `tillowl/config.py` from the service environment, never hard-coded; an unset value exits 1 before any Square call or deletion check. `TILLOWL_HMAC_KEY` comes from the secret store.

**`tillowl/jobs/verify_deleted.py --tenant own|pilot --scope spike|tenant`** builds both scopes now (BUILD_PLAN §7). STEP-20 freezes it; STEP-22 reuses `--scope tenant`; STEP-29's deletion meets the same definition.
- `--scope tenant`: zero rows in every table that carries `tenant_id`, except all `audit_log` rows (undeletable; retention is D9) and the `tenant` row reduced to its id and status.
- `--scope spike`: zero rows written by the spike run, i.e. zero tenant rows in every `tenant_id` table outside config `NON_SQUARE_TABLES` (tenant, owner sign-in, OAuth connection, `audit_log`).
- It is read-only except one audit row recording the deletion date, and prints `count: N rows_remaining`, `backup_expires: <deletion date + BACKUP_RETENTION_DAYS>`, `date:`, `exit_code:`.

## Acceptance criteria
1. **Counts only, no values.** Given `fixtures/square_responses_full.json` and `fixtures/square_responses_sparse.json` (synthetic), `pytest tests/gates/step_19/test_live_report_counts_only.py` passes, and so does each set from a seeded generator of the same shape. Every stdout line matches the evidence grammar, and output ends `date:` then `exit_code:`.
   - No string leaf and no number leaf from the fixtures appears in stdout, in audit rows or in any database table. That covers names, ids, amounts and notes. Fixture numbers are chosen so none can equal a printed count.
   - Each count equals the number of matching synthetic records.
2. **Logins hashed in memory.** `test_hmac_logins.py`: `logins_hashed` equals the number of distinct login ids in every generated set; a different key gives the same count but different hashes; no hash and no raw id reaches stdout, audit rows or the database; a missing `TILLOWL_HMAC_KEY` exits 1 before any Square call (there is no default key).
3. **V-item results.** `test_v_item_results.py`:
   - the full fixture gives all eight items RETURNED;
   - the sparse fixture gives the expected NOT_RETURNED, PARTIAL and sub-field RETURNED lines;
   - the rules: RETURNED when every mapped field is present on every relevant record; PARTIAL when present on some; NOT_RETURNED when present on none, or when there are zero relevant records (its `count: 0` shows why);
   - V8 is RETURNED only if orders reach into the oldest 7 days of the 30-day window;
   - each result writes exactly one audit row;
   - an API error on an item leaves it without a result, so `--check` exits 1 and prints no `v_item:` line for that item;
   - the job sends only read (GET or search) requests.
4. **Deletion check.** `test_verify_deleted.py`:
   - The table list comes from the database catalogue (every table with a `tenant_id` column), never a hard-coded list, so a new table can't be missed.
   - `--scope spike` and `--scope tenant` exit 0 exactly as defined in the Outcome. Under `tenant`, every `audit_log` row may remain, and a tenant row with any column besides id and status still set exits 1.
   - A seeded leftover row in any counted table exits 1 with its count. Other tenants' rows are never counted or touched.
   - It exits 1 if `BACKUP_RETENTION_DAYS` is unset or exceeds the 14-day cap in the owner's authorization.
   - `backup_expires` equals the deletion date plus `BACKUP_RETENTION_DAYS`, for every date tested, month ends included.

## V-item branches
None are built here: this step produces the results. STEP-20 records them in `docs/build/findings/square-fields.md`, and later steps read them only through `tillowl/config.py` `V_ITEMS`.

## Out of scope
Running against any live account (STEP-20); ingesting or storing events (STEP-31); the roster read (STEP-32); the decision (STEP-21); the exit job (STEP-22).

## Gate
`pytest -c pytest.ini --rootdir=. tests/gates/step_19` (exact, from `docs/build/status/STEP-19.json`). Gate files: the four tests and two fixtures in `docs/build/gates/STEP-19.txt`. `docs/build/evidence/STEP-19.md` holds `command:`, `exit_code: 0`, `count: N passed`, `date:`, and the `run_id:` of the green `ci` push run on main for the evidence commit's parent.

## If the gate fails
- Revert to the last green commit. Set `blocked` with a `blocked_reason` summarising the failing test. No values.
- After two failed attempts, restart in a fresh session with a narrower prompt.
- If `revoke()` doesn't exist yet, add it to `tillowl/square/oauth.py` with a mocked-Square test outside `tests/gates/` (for example `tests/test_oauth_revoke.py`). Never call a live account from tests.

## Prompt (paste into a fresh Claude Code session)
```text
You are running STEP-19 "Live-spike job code" for TillOwl. Follow @CLAUDE.md throughout.
Start:
1. git fetch && git rebase origin/main
2. Confirm STEP-11 is "done" in docs/build/status/STEP-11.json; if not, stop and say so. Read git log -5.
3. Run CLAUDE.md's setup command.
4. Read @docs/build/steps/STEP-19-live-spike-code.md, @docs/build/findings/square-sandbox.md, @docs/build/go-no-go-criteria.md, @tillowl/square/oauth.py, @tillowl/audit.py, @tillowl/business_day.py, and Slides 3, 15, 16, 21, 30 in @docs/architecture-pack-part1.md and @docs/architecture-pack-part2.md.
Body, test first:
5. Set docs/build/status/STEP-19.json status to "in_progress".
6. Build both synthetic fixtures in the shape of STEP-01's recorded fields. Use made-up values only: login codes like L07, no real names or amounts.
7. Write the four gate tests named in docs/build/gates/STEP-19.txt to acceptance criteria 1–4. Run them; they fail. Print RED TEST (intentional) if you stop here.
8. In tillowl/config.py add V_ITEM_FIELDS and NON_SQUARE_TABLES, and read SPIKE_OAUTH_AFTER and BACKUP_RETENTION_DAYS from the service environment (never hard-coded; TILLOWL_HMAC_KEY from the secret store). Then build tillowl/square/live_report.py, and tillowl/jobs/square_live_report.py and tillowl/jobs/verify_deleted.py (both scopes, as the Outcome defines them) on STEP-08's run_job wrapper.
9. Run the gate, PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -c pytest.ini --rootdir=. tests/gates/step_19, then CLAUDE.md's test command; show both outputs. Commit, then open the step PR with gh (status in_progress). It merges when CI is green.
Done PR: make one commit on top of main holding only docs/build/evidence/STEP-19.md and the status set to "done". run_id is the green ci push run on main for that commit's parent; count: N passed comes from that run (gh run view <id> --log, or its JUnit summary). Show the commands and their output; never claim success. Run python tools/check_evidence.py validate --step STEP-19, then open the PR with gh.
Out of scope: live accounts, ingestion, roster read, decision, exit job.
Use a subagent to review the diff against this step file and report only gaps that affect correctness or the stated acceptance criteria.
```
