# STEP-38 V-item branches in templates and checker

Track: build. Lane: digest. Gate kind: ci_fixture. Size: S.
Depends on: STEP-21 Go/no-go decision recorded, STEP-24 Digest fact checker and deny-list, STEP-37 Flags B and the ranker. Done requires: none. Runs only if STEP-21 recorded GO (`runs_if: "GO"`).
Blocks: STEP-40 counsel review T17b, STEP-43 pilot-readiness gate.
Sources: Slide 12 (target sentence; day-one sentence "9 checks cancelled during shift Y (opened by login X)"), Slide 13 step 11, Slide 21 (fact-based wording; workflow step 5), Slide 24 (scenario 2), Slide 3 (P4, P7, L4, L5), Slide 30 (rule: nothing unconfirmed appears in a digest), ADR-004, ADR-006; BUILD_PLAN design choices 10, 12, 16, 23, 24, 32; D8; `docs/build/go-no-go-criteria.md` §2.

## Outcome
The fact templates in `tillowl/digest/templates/` (STEP-23), `tillowl/digest/checker.py` (STEP-24) and STEP-26's `render_digest` in `tillowl/digest/build.py` choose their wording from `tillowl.config.V_ITEMS` and the stored flag, following the go-no-go criteria table (§2). Unconfirmed fields are left out, or the fallback sentence is used. Dollar amounts use STEP-23's `{amount}` placeholder (integer cents). Leaving out a whole line (V3, V5, V6 not RETURNED) is decided in the digest build (`render_digest`), not by `fact_line`, which still renders a line whenever it is called. `tillowl/digest/templates/MANIFEST.json` is updated to the new template hashes; before T17b this needs only code-owner review (design choice 32).

