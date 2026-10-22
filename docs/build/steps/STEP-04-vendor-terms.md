# STEP-04 Vendor data terms: model no-training (T8) and email vendor (T5)

Track: human. Lane: vendor. Gate kind: human. Size: S/W.
Depends on: none (start on day one). Done requires: none.
Blocks: STEP-43 pilot-readiness gate. Production LLM calls (STEP-25's `TILLOWL_LLM_ENABLED`) stay off until T8 is resolved or D11 is recorded.
Sources: Slide 19–20 (LLM: "A vendor term that keeps restaurant data out of model training… TBD"; email: "Vendor, authentication and data terms: TBD"), Slide 21 (No AI training; least data to vendors), Slide 30 (T5, T8); BUILD_PLAN §1 (Resend), design choices 21–22; D11.

## Outcome
The current data terms of the model vendor (Anthropic) and the email vendor (Resend, an unverified candidate) are saved. `docs/build/findings/vendor-terms.md` records:
```
t5_vendor: Resend
t5_terms_url: https://...          t5_terms_date: YYYY-MM-DD
t5_uses_customer_content_for_other_purposes: NO | YES | UNCLEAR
t8_vendor: Anthropic
t8_terms_url: https://...          t8_terms_date: YYYY-MM-DD
t8_no_training_term: CONFIRMED | NOT_CONFIRMED
model_id_pinned: claude-haiku-5-5
```

## Acceptance criteria
1. Each `CONFIRMED` or `NO` rests on a quoted clause in the saved terms copy, not on a summary.
2. If `t8_no_training_term` is `NOT_CONFIRMED`, the founder records D11 (production digest runs template-only, LLM calls disabled). A founder-approved gate-change PR then swaps the second gate command to `--label t8_template_only --role founder`, and the artifact is the founder's signed D11 note.
3. If `t5_uses_customer_content_for_other_purposes` is `YES` or `UNCLEAR`, the founder picks another email vendor before STEP-26's delivery reaches production. Record it as a founder decision in BUILD_PLAN §12.

## Human confirmation
"Founder: are `STEP-04/terms_t5` and `STEP-04/terms_t8` (or `t8_template_only`) saved in your evidence folder, and what are the findings values?" Print AWAITING HUMAN CONFIRMATION and wait.

## Out of scope
The explanation service code (STEP-25); delivery code (STEP-26); SMS terms (STEP-03).

## Gate
Exact, from the status file. The founder runs it in their own terminal:
`python tools/check_artifact.py --step STEP-04 --label terms_t5 --role vendor && python tools/check_artifact.py --step STEP-04 --label terms_t8 --role vendor`

The evidence holds both pasted blocks; the last block also carries `sha256: <hex> label=findings`. One done PR holds the findings file, the evidence and the status; CI allows the step's `findings_path` in its done PR and checks its hash.

## If the gate fails
Fix the artifact name or folder and re-run. If the terms can't be obtained, set the status to `blocked` with `blocked_reason: t8_terms_unavailable` and raise D11 with the founder. Otherwise: revert to the last green commit; set the status to `blocked` with a `blocked_reason` that holds no names or values; after two failed attempts, restart in a fresh session with a narrower prompt.

## Prompt (paste into a fresh Claude Code session, run from an engineer's account)
```text
You are running STEP-04 "Vendor data terms (T5, T8)" for TillOwl. Follow @CLAUDE.md throughout.
Start: git fetch && git rebase origin/main; no depends_on; read git log -5; run CLAUDE.md's setup command; read @docs/build/steps/STEP-04-vendor-terms.md and Slides 19, 20, 21, 30 in @docs/architecture-pack-part2.md.
This is a human step. Never read $PRIVATE_EVIDENCE_DIR and never run tools/check_artifact.py yourself.
1. Use WebFetch to find Anthropic's and Resend's current official commercial or data-processing terms pages; print the URLs and the exact clauses that bear on training and data use, labelled unverified until the founder saves a copy.
2. Print both commands for the founder's own terminal, with the D4 absolute path from BUILD_PLAN §1 written out (PRIVATE_EVIDENCE_DIR=<path> python tools/check_artifact.py ... --date YYYY-MM-DD), then the human-confirmation line and AWAITING HUMAN CONFIRMATION; wait.
3. From the founder's reply only: write docs/build/findings/vendor-terms.md, write docs/build/evidence/STEP-04.md from the pasted output plus the findings sha256 line, set status "done", run python tools/check_evidence.py validate --step STEP-04 and show the output, then open one PR with gh holding the findings file, the evidence and the status (founder approves, then re-runs founder-approval). If T8 is NOT_CONFIRMED, stop and tell the founder D11 needs a gate-change PR first.
Out of scope: model or email code.
End: Use a subagent to review the diff against this step file and report only gaps that affect correctness or the stated acceptance criteria.
```
