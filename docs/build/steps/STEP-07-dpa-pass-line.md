# STEP-07 Design Partner Agreement and pass line signed

Track: human. Lane: legal. Gate kind: human. Size: W (waits on the owner).
Depends on: STEP-02 Counsel review T17a (code `dpa_approved: YES`). Done requires: none. D10 (how "the owner stops opening the digest" is measured) and D15 (our signing entity) must be recorded in BUILD_PLAN §12 before signing, because the text states them.
Blocks: STEP-33 pilot onboarding, STEP-42 billing, STEP-43 pilot-readiness gate.
Sources: Slide 26 (pass line, Square caveat, before day one, fixed 90-day term, "go paid or don't"), Slide 21 (exit rights, no AI training, month-to-month and one-click cancel, fact-based wording), Slide 17 (data rules), Slide 24 ("the pilot fails if the owner stops opening the digest"), Slide 28 (N13), Slide 29 (RK2, RK3, RK4, RK7), Slide 30 (T11, V1, V5, V8), Slide 3 (L4, C1); R2 §6; ADR-004; BUILD_PLAN design choices 17, 31; D9, D10, D12, D15.

## Outcome
Three artifacts, copies at `$PRIVATE_EVIDENCE_DIR/STEP-07/<label>.<ext>`:
- **`dpa`.** The signed Design Partner Agreement (not a data processing agreement), the exact text counsel approved under T17a.
- **`pass_line`.** The pass line, signed by both sides (Slide 26). It may be a schedule inside the DPA, but it is saved as its own copy so it has its own hash.
- **`upfront_invoice`.** A copy of the up-front invoice, issued by the founder outside the product (design choice 31).

**The DPA states:**
- **Term.** A fixed 90-day term with a weekly 30-minute check-in, ending "go paid or don't" (Slide 26).
- **After the term.** Paid means $79–99 a month, month-to-month, one-click cancel, no hidden per-feature fees (Slides 21, 26). STEP-42 builds billing by day 90; its provider is D12.
- **Up-front fee.** 10–20% of the intended annual price, invoiced outside the product. The DPA says what happens to the fee on a NO-GO, because STEP-22 settles it under this clause. The rule itself is the founder's: TBD — not in sources.
- **No AI training.** The restaurant's data is never used to train a model (Slide 21; matched by T8 in STEP-04).
- **Exit.** A 30-day CSV export of all flagged events after termination, and the same if we shut down, then deletion per contract, audit-logged (STEP-29). How long audit rows are kept after exit is D9.
- **Fact-based wording.** POS data only. Digests go to the owner only, state facts not conclusions, never suggest a wage deduction (L4), and are never the only basis for discipline or a firing (Slide 21; RK3). Putting this in the contract is a design choice.
- **The pass line**, below.

**The pass line states:**
- **Measure.** Voids + comps + discounts as a percent of net sales (sales after refunds), 30 days before and 60 days after (Slide 26). "Before" is the 30 days ending the day before pilot day one (design choice 17).
- **PASS** is a drop of at least 1 point. **FAIL** is a drop under 0.5 point, or the owner stops opening the digest.
- **Between 0.5 and 1 point (T11).** Exactly one stated outcome, agreed by both sides: TBD — not in sources.
- **How "stops opening the digest" is measured**, as D10 records it: a weekly check-in note, or a link-click count that the DPA discloses to the owner.
- **Both V1 variants**, written out before signing (RK2), under V-item branches below.

## V-item branches
- **V1 (dollar amount on cancelled orders).** If RETURNED: the measure applies as written. If NOT_RETURNED or PARTIAL: the substitute measure applies. Both sides agree it now (TBD — not in sources). It is built only from fields STEP-01 marked `CAN_RETURN` that don't depend on V1, and it uses the same PASS, FAIL and T11 lines unless the DPA says otherwise. STEP-20's `v_item: V1` result decides which variant applies; nobody chooses later.
- **V5 (comp detail).** If NOT_RETURNED or PARTIAL, comps can't be summed. Both variants say whether comps are dropped or replaced. This is our inference: Slide 26 names only void dollars.
- **V8 (30 days of history).** If NOT_RETURNED, there is no "before" figure, which is hard stop 2 in `docs/build/go-no-go-criteria.md`. The only way past it is a collect-first variant written into this DPA (the first 30 pilot days build the "before" figure, and the 90-day term starts after them), reviewed by counsel.

