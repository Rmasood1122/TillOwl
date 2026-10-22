# STEP-39 Pass-line measurement

Track: build. Lane: rules. Gate kind: ci_fixture. Size: S.
Depends on: STEP-21 Go/no-go decision recorded, STEP-31 Square event ingestion. Done requires: none. Runs only if STEP-21 recorded GO (`runs_if: "GO"`). Also blocked by founder decision D10 until it is recorded as Resolved in BUILD_PLAN §12.
Blocks: STEP-40 counsel review T17b (a D10 link-click count would change a template), STEP-43 pilot-readiness gate.
Sources: Slide 26 (pass line: "voids + comps + discounts as a percent of net sales (sales after refunds), for 30 days before and 60 days after"; PASS ≥ 1 point, FAIL < 0.5 point or the owner stops opening the digest; 0.5–1 TBD; Square caveat; weekly 30-minute check-in), Slide 24 ("the pilot fails if the owner stops opening the digest"), Slide 28 (N13), Slide 29 (RK2, RK4), Slide 30 (V1, V8, T11); BUILD_PLAN design choices 10, 17, 18; D8, D10; `docs/build/go-no-go-criteria.md` §1–2.

## Outcome
`tillowl/rules/passline.py` computes, for one tenant:
- the **before** figure over the 30 days ending the day before pilot day one (design choice 17), and the **after** figure over the 60 days from day one, each as (voids + comps + discounts) ÷ net sales × 100, net sales being sales after refunds; days are the restaurant's business days in its time zone (design choice 18);
- the drop in points and a verdict: `PASS` (drop ≥ 1), `FAIL` (drop < 0.5, or the owner stopped opening the digest), the T11 result for 0.5 ≤ drop < 1, or `INCOMPLETE`;
- the D10 opening measure, in the one variant D10 chose.
`tillowl/jobs/passline_report.py --tenant pilot` runs the measure on production at day 90 (a founder-launched one-off job) and prints only `count: N days`, `passline: PASS|FAIL|T11_ZONE|INCOMPLETE` and `exit_code: 0`; its unit test sits beside the gate tests in `test_passline.py`.
Pilot day one, the T11 rule and the substitute measure are read from `PASS_LINE` in `tillowl/config.py`. The founder supplies these values from the signed DPA (STEP-07). They are never invented.

## Acceptance criteria
1. Given `tests/gates/step_39/fixtures/passline_before_after.json`, `pytest -c pytest.ini --rootdir=. tests/gates/step_39` passes. The tests also generate before/after series whose drop lands just below, on and just above 0.5 and 1.0 points: exactly 1.0 is `PASS`, exactly 0.5 is in the T11 zone, and anything under 0.5 is `FAIL`. Money is summed in integer cents, and the ratio is computed with `Decimal`, so boundaries never depend on float rounding.
2. Windows: the before window ends the day before `PASS_LINE` day one and the after window starts on it, both counted in the restaurant's business days, including a shift that crosses midnight. If any day in either window has no completed pull, or fewer than 60 after-days have passed, the verdict is `INCOMPLETE` and the result gives the missing-day count. It never extrapolates. A closed day with a completed pull counts as a day with zero sales, not a missing one.
3. 0.5–1 point: the verdict is the T11 value in `PASS_LINE`. If that value, day one, or (when V1 is not RETURNED) the substitute measure is unset, `passline` raises a named error. It never falls back to a default.
4. Net sales of zero in a window raise a named error. No division happens and no verdict is given.
5. Opening measure (`test_digest_opening_measure.py`), the D10 variant only:
   - **weekly check-in:** after each weekly check-in (Slide 26) the founder records whether the owner opened the digest that week. A one-field console form, used by the owner or by the founder under support access (STEP-27), writes it through `audit()`; no new table.
   - **disclosed link-click count:** each digest carries one disclosed link with no login code in it, and each click is recorded through `audit()`.
   In either variant, "stopped opening" is decided by the rule recorded with D10 in `PASS_LINE`, never by a number chosen here, and it makes the overall verdict `FAIL` whatever the drop.
6. The measure uses restaurant-level totals only, never per-login values or display names. It imports nothing from `tillowl.explain`.

