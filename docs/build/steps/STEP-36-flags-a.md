# STEP-36 Flags A: cancelled orders, item voids, approval codes, no-sale opens (V1–V4, V6)

Track: build. Lane: rules. Gate kind: ci_fixture. Size: M.
Depends on: STEP-32 Roster-read job and acknowledgment mapping, STEP-35 Ratio rules and baselines. Done requires: none. Runs only if STEP-21 recorded GO (`runs_if: "GO"`).
Blocks: STEP-37 Flags B and the ranker, STEP-43 pilot-readiness gate.
Sources: Slide 12 (target and day-one sentences), Slide 13 steps 5–7, Slides 15–16 (CHK, CXL, MAC, NSE; R5, R7, R8, R9), Slides 17–18 (Flag: login, shift, metric, value, baseline, evidence; Q7, Q9), Slide 21 (workflow step 5), Slide 3 (P2, T2), Slide 29 (RK1, TD4), Slide 30 (V1–V4, V6, rule), ADR-002, ADR-004, ADR-006; BUILD_PLAN design choices 10, 14, 15, 16, 18; D8; `docs/build/go-no-go-criteria.md` §2.

## Outcome
`tillowl/rules/flags.py` turns STEP-35's counts and baselines for one tenant and one business day into rows of the `flag` table (Slides 17–18) for: `cancelled_orders` (always; T2), the cancelled-order dollar total (V1), `item_voids` (V3), the approving code (V4) and `no_sale_opens` (V6). Each row holds `login_id` (or NULL), `shift_id`, `metric`, `value`, `baseline_id` and `evidence`: the check (order) ids and times, in the restaurant's time zone, that make up `value` (Slide 13 step 7). `tillowl.jobs.run_rules` calls it after the baselines; in production `run_rules` stays off behind `TILLOWL_JOBS_ENABLED` until STEP-43.

## Acceptance criteria
1. Given `tests/gates/step_36/fixtures/events_v_returned.json` with every V-item RETURNED, `pytest -c pytest.ini --rootdir=. tests/gates/step_36` passes. For every (login, shift window, metric) the fixture covers, a flag exists exactly when `value` is above the upper bound of that login's baseline normal range for that window (Q9), and never at or below it. The tests vary the baseline ranges, so code tuned to the fixture fails.
2. Given `events_v_not_returned.json`, run once with each of V1, V2, V3, V4, V6 set NOT_RETURNED and once with each set PARTIAL, the branches below hold, and PARTIAL behaves exactly like NOT_RETURNED (design choice 10). A sub-field recorded as its own RETURNED item (for example `V2.opened_by`) is honoured through the same lookup.
3. Acknowledgment gate (`test_flag_ack_gate.py`; design choice 16): a flag carries a login only if STEP-32's mapping holds an acknowledgment for it when the rules run. An unacknowledged login's events count only in shift-window flags and the login appears in no flag row, even when the test feeds such a login straight past ingest. Once a mapping is removed, the next run names that login nowhere. An approving code (V4) is recorded only if its holder login passes the same gate.
4. Evidence: each flag's evidence lists only the check ids and times of the events counted in its `value` (for count metrics, the number of entries equals `value`). A shift window that crosses midnight yields one business day (design choice 18).
5. Reproducible without the model (P2): two runs on the same inputs write identical rows and no duplicates; `flags.py` imports nothing from `tillowl.explain` or the `anthropic` SDK.
6. Flag rows hold login codes only, never display names (design choice 14), and no free text or label. Every row carries `tenant_id` and is written under row-level security.
7. V-item results are read only through `tillowl.config.V_ITEMS`, loaded from `docs/build/findings/square-fields.md`; the tests switch branches by changing `V_ITEMS` alone. Fixtures are synthetic: login codes like `L07`, shift names like "Dinner", no real names or values.