## Acceptance criteria
1. The signed DPA equals the version counsel reviewed (`dpa_approved: YES` in `docs/build/findings/counsel-t17a-answers.md`). Any change after review goes back to counsel.
2. The pass line holds both V1 variants, the T11 outcome and the D10 measure before anyone signs; a blank in any of them means not done. The owner and the founder both sign it.
3. The invoice amount is between 10% and 20% of twelve times the intended monthly price. It is issued outside the product.
4. No staff name or identifier appears anywhere. The repo, the evidence and the session hold only hashes, roles and dates.

## Human confirmation
"Founder: are `STEP-07/dpa`, `STEP-07/pass_line` and `STEP-07/upfront_invoice` saved in your evidence folder? Is the DPA the counsel-approved version, and does the pass line hold both V1 variants, the T11 outcome and the D10 measure?" Print AWAITING HUMAN CONFIRMATION and wait.

## Out of scope
Billing code (STEP-42), the pass-line measurement code (STEP-39), the CSV export (STEP-29), the no-go exit and fee settlement (STEP-22), the spike authorization (STEP-06).

## Gate
Exact, from `docs/build/status/STEP-07.json`. The founder runs it in their own terminal:
`python tools/check_artifact.py --step STEP-07 --label dpa --role owner && python tools/check_artifact.py --step STEP-07 --label pass_line --role owner && python tools/check_artifact.py --step STEP-07 --label upfront_invoice --role founder`

No gate test files (`docs/build/gates/STEP-07.txt`). `docs/build/evidence/STEP-07.md` holds three pasted blocks, each with the command and `--date`, `exit_code: 0`, `sha256: … label=<label>`, `role:` and `date:`.

## If the gate fails
Fix the artifact name or folder and re-run. If the owner won't sign, or a variant, the T11 outcome or the D10 measure is missing, set the status to `blocked` with `blocked_reason: dpa_not_signed` or `pass_line_incomplete`. STEP-33 and STEP-43 wait. After two failed attempts, restart in a fresh session with a narrower prompt.

## Prompt (paste into a fresh Claude Code session, run from an engineer's account)
```text
You are running STEP-07 "Design Partner Agreement and pass line signed" for TillOwl. Follow @CLAUDE.md throughout.
Start: git fetch && git rebase origin/main; confirm STEP-02 is "done" in docs/build/status/STEP-02.json (stop and say so if not); read git log -5; run CLAUDE.md's setup command; read @docs/build/steps/STEP-07-dpa-pass-line.md, @docs/build/findings/counsel-t17a-answers.md, @docs/build/findings/square-sandbox.md, @docs/build/go-no-go-criteria.md, and Slides 3, 17, 21, 24, 26, 28, 29, 30 in @docs/architecture-pack-part1.md and @docs/architecture-pack-part2.md.
This is a human step. Never read $PRIVATE_EVIDENCE_DIR, never run tools/check_artifact.py yourself, and never write a staff name anywhere.
1. Stop and tell the founder if dpa_approved is not YES, or if BUILD_PLAN §12 doesn't record D10 and D15 yet.
2. Print the checklist of DPA and pass-line clauses from the step file, including both V1 variants, the V5 and V8 notes, the T11 outcome, the D10 measure and the NO-GO fee rule. List the CAN_RETURN fields from the sandbox findings that a substitute measure may use.
3. Print the three commands for the founder's own terminal, with the D4 absolute path from BUILD_PLAN §1 written out (PRIVATE_EVIDENCE_DIR=<absolute path> python tools/check_artifact.py --step STEP-07 --label <dpa|pass_line|upfront_invoice> --role <owner|owner|founder> --date YYYY-MM-DD), then the human-confirmation line and AWAITING HUMAN CONFIRMATION; wait.
4. From the founder's pasted output only: write docs/build/evidence/STEP-07.md, set status "done", run python tools/check_evidence.py validate --step STEP-07 and show the command and its output, then open the PR with gh. Its description says the founder must approve and then re-run the founder-approval check.
Out of scope: billing, measurement, export and exit code; legal drafting.
Use a subagent to review the diff against this step file and report only gaps that affect correctness or the stated acceptance criteria.
```
