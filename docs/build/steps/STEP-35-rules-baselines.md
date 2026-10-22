# STEP-35 Ratio rules and baselines

Track: build. Lane: rules. Gate kind: ci_fixture. Size: M. Runs only if STEP-21 recorded GO.
Depends on: STEP-21 go/no-go decision recorded (GO), STEP-28 console shift windows and digest settings, STEP-31 Square event ingestion (scenario 1), STEP-32 roster-read job and acknowledgment mapping. Done requires: none.
Blocks: STEP-36 flags A (cancelled orders, item voids, approval codes, no-sale opens).
Sources: Slide 3 (P2 "every flag can be reproduced without the model"), Slides 12–13 (flow steps 3–5: "Cancelled-order, comp, discount, refund and no-sale counts; shares of net sales"; "Baseline per login and shift window"), Slides 17–18 (BAS "login, shift window, metric, normal range"; Q8), Slide 26 (net sales = "sales after refunds"), Slide 29 (TD4), ADR-002, ADR-006; BUILD_PLAN design choices 15, 16, 18; T17a code `pre_notice_history`.

## Outcome
**`tillowl/rules/ratios.py`.** `ratios(tenant, business_day)` reads the day's stored events and returns rows in process (Slide 13 step 4; no table). Each row is keyed by login (or none) and owner-set shift window, and holds:
- counts of cancelled orders, comps, discounts, refunds, no-sale opens and item voids;
- shares of net sales (sales after refunds) for each amount that is stored.

**`tillowl/rules/baselines.py`.** `update_baselines(tenant, business_day)` upserts `baseline` rows: `login_id`, `shift_id`, metric, normal range and the number of shifts used.
- Per-login rows exist only for logins whose acknowledgment is on file, including new hires once their acknowledgment is entered.
- Which events feed a login's baseline branches on `COUNSEL.pre_notice_history` (T17a), always measured against `acknowledgment.signed_at` (the paper signing date), never the date it was entered: `TOTALS_ONLY` → only that login's events on or after `signed_at`; `PER_LOGIN_ALLOWED` → STEP-34's history-pull events of that login from before `signed_at` may feed it too. With 8 shifts needed, day one may have few per-login baselines either way.
- Window-level rows (`login_id` null) cover restaurant totals, stripped events included.
- Normal range (design choice): the median and the median absolute deviation over the trailing 30 business days the login worked that window. A baseline exists only after at least 8 such shifts. Both numbers are module constants, hand-tuned per restaurant (TD4).

**`tillowl/jobs/run_rules.py`** (`--tenant … --date YYYY-MM-DD`) runs steps 3–5 for now, and STEP-36 and 37 add flags and the ranker. It prints only `count: N rows`, then `date:` and `exit_code: N`, and stays off in production until STEP-43.

Plain code only: no model and no network (P2, ADR-002).

## Acceptance criteria
1. **Ratios** (`test_ratios.py`, given `fixtures/events_30_days.json`: synthetic normalized events over 30 business days, logins `L01`–`L06`, windows "Lunch", "Dinner" and "Late", where "Late" crosses midnight).
   - For every (day, login, window), the counts equal the fixture's hand-counted `expected` block.
   - Every share equals amount divided by (sales minus refunds). A window with zero net sales yields no share, not 0 and not an error.
   - Events after midnight count in the "Late" window's business day.
   - Two runs give identical output.
   - A static check fails if anything under `tillowl/rules/` imports `tillowl.explain` or `anthropic`.