## Acceptance criteria
1. Given `tests/gates/step_38/fixtures/flags_mixed_v_results.json`, `pytest -c pytest.ini --rootdir=. tests/gates/step_38` passes. The tests render every fixture flag under **every** combination of RETURNED, NOT_RETURNED and PARTIAL for V1–V7 (generated, not listed by hand), and assert for each rendered line:
   - it contains the clause "(opened by login X)" only if V2 is RETURNED and the flag carries an acknowledged login; otherwise it reads "9 checks cancelled during shift Y", with the flag's own count and shift name;
   - it contains "approved by code Y" only if V4 is RETURNED and the flag's evidence holds that code;
   - it contains a dollar amount (through `{amount}`) only if V1 is RETURNED (cancelled orders) or V5 is RETURNED (comps), and only an amount stored in the flag;
   - `render_digest` emits no line for an `item_voids`, `comps` or `no_sale_opens` flag whose V-item (V3, V5, V6) is not RETURNED, while `fact_line` called directly on that flag still returns one line (STEP-23's frozen contract);
   - a discount or refund line names a login only if V7 is RETURNED.
   PARTIAL renders exactly like NOT_RETURNED (design choice 10).
2. The checker (scenario 2) still rejects any number, time or name not in the stored flag, and any deny-list word, and sends the branch's template line instead. Under every combination above, an LLM sentence from the fixture that adds a login to a shift-window-only flag, a dollar amount when V1 is not RETURNED, or an approving code when V4 is not RETURNED is replaced by the template line.
3. No rendered line contains a display name, "thief" or another deny-list word, a wage deduction (L4), or wording that presents a flag as the basis for a firing (Slide 21). Lines go to the owner only.
4. Every file in `tillowl/digest/templates/` is listed in `MANIFEST.json` with its current SHA-256, and `python tools/check_evidence.py manifest` exits 0. STEP-23's frozen gate tests still pass unchanged on the PR, and STEP-24's and STEP-26's (ci_staging) stay green in the staging run on main after merge.
5. V-item results come only from `tillowl.config.V_ITEMS`; templates, checker and `render_digest` never hard-code a V-item result. Every test pins `V_ITEMS` explicitly with monkeypatch for each combination, both the RETURNED and the NOT_RETURNED branch of every item, and never reads `square-fields.md` (BUILD_PLAN §7). The fixture is synthetic (login codes like `L07`, shift names like "Dinner").

## V-item branches
Per `docs/build/go-no-go-criteria.md` §2:
- **V1.** If RETURNED: dollar totals appear in cancelled-order lines. If NOT_RETURNED or PARTIAL: no dollar amounts in cancelled-order lines.
- **V2.** If RETURNED: "9 checks cancelled during shift Y (opened by login X)". If NOT_RETURNED or PARTIAL: "9 checks cancelled during shift Y".
- **V3.** If RETURNED: item-void counts per login and shift. If NOT_RETURNED or PARTIAL: left out.
- **V4.** If RETURNED: "approved by code Y" added to the line. If NOT_RETURNED or PARTIAL: left out.
- **V5.** If RETURNED: comp counts and amounts per login and shift. If NOT_RETURNED or PARTIAL: left out.
- **V6.** If RETURNED: no-sale counts per login and shift. If NOT_RETURNED or PARTIAL: left out.
- **V7.** If RETURNED: discounts and refunds per login and shift window. If NOT_RETURNED or PARTIAL: per shift window only; no login named.

## Out of scope
Adding deny-list words (STEP-24 owns the list; any change still goes through the manifest); the explanation prompt (STEP-25); delivery (STEP-26); flag logic (STEP-36, STEP-37); any edit after STEP-40 is done.

## Gate
`pytest -c pytest.ini --rootdir=. tests/gates/step_38` (exact, from `docs/build/status/STEP-38.json`). Gate files, exactly as in `docs/build/gates/STEP-38.txt`: `test_v_item_wording.py`, `fixtures/flags_mixed_v_results.json`.

`docs/build/evidence/STEP-38.md` holds one block: the command, `exit_code: 0`, `count: N passed`, the `run_id` of the green `ci` push run on main for the evidence commit's parent, and a date.

## If the gate fails
Revert to the last green commit. Set the status to `blocked` with a `blocked_reason` (no names or values). After two failed attempts, restart in a fresh session with a narrower prompt. If STEP-40 is already done, stop: a template change then needs a founder-approved gate-change PR and reopens T17b.

## Prompt (paste into a fresh Claude Code session)
```text
You are running STEP-38 "V-item branches in templates and checker" for TillOwl. Follow @CLAUDE.md throughout.
Start:
1. git fetch && git rebase origin/main
2. Confirm STEP-21, STEP-24 and STEP-37 are "done" in docs/build/status/, "decision" in STEP-21.json is "GO", and STEP-40 is not "done". If not, stop and say which.
3. Read git log -5. Run CLAUDE.md's setup command.
4. Read @docs/build/steps/STEP-38-v-item-branches.md, @docs/build/go-no-go-criteria.md (section 2), @docs/build/findings/square-fields.md, @tillowl/digest/templates/MANIFEST.json, @tillowl/digest/checker.py, @tillowl/digest/facts.py, @tillowl/digest/build.py (render_digest), @tillowl/config.py, then Slides 3, 12, 13, 21, 24, 30 in @docs/architecture-pack-part1.md and @docs/architecture-pack-part2.md.
Work, test first:
- Set docs/build/status/STEP-38.json status to "in_progress".
- Write the gate files exactly as listed in docs/build/gates/STEP-38.txt: a synthetic fixture of flags and LLM sentences, and tests that generate every V1–V7 combination, pin V_ITEMS with monkeypatch for each (both branches), and check every acceptance criterion. Run them; they fail (print RED TEST (intentional) if you stop here).
- Edit the templates, the checker and render_digest (line left out for V3/V5/V6 not RETURNED; fact_line unchanged); update MANIFEST.json hashes. Run python tools/check_evidence.py manifest and show the output.
- Run the gate command, STEP-23's gate and CLAUDE.md's test command; show the outputs. STEP-24's and STEP-26's gates are ci_staging and run on main after merge: check that staging run is green before the done PR. Commit; open the step PR with gh (status in_progress). It needs a code owner's review (manifest) and merges when CI is green.
Done PR (after the step PR merges): one commit on top of main holding only docs/build/evidence/STEP-38.md and the status set to "done". run_id is the green ci push run on main for that commit's parent; count: N passed comes from that run (gh run view <id> --log or its JUnit summary). Run python tools/check_evidence.py validate --step STEP-38 and show the output. Never claim success without the output.
Out of scope: deny-list additions, the explanation prompt, delivery, flag logic, any edit after T17b.
End: Use a subagent to review the diff against this step file and report only gaps that affect correctness or the stated acceptance criteria.
```
