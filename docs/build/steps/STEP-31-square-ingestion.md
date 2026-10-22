# STEP-31 Square event ingestion (scenario 1)

Track: build. Lane: connector. Gate kind: ci_staging. Size: M. Runs only if STEP-21 recorded GO.
Depends on: STEP-11 Square OAuth connect, STEP-21 go/no-go decision recorded (GO), STEP-27 console notices, acknowledgment entry and support access, STEP-28 console shift windows and digest settings. Done requires: none.
Blocks: STEP-34 30-day history pull, STEP-35 ratio rules and baselines, STEP-39 pass-line measurement.
Sources: Slide 3 (P3, P5, T1, T2), Slides 12–13 (flow steps 1–2: "refreshes the OAuth token if due, then pulls yesterday's orders, refunds and cash-drawer events"; "Normalized events: login, shift, time, type, amount"), Slides 15–16 (LOC, CHK, LIN, CXL, CMP, DSC, REF, NSE, MAC; R5, R7–R13), Slides 19–20 (Square data available and known gaps), Slide 21 (acknowledgment gate), Slide 22 ("A missed night is re-pulled the next night"), Slide 24 (scenario 1), Slide 29 (TD2, TD3), Slide 30 (V1–V7), ADR-003, ADR-004, ADR-006; BUILD_PLAN design choices 10, 15, 16, 18, 25; T17a code `pre_notice_history`.

## Outcome
- `tillowl/square/ingest.py`: `ingest_day(tenant, business_day)` pulls one restaurant business day through `tillowl/square/client.py` (read calls only), including orders in state CANCELED (counted only, no line items; T2), refunds, discounts, comps and cash-drawer events. It writes normalized rows into STEP-08's tables for Slide 16's entities (`check`, `cancelled_order`, `line_item`, `discount`, `comp`, `refund`, `no_sale`, `approval_code`). Every row carries `tenant_id`, `business_day`, `shift_id` (the owner-set window from STEP-28, or null outside every window), event time, type, amount where stored, and `login_id` (null when stripped). Rows are upserted on Square's ids, so re-pulling a day replaces it. Raw responses are never stored. Ingest never creates `login` rows; only STEP-32's roster read or the founder's typed entry does.
- `tillowl/jobs/nightly_pull.py` (`python -m tillowl.jobs.nightly_pull --env staging|production --tenant …`):
  - refreshes the token first when due, with STEP-11's `oauth.py`;
  - ingests every business day after `location.last_pulled_business_day` through yesterday, oldest first, at most 30 (design choice);
  - advances that marker only after a day commits;
  - prints only `count: N days`, `count: N orders`, `count: N events` and `exit_code: N`.
- The marker is one new column on `location`. Its migration creates no table, policy, grant or role, so it needs no gate-change PR (design choice 33).
- `tillowl/config.py` holds `V_ITEMS`, parsed from the `v_item:` lines of `docs/build/findings/square-fields.md` (PARTIAL becomes NOT_RETURNED; design choice 10), and `COUNSEL`, parsed from `docs/build/findings/counsel-t17a-answers.md`. Add them here if no earlier step did. They are the only readers of those files.
- `nightly_pull` refuses to run (exit 2, no Square call) unless it is listed in `TILLOWL_JOBS_ENABLED`. Production lists only `refresh_tokens` until STEP-43 (design choice 25).

## Acceptance criteria
1. **Business day and shift.** For every stored row, `business_day` is `tillowl/business_day.py`'s day for the event time in the location's time zone. `shift_id` is the owner-set window that contains that time, including windows that cross midnight (design choice 18). Rows outside every window keep `shift_id` null and still count in restaurant totals.
2. **Cancelled orders.** Each CANCELED order becomes exactly one `cancelled_order` row and is never also counted as a sale.
3. **Branches through `V_ITEMS` only** (`test_ingest_branches.py`).
   - Given `fixtures/square_orders_returned.json` with every item RETURNED, each field named under V-item branches is stored.
   - Given `fixtures/square_orders_not_returned.json` with every item NOT_RETURNED, and again with PARTIAL, none of those fields is stored. The counts of cancelled orders, discounts and refunds stay the same.
   - A static check fails if any module other than `tillowl/config.py` reads `square-fields.md` or compares a V-item status.
4. **Acknowledgment stripping** (`test_ack_stripping.py`; design choice 15). For every stored row whose `login_id` is not null, that login has an acknowledgment entered and mapped (STEP-27) at ingest time.
   - With `pre_notice_history: TOTALS_ONLY`, the acknowledgment is also dated on or before the row's `business_day`.
   - With `PER_LOGIN_ALLOWED`, an acknowledged login's rows from before its acknowledgment keep the login.
   - Stripping changes no restaurant total: row counts and amount sums are the same with and without acknowledgments.
   - The Square team-member id of an unacknowledged login is never written to the database, the logs or the audit log.