2. **Baselines only for acknowledged logins** (`test_baselines_ack_only.py`).
   - A per-login baseline exists only for logins whose acknowledgment is entered and mapped.
   - With `COUNSEL` pinned (monkeypatch) to `TOTALS_ONLY`, a login whose `signed_at` is fixture day 20 (entered on day 25) gets a baseline built only from events on or after day 20, and has none before 8 such shifts. Pinned to `PER_LOGIN_ALLOWED`, its earlier fixture events also feed it. An entry date never moves the cut-off.
   - Unacknowledged logins appear only in window-level rows.
   - A planted login-tagged event of an unacknowledged login is ignored and creates no row (defence in depth on top of STEP-31's stripping).
   - A re-run upserts and never duplicates.
3. **Branches through `V_ITEMS` only.**
   - Tests pin `V_ITEMS` explicitly (monkeypatch). With every item RETURNED, every metric is present.
   - With every item NOT_RETURNED, and again with PARTIAL, each gated metric listed below has no row (not a zero row). The per-login rows for V2- and V7-gated metrics disappear, and their window-level rows remain.

## V-item branches
- **V1 (dollar amount on cancelled orders).** If V1 is RETURNED: a cancelled-dollar share per login and window. If NOT_RETURNED or PARTIAL: cancelled-order counts only.
- **V2 (login on cancelled orders).** If V2 is RETURNED: cancelled-order counts, and net sales, per login and window. If NOT_RETURNED or PARTIAL: per window only, and no per-login shares.
- **V3 (item voids on paid checks).** If V3 is RETURNED: an item-void count metric. If NOT_RETURNED or PARTIAL: no such metric.
- **V4 (approving manager code).** No metric in this step in either branch. STEP-36 adds the code to the flag line when V4 is RETURNED.
- **V5 (comps).** If V5 is RETURNED: comp count and comp share per login and window. If NOT_RETURNED or PARTIAL: no comp metrics.
- **V6 (no-sale drawer opens).** If V6 is RETURNED: no-sale counts per login and window. If NOT_RETURNED or PARTIAL: no no-sale metric.
- **V7 (login on discounts and refunds).** If V7 is RETURNED: discount and refund counts and shares per login and window. If NOT_RETURNED or PARTIAL: per window only.
- **V8 (30 days of history).** If V8 is RETURNED: baselines start from STEP-34's history. Under the collect-first option, they start once 8 pilot shifts exist.

## Out of scope
Flags, departures and ranking (STEP-36 and 37); the pass line (STEP-39); any LLM call; enabling `run_rules` in production.

## Gate
`pytest -c pytest.ini --rootdir=. tests/gates/step_35` (exact, from the status file). The gate files are listed in `docs/build/gates/STEP-35.txt`. `docs/build/evidence/STEP-35.md` holds one pytest block: `command:`, `exit_code: 0`, `count: N passed`, the `run_id:` of the green `ci` push run on main for the evidence commit's parent, and `date:`.

## If the gate fails
Revert to the last green commit. Set the status to `blocked` with a `blocked_reason` (no names or values). After two failed attempts, restart in a fresh session with a narrower prompt. Never change the fixture's `expected` block to match the code.

## Prompt (paste into a fresh Claude Code session)
```text
You are running STEP-35 "Ratio rules and baselines" for TillOwl. Follow @CLAUDE.md throughout.
Start:
1. git fetch && git rebase origin/main
2. Confirm STEP-21, STEP-28, STEP-31 and STEP-32 are "done" in docs/build/status/, and that STEP-21's "decision" is "GO". If not, stop and say which.
3. Read git log -5.
4. Run CLAUDE.md's setup command.
5. Read @docs/build/steps/STEP-35-rules-baselines.md, @tillowl/config.py (V_ITEMS, COUNSEL), @tillowl/square/ingest.py, and Slides 3, 12, 13, 17, 18, 26 and 29 in @docs/architecture-pack-part1.md and @docs/architecture-pack-part2.md.
Work, test first:
- Set docs/build/status/STEP-35.json status to "in_progress".
- Write the two tests and the fixture exactly as listed in docs/build/gates/STEP-35.txt. Hand-count the expected block before writing any code.
- Run pytest -c pytest.ini --rootdir=. tests/gates/step_35. It fails (print RED TEST (intentional) if you stop here).
- Implement rules/ratios.py, rules/baselines.py and the steps 3–5 part of jobs/run_rules.py, to the acceptance criteria.
- Run the gate and CLAUDE.md's test command, and show both outputs. Commit, then open the step PR with gh (status in_progress). It merges when CI is green.
Done PR: after the ci push run on main is green, make one commit on top of main holding only docs/build/evidence/STEP-35.md (command, exit_code: 0, count: N passed and run_id from that run via gh run view <id> --log, date) and the status set to "done". Run python tools/check_evidence.py validate --step STEP-35, show the output, and open the PR. Never claim success without output.
Out of scope: flags, ranking, pass line, LLM, enabling jobs.
Use a subagent to review the diff against this step file and report only gaps that affect correctness or the stated acceptance criteria.
```
