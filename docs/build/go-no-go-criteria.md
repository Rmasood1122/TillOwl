# Go/no-go criteria for the live-account spike (DRAFT)

**Status: DRAFT.** The founder edits this file and accepts it before the live spike (STEP-20). To accept it, remove every occurrence of the word DRAFT and merge the change on a branch named `gate-change/step-18-accept-criteria`. The file is G1-protected. STEP-18 hashes the accepted version, and STEP-21 refuses to record a decision if it changed after acceptance.

The decision is recorded in STEP-21 against these criteria and RK1 on Slide 29: "Test every verify item on the friend's account before day one; start with the fallback wording; stop if the signal is too thin." Inputs:
- the `v_item` results and counts in STEP-20's evidence and `docs/build/findings/square-fields.md`;
- STEP-01's sandbox findings;
- counsel's T17a answer (STEP-02);
- the signed DPA and pass line (STEP-07).

PARTIAL counts as NOT_RETURNED (Slide 30: nothing appears in a digest until its test passes). A sub-field that passes on its own is recorded as its own RETURNED item, for example `V2.opened_by`.

## 1. Hard stops: NO-GO whatever else is true

1. **No cancelled-order counts per business day.** The checked fact is that voided orders come back CANCELED without line items (Slide 3, T2), so cancelled-order counts are the base signal. If even those can't be counted per business day, there is nothing to show.
2. **V8 NOT_RETURNED: no 30 days of history.** The pass line needs "30 days before" (Slide 26).
   - Default: NO-GO.
   - Founder option (edit before accepting): GO only if the signed DPA already contains a collect-first variant, where the first 30 pilot days build the "before" figure and the 90-day term starts after them, and counsel reviewed it under T17a.
3. **V1 or V5 NOT_RETURNED and no signed substitute measure.** The pass line is voids + comps + discounts as a percent of net sales (Slide 26), so it needs void dollars (V1) and comp detail (V5). If either is missing, GO needs the substitute measure for that case and the 0.5–1 point rule already signed in the DPA (STEP-07, RK2, T11).
4. **Both V2 and V7 NOT_RETURNED: no per-login signal at all.** Per-login baselines then have no data (our inference, not in the pack).
   - Default: NO-GO under RK1, "stop if the signal is too thin".
   - Founder option (edit before accepting): GO for a shift-level-only digest, if the owner agrees in writing that shift-level facts are useful.

## 2. What the digest shows for each V-item

| Item | If RETURNED | If NOT_RETURNED or PARTIAL |
|---|---|---|
| V1 dollar amount on cancelled orders | Dollar totals appear in cancelled-order lines; the pass line is measured as written | No dollar amounts; the pass line uses the DPA's substitute measure |
| V2 login on cancelled orders | Fallback sentence with the login clause: "9 checks cancelled during shift Y (opened by login X)" | Fallback sentence without the login clause: "9 checks cancelled during shift Y" |
| V3 item voids on paid checks | Item-void counts per login and shift | Left out |
| V4 approving manager code | "approved by code Y" added to the line | Left out |
| V5 comp detail | Comp counts and amounts per login and shift | Left out |
| V6 no-sale drawer opens | No-sale counts per login and shift | Left out |
| V7 login on discounts and refunds | Discounts and refunds per login and shift window | Discounts and refunds per shift window only; no login named |
| V8 30 days of history | Baselines start from the history pull | Hard stop 2 |

A login appears in any line only once its acknowledgment is on file (ADR-006; the flag-level gate is a design choice).

## 3. Is the signal thick enough? (RK1 thresholds, D16)

These numbers are **proposed by the plan, not taken from the sources**. The founder sets them before accepting. They are read from STEP-20's counts over the history the spike can see (30 days if V8 is RETURNED).

| Measure | Proposed GO threshold | Evidence line |
|---|---|---|
| Orders | at least 300 in 30 days | `count: N orders` |
| At least one monitored metric with enough events | at least 20 events in 30 days for at least one of: cancelled orders, comps, discounts, refunds, no-sale opens | `count: N cancelled_orders`, `count: N comps`, `count: N discounts`, `count: N refunds`, `count: N no_sale_opens` |
| Distinct logins (only if V2 or V7 is RETURNED) | at least 3 hashed logins with events | `count: N logins_hashed` |

If any threshold is missed: NO-GO by default. The founder may write a different rule here before accepting.

## 4. Recording the decision

The founder sets `decision` to GO or NO-GO in `docs/build/status/STEP-21.json` and runs `python tools/check_evidence.py decision` in the engineer's session. The command prints:
- the decision;
- every V-item result;
- the hash of this file as accepted.

That output is the STEP-21 evidence.
- **GO:** the data-dependent steps (STEP-31 onward) may start.
- **NO-GO:** STEP-22 runs the exit: revoke OAuth, give the owner the notice and acknowledgment records, delete tenant data, verify the deletion, and settle the up-front fee under the DPA.
