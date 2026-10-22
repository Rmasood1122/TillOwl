# STEP-37 Flags B: comps, discounts, refunds (V5, V7) and the ranker

Track: build. Lane: rules. Gate kind: ci_fixture. Size: M.
Depends on: STEP-36 Flags A. Done requires: none. Runs only if STEP-21 recorded GO (`runs_if: "GO"`).
Blocks: STEP-38 V-item branches in templates and checker, STEP-41 metered cost estimate, STEP-43 pilot-readiness gate.
Sources: Slide 12 (anomaly ranker "ranks the few biggest departures"), Slide 13 steps 6–8, Slides 15–16 (CMP, DSC, REF, LIN; R11, R12, R13), Slides 17–18 (Flag; Q7, Q9, Q12), Slide 21 (workflow step 5), Slide 29 (RK1, TD4), Slide 30 (V5, V7, rule), ADR-002, ADR-004, ADR-006; BUILD_PLAN design choices 10, 14, 16; D8; `docs/build/go-no-go-criteria.md` §2.

## Outcome
- `tillowl/rules/flags.py` gains `comps`, `discounts` and `refunds` flags in the same `flag` rows as STEP-36 (login or NULL, shift window, metric, value, baseline, time-stamped evidence of check ids and times).
- `tillowl/rules/ranker.py` ranks all of a run's flags (STEP-36's and these) by their departure from baseline and stores a `rank` on each flag; the top `RANK_TOP_N` are the "top flags" the explanation service reads 2–3 times a week (Slide 13 step 8). `RANK_TOP_N` lives in `tillowl/config.py`; the founder sets its value (hand-tuned per restaurant, TD4).
- `tillowl.jobs.run_rules` runs flags, then the ranker. In production it stays off behind `TILLOWL_JOBS_ENABLED` until STEP-43.

## Acceptance criteria
1. Given `tests/gates/step_37/fixtures/events_comps_discounts_refunds.json`, `pytest -c pytest.ini --rootdir=. tests/gates/step_37` passes for both branches of V5 and V7, with PARTIAL behaving exactly like NOT_RETURNED (design choice 10). A flag exists exactly when `value` is above the upper bound of the matching baseline's normal range (Q9); the tests vary the ranges, so fixture-tuned code fails.
2. Acknowledgment gate (design choice 16): a comp, discount or refund flag names a login only if STEP-32's mapping holds an acknowledgment for it at run time. Otherwise the events count only toward shift-window flags and the login appears in no row.
3. Evidence: each flag's evidence lists exactly the check ids and times counted in its `value`, in the restaurant's time zone. Comp, discount and refund amounts appear only when the branch below allows them.
4. Ranker, for every set of flags (the tests generate sets, not just the fixture's):
   - the order is a strict total order and the same on every run: departure is `value` divided by the baseline's upper bound, ties broken by metric name, then earliest evidence time, then flag id;
   - shift-window-only flags rank alongside per-login flags;
   - exactly `min(RANK_TOP_N, number of flags)` flags are marked top, and changing `RANK_TOP_N` changes only the cut, never the order;
   - the ranker reads only stored flag fields; it never reads display names, events or anything outside the flag row.
5. Reproducible without the model (P2): re-running flags and the ranker on the same inputs gives identical rows and ranks; neither module imports `tillowl.explain` or the `anthropic` SDK.
6. V-item results come only from `tillowl.config.V_ITEMS`; the tests switch branches by changing `V_ITEMS` alone. Rows carry `tenant_id`, login codes only (design choice 14), no free text or label. Fixtures are synthetic (login codes like `L07`, shift names like "Dinner").

## V-item branches
- **V5** (comp detail). If RETURNED: `comps` flags with counts and amounts per acknowledged login and shift window, against that login's baseline. If NOT_RETURNED or PARTIAL: the metric is not flagged at all.
- **V7** (login on discounts and refunds). If RETURNED: `discounts` and `refunds` flags per acknowledged login and shift window, against that login's baseline. If NOT_RETURNED or PARTIAL: flagged per shift window only, against the shift-window baseline, with `login_id` NULL, so the digest names no login.

## Out of scope
Cancelled orders, item voids, approval codes, no-sale opens (STEP-36); digest wording (STEP-38); the LLM explanation (STEP-25); setting `RANK_TOP_N`'s production value (the founder does that at onboarding); any write to Square.

## Gate
`pytest -c pytest.ini --rootdir=. tests/gates/step_37` (exact, from `docs/build/status/STEP-37.json`). Gate files, exactly as in `docs/build/gates/STEP-37.txt`: `test_flags_b_branches.py`, `test_ranker.py`, `fixtures/events_comps_discounts_refunds.json`.

`docs/build/evidence/STEP-37.md` holds one block: the command, `exit_code: 0`, `count: N passed`, the `run_id` of the green `ci` push run on main for the evidence commit's parent, and a date.

## If the gate fails
Revert to the last green commit. Set the status to `blocked` with a `blocked_reason` (no names or values). After two failed attempts, restart in a fresh session with a narrower prompt. Never weaken STEP-36's gate tests to fit the ranker; they are frozen.

## Prompt (paste into a fresh Claude Code session)
```text
You are running STEP-37 "Flags B: comps, discounts, refunds and the ranker" for TillOwl. Follow @CLAUDE.md throughout.
Start:
1. git fetch && git rebase origin/main
2. Confirm STEP-36 is "done" in docs/build/status/STEP-36.json and "decision" in docs/build/status/STEP-21.json is "GO". If not, stop and say which.
3. Read git log -5. Run CLAUDE.md's setup command.
4. Read @docs/build/steps/STEP-37-flags-b-ranker.md, @docs/build/go-no-go-criteria.md (section 2), @tillowl/rules/flags.py, @tillowl/rules/baselines.py, @tillowl/config.py, then Slides 12, 13, 15–18, 21, 29, 30 in @docs/architecture-pack-part1.md and @docs/architecture-pack-part2.md.
Work, test first:
- Set docs/build/status/STEP-37.json status to "in_progress".
- Write the gate files exactly as listed in docs/build/gates/STEP-37.txt: a synthetic fixture (login codes like L07, one unacknowledged login, both V5 and V7 branches) and tests for every acceptance criterion, including PARTIAL and generated flag sets for the ranker. Run them; they fail (print RED TEST (intentional) if you stop here).
- Extend tillowl/rules/flags.py; write tillowl/rules/ranker.py; add RANK_TOP_N to tillowl/config.py; call the ranker from tillowl/jobs/run_rules.py after the flags.
- Run the gate command, STEP-36's gate and CLAUDE.md's test command; show the outputs. Commit; open the step PR with gh (status in_progress). It merges when CI is green.
Done PR (after the step PR merges): one commit on top of main holding only docs/build/evidence/STEP-37.md and the status set to "done". run_id is the green ci push run on main for that commit's parent; count: N passed comes from that run (gh run view <id> --log or its JUnit summary). Run python tools/check_evidence.py validate --step STEP-37 and show the output. Never claim success without the output.
Out of scope: STEP-36's metrics, digest wording, the explanation, RANK_TOP_N's production value, any write to Square.
End: Use a subagent to review the diff against this step file and report only gaps that affect correctness or the stated acceptance criteria.
```