## V-item branches
- **V1** (dollar amount on cancelled orders). If RETURNED: cancelled-order flags also carry the dollar total of the checks in their evidence. If NOT_RETURNED or PARTIAL: no flag row holds a dollar value from cancelled orders.
- **V2** (login on cancelled orders). If RETURNED: cancelled-order flags per acknowledged login and shift window, against that login's baseline. If NOT_RETURNED or PARTIAL: per shift window only, against the shift-window baseline, with `login_id` NULL (so STEP-38 can only print "9 checks cancelled during shift Y").
- **V3** (item voids on paid checks). If RETURNED: `item_voids` flags per acknowledged login and shift window. If NOT_RETURNED or PARTIAL: the metric is not flagged at all.
- **V4** (approving manager code). If RETURNED: each cancelled-order flag's evidence records the approving code reference per check (holder acknowledged). If NOT_RETURNED or PARTIAL: no approval-code field appears in any flag.
- **V6** (no-sale drawer opens). If RETURNED: `no_sale_opens` flags per acknowledged login and shift window. If NOT_RETURNED or PARTIAL: the metric is not flagged at all.

## Out of scope
Comps, discounts, refunds and ranking (STEP-37); digest wording and template branches (STEP-38); the explanation (STEP-25); building baselines (STEP-35); any write to Square, payroll or schedules.

## Gate
`pytest -c pytest.ini --rootdir=. tests/gates/step_36` (exact, from `docs/build/status/STEP-36.json`). Gate files, exactly as in `docs/build/gates/STEP-36.txt`: `test_flags_a_branches.py`, `test_flag_ack_gate.py`, `fixtures/events_v_returned.json`, `fixtures/events_v_not_returned.json`.

`docs/build/evidence/STEP-36.md` holds one block: the command, `exit_code: 0`, `count: N passed`, the `run_id` of the green `ci` push run on main for the evidence commit's parent, and a date.

## If the gate fails
Revert to the last green commit. Set the status to `blocked` with a `blocked_reason` (no names or values). After two failed attempts, restart in a fresh session with a narrower prompt. If STEP-35 provides no shift-window baseline for the V2 NOT_RETURNED branch, set `blocked_reason: no_shift_window_baseline` rather than inventing one here.

## Prompt (paste into a fresh Claude Code session)
```text
You are running STEP-36 "Flags A: cancelled orders, item voids, approval codes, no-sale opens" for TillOwl. Follow @CLAUDE.md throughout.
Start:
1. git fetch && git rebase origin/main
2. Confirm STEP-32 and STEP-35 are "done" in docs/build/status/, and that "decision" in docs/build/status/STEP-21.json is "GO". If not, stop and say which.
3. Read git log -5. Run CLAUDE.md's setup command.
4. Read @docs/build/steps/STEP-36-flags-a.md, @docs/build/go-no-go-criteria.md (section 2), @docs/build/findings/square-fields.md, @tillowl/config.py, @tillowl/rules/baselines.py, then Slides 3, 12, 13, 15–18, 21, 30 in @docs/architecture-pack-part1.md and @docs/architecture-pack-part2.md.
Work, test first:
- Set docs/build/status/STEP-36.json status to "in_progress".
- Write the gate files exactly as listed in docs/build/gates/STEP-36.txt: synthetic fixtures (login codes like L07, a shift window crossing midnight, one unacknowledged login, an approving code whose holder is unacknowledged) and tests for every acceptance criterion and every V-item branch, including PARTIAL. Run them; they fail (print RED TEST (intentional) if you stop here).
- Implement tillowl/rules/flags.py and call it from tillowl/jobs/run_rules.py after the baselines. Read V-item results only through tillowl.config.V_ITEMS.
- Run the gate command and CLAUDE.md's test command; show both outputs. Commit; open the step PR with gh (status in_progress). It merges when CI is green.
Done PR (after the step PR merges): one commit on top of main holding only docs/build/evidence/STEP-36.md and the status set to "done". run_id is the green ci push run on main for that commit's parent; count: N passed comes from that run (gh run view <id> --log or its JUnit summary). Run python tools/check_evidence.py validate --step STEP-36 and show the output. Never claim success without the output.
Out of scope: comps, discounts, refunds, ranking, digest wording, the explanation, baselines, any write to Square.
End: Use a subagent to review the diff against this step file and report only gaps that affect correctness or the stated acceptance criteria.
```