## V-item branches
- **V1** (dollar amount on cancelled orders). If RETURNED: voids are the cancelled-order dollar totals, and the pass line is measured as written. If NOT_RETURNED or PARTIAL: the DPA's substitute measure, as transcribed in `PASS_LINE`, is used; with none set, `passline` raises (go-no-go hard stop 3 should have prevented GO).
- **V5** (comp detail). If RETURNED: comp amounts enter the numerator. If NOT_RETURNED or PARTIAL: the comps term comes only from what the signed DPA variant in `PASS_LINE` says; with nothing set, `passline` raises. It never silently drops the term.
- **V8** (30 days of history). If RETURNED: the before window comes from the STEP-34 history pull. If NOT_RETURNED or PARTIAL: hard stop 2, so this step runs only under the founder's collect-first option, with the before window as `PASS_LINE` defines it.

## Out of scope
The digest's own wording (STEP-38); telling the owner the result; the D10 variant not chosen.

## Gate
`pytest -c pytest.ini --rootdir=. tests/gates/step_39` (exact, from `docs/build/status/STEP-39.json`). Gate files, exactly as in `docs/build/gates/STEP-39.txt`: `test_passline.py`, `test_digest_opening_measure.py`, `fixtures/passline_before_after.json`.

`docs/build/evidence/STEP-39.md` holds one block: the command, `exit_code: 0`, `count: N passed`, the `run_id` of the green `ci` push run on main for the evidence commit's parent, and a date.

## If the gate fails
Revert to the last green commit. Set the status to `blocked` with a `blocked_reason` (no names or values). After two failed attempts, restart in a fresh session with a narrower prompt. If D10 or a `PASS_LINE` value is missing, set `blocked_reason: d10_open` or `pass_line_config_missing`, and never guess.

## Prompt (paste into a fresh Claude Code session)
```text
You are running STEP-39 "Pass-line measurement" for TillOwl. Follow @CLAUDE.md throughout.
Start:
1. git fetch && git rebase origin/main
2. Confirm STEP-21 and STEP-31 are "done" in docs/build/status/, "decision" in STEP-21.json is "GO", and D10 is marked Resolved in @docs/build/BUILD_PLAN.md section 12. If not, stop and say which.
3. Read git log -5. Run CLAUDE.md's setup command.
4. Read @docs/build/steps/STEP-39-pass-line-measure.md, @docs/build/go-no-go-criteria.md, @docs/build/findings/square-fields.md, @tillowl/config.py, then Slides 24, 26, 28, 29, 30 in @docs/architecture-pack-part2.md.
Founder input: ask the founder for PASS_LINE (pilot day one, the T11 rule for a 0.5–1 point drop, the substitute measure if V1 is not RETURNED, the comps term if V5 is not RETURNED, the D10 opening rule) as the signed DPA and D10 state them. Never read $PRIVATE_EVIDENCE_DIR. Print AWAITING HUMAN CONFIRMATION and wait. If D10 is the link-click count and STEP-40 is done, stop: the link is a template change that reopens T17b.
Work, test first:
- Set docs/build/status/STEP-39.json status to "in_progress".
- Write the gate files exactly as listed in docs/build/gates/STEP-39.txt: a synthetic fixture (restaurant-level daily totals only) and tests for every acceptance criterion, including generated boundary series and every V-item branch. Run them; they fail (print RED TEST (intentional) if you stop here).
- Implement tillowl/rules/passline.py, PASS_LINE in tillowl/config.py with the founder's values, and only the D10 variant chosen.
- Run the gate command and CLAUDE.md's test command; show both outputs. Commit; open the step PR with gh (status in_progress), asking the founder to review the PASS_LINE values. It merges when CI is green.
Done PR (after the step PR merges): one commit on top of main holding only docs/build/evidence/STEP-39.md and the status set to "done". run_id is the green ci push run on main for that commit's parent; count: N passed comes from that run (gh run view <id> --log or its JUnit summary). Run python tools/check_evidence.py validate --step STEP-39 and show the output. Never claim success without the output.
Out of scope: digest wording, telling the owner the result, a production pass-line command, the D10 variant not chosen.
End: Use a subagent to review the diff against this step file and report only gaps that affect correctness or the stated acceptance criteria.
```
