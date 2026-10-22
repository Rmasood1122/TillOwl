# STEP-03 Twilio 10DLC registration and the owner's SMS opt-in (T6)

Track: human. Lane: vendor. Gate kind: human. Size: W (waits on Twilio and its carriers).
Depends on: none (start on day one; D15 names the registering entity). Done requires: none.
Blocks: STEP-43 pilot-readiness gate. SMS stays off in STEP-26 until this is done.
Sources: Slide 19–20 (Twilio: "number + 10DLC campaign"; credential type, approval time and limits TBD), Slide 30 (T6), Slide 22 (SMS ~$15 of the lean line); BUILD_PLAN design choice 20; D15.

## Outcome
- The 10DLC brand and campaign for the digest are approved.
- The owner's signed SMS opt-in (consent to receive the digest by text at their number) is on file.
- Twilio's data terms are saved.
- `docs/build/findings/twilio-10dlc.md` records, as codes and numbers only:
```
tendlc_status: APPROVED
approval_days: <n>                  (registration to approval; closes the T6 "approval time")
message_limit: <n per day> | TBD    (as stated in Twilio's approval or account; T6 "message limits")
credential_type: <API key | auth token | TBD>
terms_url: https://...              (Twilio terms page used)
terms_date: YYYY-MM-DD
login_codes_in_sms_allowed: YES | NO | UNCLEAR   (digests carry login codes)
```

## Acceptance criteria
1. The registration follows Twilio's current official 10DLC docs. Cite each URL in the findings; process details are unverified candidates until Twilio's approval confirms them.
2. The opt-in names the owner's number only. No staff number is ever registered or texted (Slide 21: "never a staff group chat").
3. Every findings line has a value or `TBD`. The step is not done while `tendlc_status` is not `APPROVED`.

## Human confirmation
"Founder: are `STEP-03/sms_optin`, `STEP-03/tendlc_approval` and `STEP-03/terms_t6` saved in your evidence folder, and what are the findings values?" Print AWAITING HUMAN CONFIRMATION and wait.

## Out of scope
Sending any SMS (STEP-26 stubs it; STEP-43 sends the first real one), the digest wording, the email vendor (STEP-04).

## Gate
Exact, from `docs/build/status/STEP-03.json`. The founder runs it in their own terminal:
`python tools/check_artifact.py --step STEP-03 --label sms_optin --role owner && python tools/check_artifact.py --step STEP-03 --label tendlc_approval --role vendor && python tools/check_artifact.py --step STEP-03 --label terms_t6 --role vendor`

`docs/build/evidence/STEP-03.md` holds the three pasted blocks. The last block also carries `sha256: <hex> label=findings` for the findings file. One done PR holds the findings file, the evidence and the status; CI allows the step's `findings_path` in its done PR and checks its hash.

## If the gate fails
Fix the artifact name or folder and re-run. If Twilio rejects the registration, set the status to `blocked` with `blocked_reason: tendlc_rejected` and resubmit. Email-only digests can still run on staging meanwhile. Otherwise: revert to the last green commit; set the status to `blocked` with a `blocked_reason` that holds no names or values; after two failed attempts, restart in a fresh session with a narrower prompt.

## Prompt (paste into a fresh Claude Code session, run from an engineer's account)
```text
You are running STEP-03 "Twilio 10DLC and the owner's SMS opt-in" for TillOwl. Follow @CLAUDE.md throughout.
Start: git fetch && git rebase origin/main; no depends_on; read git log -5; run CLAUDE.md's setup command; read @docs/build/steps/STEP-03-twilio-10dlc.md and Slides 19, 20, 22, 30 in @docs/architecture-pack-part2.md.
This is a human step. Never read $PRIVATE_EVIDENCE_DIR and never run tools/check_artifact.py yourself.
1. Use WebFetch on Twilio's official 10DLC registration docs and print a short checklist for the founder, citing each URL as an unverified candidate. Ask which legal entity registers (D15) if BUILD_PLAN §12 doesn't record it yet.
2. Print the three commands for the founder's own terminal, with the D4 absolute path from BUILD_PLAN §1 written out (PRIVATE_EVIDENCE_DIR=<path> python tools/check_artifact.py ... --date YYYY-MM-DD), then the human-confirmation line and AWAITING HUMAN CONFIRMATION; wait.
3. From the founder's reply only: write docs/build/findings/twilio-10dlc.md, write docs/build/evidence/STEP-03.md from the pasted output plus the findings sha256 line, set status "done", run python tools/check_evidence.py validate --step STEP-03 and show the output, then open one PR with gh holding the findings file, the evidence and the status (founder approves, then re-runs founder-approval).
Out of scope: sending SMS, digest wording, email vendor.
End: Use a subagent to review the diff against this step file and report only gaps that affect correctness or the stated acceptance criteria.
```