5. **Scenario 1** (`test_scenario1_missed_day.py`). The stub Square fails, or the job does not run, for business day D. The next run ingests D and D+1, each stored once. Re-running any day replaces it and never duplicates it, and the marker never skips a failed day. Every request the connector made is in `client.py`'s read-only allowlist, and no code path under `tillowl/square/` issues a write. So a platform outage has zero effect on orders and payments (P3, P5).
6. **Refresh failure.** A failed token refresh leaves the day unpulled and raises STEP-11's reconnect flag (scenario 4). The next successful run recovers the day.
7. **No names or values.** Given fixtures that contain names and amounts, the job's stdout and log records hold only evidence-grammar lines.
8. **Fixtures.** They use only field names recorded in `square-fields.md` (or STEP-01's `square-sandbox.md`), with synthetic values: logins like `L07`, windows like "Dinner". No real identifiers or spike samples.
9. **CI.** Each gate test uses a module-level `db` fixture that is `staging_schema` when `STAGING_DATABASE_URL` is set (the staging workflow) and `fresh_db` otherwise. Square is always stubbed, and CI never calls a real Square account.

## V-item branches
Store a field only if its item is RETURNED in `V_ITEMS`; otherwise don't store it. A sub-item that is RETURNED on its own, such as `V2.opened_by`, enables only its own field.
- **V1 (dollar amount on cancelled orders).** If V1 is RETURNED: store the `cancelled_order` amount. If NOT_RETURNED or PARTIAL: the amount stays null, cancelled orders are still counted, and the pass line uses the DPA's substitute measure.
- **V2 (login on cancelled orders).** If V2 is RETURNED: store the login (when acknowledged) on cancelled orders, so the digest can say "9 checks cancelled during shift Y (opened by login X)". The same opened-by field also tags ordinary checks (design choice; it feeds STEP-35's per-login net sales). If NOT_RETURNED or PARTIAL: `login_id` stays null on cancelled orders and checks, and the digest says "9 checks cancelled during shift Y".
- **V3 (item voids on paid checks).** If V3 is RETURNED: store item-void rows with time, shift and login. If NOT_RETURNED or PARTIAL: store nothing for them.
- **V4 (approving manager code).** If V4 is RETURNED: store the `approval_code` reference and its holder login (R5). If NOT_RETURNED or PARTIAL: store nothing.
- **V5 (comps).** If V5 is RETURNED: store `comp` rows (line item at $0.00, reason). If NOT_RETURNED or PARTIAL: store no comps.
- **V6 (no-sale drawer opens).** If V6 is RETURNED: store `no_sale` rows (opened_at, login, location). If NOT_RETURNED or PARTIAL: store nothing.
- **V7 (login on discounts and refunds).** If V7 is RETURNED: store the login on discount and refund rows. If NOT_RETURNED or PARTIAL: store discounts and refunds per shift window, with `login_id` null.

## Out of scope
The history pull job (STEP-34) and the roster read (STEP-32); ratios, baselines and flags (STEP-35 to 37) and digest wording (STEP-38); enabling `nightly_pull` in production (STEP-43); any write to Square.

## Gate
`pytest -c pytest.ini --rootdir=. tests/gates/step_31` (exact, from `docs/build/status/STEP-31.json`). The gate files are listed in `docs/build/gates/STEP-31.txt`: three tests and the two fixtures. `docs/build/evidence/STEP-31.md` holds one pytest block: `command:`, `exit_code: 0`, `count: N passed`, the `run_id:` of the green `staging` push run on main whose job `gate STEP-31` passed (gate files unchanged since), and `date:`.

## If the gate fails
Revert to the last green commit. Set the status to `blocked` with a `blocked_reason` (no names or values). After two failed attempts, restart in a fresh session with a narrower prompt. A red staging run blocks only this step. Never point a test at a real Square account to "check" it.

## Prompt (paste into a fresh Claude Code session)
```text
You are running STEP-31 "Square event ingestion (scenario 1)" for TillOwl. Follow @CLAUDE.md throughout.
Start:
1. git fetch && git rebase origin/main
2. Confirm STEP-11, STEP-21, STEP-27 and STEP-28 are "done" in docs/build/status/, and that STEP-21's "decision" is "GO". If not, stop and say which.
3. Read git log -5.
4. Run CLAUDE.md's setup command.
5. Read @docs/build/steps/STEP-31-square-ingestion.md, @docs/build/findings/square-fields.md, @docs/build/findings/counsel-t17a-answers.md, @docs/build/go-no-go-criteria.md, and Slides 3, 12, 13, 15, 16, 19, 20, 21, 22, 24 and 30 in @docs/architecture-pack-part1.md and @docs/architecture-pack-part2.md.
Work, test first:
- Set docs/build/status/STEP-31.json status to "in_progress".
- Write the three tests and two fixtures exactly as listed in docs/build/gates/STEP-31.txt, with the module-level db fixture from criterion 9.
- Run pytest -c pytest.ini --rootdir=. tests/gates/step_31 locally. It fails (print RED TEST (intentional) if you stop here).
- Implement config.py V_ITEMS/COUNSEL, ingest.py, the location marker migration and jobs/nightly_pull.py to the acceptance criteria. Use field names only from the findings files; never invent one.
- Re-run the gate locally and then CLAUDE.md's test command. Show both outputs. Commit, then open the step PR with gh (status in_progress).
Done PR (after merge): wait for the staging workflow's job "gate STEP-31" on main to go green. Then make one commit on top of main holding only docs/build/evidence/STEP-31.md (command, exit_code: 0, count: N passed, run_id of that staging run, date) and the status set to "done". Run python tools/check_evidence.py validate --step STEP-31, show the output, and open the PR. Never claim success without output.
Out of scope: history pull, roster read, rules, flags, digest wording, enabling jobs in production, any Square write.
Use a subagent to review the diff against this step file and report only gaps that affect correctness or the stated acceptance criteria.
```
