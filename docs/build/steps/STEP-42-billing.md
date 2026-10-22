# STEP-42 Billing with one-click cancel

Track: build. Lane: console. Gate kind: ci_fixture. Size: M. Runs only if STEP-21 recorded GO.
Depends on: STEP-07 Design Partner Agreement and pass line signed, STEP-10 Owner sign-in with TOTP two-factor. Done requires: none. D12 (billing provider; TBD — not in sources) blocks the start of this step.
Blocks: none in the plan. Needed by day 90 of the pilot term, not by STEP-43.
Sources: Slide 21 ("Month-to-month, one-click cancel": monthly billing, cancel in one click, no hidden per-feature fees; exit rights), Slide 3 (C1: under $100 a month, $79–99, month-to-month, one-click cancel, no hidden fees), Slide 26 (after the 90-day term: "$79–99, month-to-month, one-click cancel"; 10–20% charged up front under the DPA), Slide 29 (RK7: month-to-month billing and the CSV export clause); BUILD_PLAN §9, design choices 4, 31; D12.

## Outcome
- `tillowl/console/billing.py`: a billing page and two owner-only actions on the console.
  - **Start monthly plan.** The owner starts it themselves after the 90-day term; nothing converts or charges automatically (design choice). The page shows one monthly price, read from config and equal to the signed DPA's intended price, plus the words "month-to-month" and "cancel any time in one click".
  - **Cancel.** One button, one form submit, with no confirmation page, survey, retention offer or "contact support" step in between. Cancelling stops every future charge. Service runs to the end of the month already paid (design choice), then STEP-29's termination path starts: a 30-day CSV export of all flagged events, then deletion per contract.
- The D12 provider's client, using httpx like the other vendors. Card details are entered only on the provider's own hosted page, if D12's provider offers one (TBD — not in sources; if it doesn't, stop and raise it with the founder). TillOwl never receives, logs or stores a card number.
- Billing state (provider customer reference, plan status, paid-through date, cancel date) is held as columns added to STEP-08's tenant table, through a plain `ALTER TABLE … ADD COLUMN` migration. A new table would need RLS policies, and CI sends any migration touching policies to a gate-change PR once STEP-08 is done.
- The up-front 10–20% DPA fee is invoiced outside the product (design choice 31). Whether it is credited against later months follows the signed DPA; TBD — not in sources.

## Acceptance criteria
1. Given any tenant in any plan state (`none`, `active`, `cancel_pending`, `ended`), `pytest -c pytest.ini --rootdir=. tests/gates/step_42/test_billing_cancel.py` passes. For every state where a charge is still scheduled, exactly one POST to the cancel route results in:
   - no further charge scheduled at the provider (stubbed);
   - a stored cancel date;
   - an `audit_log` row for the billing change, written through `audit()`.
2. The cancel action needs no input beyond the signed-in owner's session and its CSRF token. The test asserts that cancel is reachable in one request from the billing page and that the response is the final state, not a confirmation step.
3. The amount on the billing page equals the amount sent to the provider for every configured price. No other line item, setup fee or per-feature charge is ever created; the test checks the stubbed provider calls.
4. Owner only. Another tenant's owner, a signed-out request, and a session without completed two-factor all get no billing data and change nothing, and each attempt writes a denied-access `audit_log` row (STEP-10's helper). Row-level security returns zero rows across tenants.
5. Cancelling never deletes data at once. The termination path starts at the paid-through date, and the 30-day export stays available after it (STEP-29). The test checks the stored dates for a cancel on the first, a middle and the last day of a paid month.
6. A cancelled tenant is never charged again, even if the provider stub reports a later renewal attempt. Starting again needs a new "Start monthly plan" action.
7. No real charge in CI. The provider is called only through its test mode, where its official docs show one (cite the URL as an unverified candidate), otherwise through a stub. The gate list names no fixture file, so stub responses live inside the test.

## Out of scope
The up-front DPA invoice; dunning and payment-failure emails; provider webhooks, unless D12's provider needs one to confirm a cancel (then add it with signature checking, TBD — not in sources); taxes; any price beyond the one monthly plan; staff access; Toast or voice pricing (v2/v3).

## Gate
`pytest -c pytest.ini --rootdir=. tests/gates/step_42` (exact, from `docs/build/status/STEP-42.json`). Gate files: `docs/build/gates/STEP-42.txt` (`tests/gates/step_42/test_billing_cancel.py`).

`docs/build/evidence/STEP-42.md` holds:
- the command and `exit_code: 0`;
- `count: N passed`;
- `run_id:` of the green `ci` push run on main for the evidence commit's parent (from `gh run view <id> --log` or the JUnit summary);
- `date:`.

## If the gate fails
Revert to the last green commit. Set `blocked` with a `blocked_reason` (no names or values). After two failed attempts, restart in a fresh session with a narrower prompt.
- **D12 still open:** set `blocked_reason: d12_billing_provider_open` and stop.
- **The provider has no hosted card page, or can't cancel in one API call:** stop and raise it with the founder; never build a card form.

## Prompt (paste into a fresh Claude Code session)
```text
You are running STEP-42 "Billing with one-click cancel" for TillOwl. Follow @CLAUDE.md throughout.
Start: git fetch && git rebase origin/main; confirm STEP-07 and STEP-10 are "done" and STEP-21's decision is GO in docs/build/status/ (stop and say which if not); confirm D12 names a billing provider in @docs/build/BUILD_PLAN.md §12 (if not, set status "blocked" with blocked_reason d12_billing_provider_open and stop); read git log -5; run CLAUDE.md's setup command; read @docs/build/steps/STEP-42-billing.md and Slides 3, 21, 26, 29 in @docs/architecture-pack-part1.md and @docs/architecture-pack-part2.md.
Work, test first:
- Set docs/build/status/STEP-42.json status to "in_progress".
- Use WebFetch on the D12 provider's official docs for hosted checkout, one-call cancellation and test mode; cite each URL as an unverified candidate in the PR description. Invent no endpoint, field or price.
- Write tests/gates/step_42/test_billing_cancel.py exactly as listed in docs/build/gates/STEP-42.txt (stub responses inline); run it; it fails (print RED TEST (intentional) if you stop here).
- Implement tillowl/console/billing.py and the ALTER TABLE migration to the acceptance criteria. If the work seems to need a new table, a policy or a grant, stop: that needs a gate-change PR.
- Run the test command from CLAUDE.md and show the output; commit; open the step PR with gh.
Done PR (after the step PR merges and the ci push run on main is green): add docs/build/evidence/STEP-42.md as one commit on top of main, from that run's id and its "N passed" count; set status "done"; run python tools/check_evidence.py validate --step STEP-42 and show the output; open the PR with gh. Show every command and its output; never claim success without it.
Out of scope: the up-front DPA invoice, dunning, taxes, extra plans, staff access, any real charge.
End: Use a subagent to review the diff against this step file and report only gaps that affect correctness or the stated acceptance criteria.
```
