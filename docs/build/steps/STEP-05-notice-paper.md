# STEP-05 §52-c*2 notice given, acknowledged on paper, posted (T16)

Track: human. Lane: legal. Gate kind: human. Size: W (waits on the owner and staff).
Depends on: STEP-02 counsel T17a (the notice text version counsel approved). Done requires: none.
Blocks: STEP-20 live spike, STEP-33 pilot onboarding, STEP-43 pilot-readiness gate.
Sources: Slide 3 (L1), Slide 21 (notice workflow 1–6, "who sees what"), Slide 26 ("§52-c*2 notices given, acknowledged and posted"), Slide 29 (RK9, TD5), Slide 30 (T16), ADR-006; BUILD_PLAN §1 (T16 = paper), design choices 13 and 16.

## Outcome
The owner has done the following:
1. Given the counsel-approved notice (`notice_text_version` from `docs/build/findings/counsel-t17a-answers.md`) in writing to every current staff member.
2. Collected signed paper acknowledgments. The restaurant keeps the originals; the founder keeps a scanned copy of the batch in `$PRIVATE_EVIDENCE_DIR/STEP-05/ack_batch.<ext>`.
3. Posted the notice where staff can see it, and photographed it with the date.
4. Told staff that nobody is punished just because data shows up (workflow step 6; RK9).

New hires get the notice at hire throughout the pilot. Their acknowledgments are entered later through STEP-27's screen.

## Acceptance criteria
1. Staff appear only as counts: signed, absent, refused. No staff name, initial or login enters the repo, the evidence or a Claude session.
2. Absent or refusing staff never block silently: their counts are in the evidence. If any staff haven't signed, the spike (STEP-20) may run only if `spike_with_unsigned_staff: ALLOWED` in counsel's answers. Otherwise STEP-20 waits.
3. The notice version given equals `notice_text_version` from counsel's answers.

## Human confirmation
"Founder: are `STEP-05/notice`, `STEP-05/ack_batch` and `STEP-05/posting` saved in your evidence folder? How many staff signed, were absent and refused? Did the owner give the nobody-is-punished briefing?" Print AWAITING HUMAN CONFIRMATION and wait.

## Out of scope
Entering acknowledgments into the console and mapping them to logins (STEP-27 builds the screen; STEP-33 enters them after GO). No software is needed for this step.

## Gate
Exact, from the status file. The founder runs it in their own terminal:
`python tools/check_artifact.py --step STEP-05 --label notice --role owner && python tools/check_artifact.py --step STEP-05 --label ack_batch --role staff && python tools/check_artifact.py --step STEP-05 --label posting --role owner`

The `ack_batch` run adds `--count <signed> --absent <n> --refused <n>`. `docs/build/evidence/STEP-05.md` holds the three pasted blocks: SHA-256, role, `count: … staff_signed/staff_absent/staff_refused`, and date.

## If the gate fails
Fix the artifact name or folder and re-run. If the owner hasn't given the briefing or posted the notice, the step is not done: set the status to `blocked` with `blocked_reason: notice_not_posted` or `briefing_pending`.

## Prompt (paste into a fresh Claude Code session, run from an engineer's account)
```text
You are running STEP-05 "§52-c*2 notice given, acknowledged on paper, posted" for TillOwl. Follow @CLAUDE.md throughout.
Start: git fetch && git rebase origin/main; confirm STEP-02 is "done" in docs/build/status/STEP-02.json (stop and say so if not); read git log -5; run CLAUDE.md's setup command; read @docs/build/steps/STEP-05-notice-paper.md, @docs/build/findings/counsel-t17a-answers.md, and Slides 3, 21, 26, 29, 30 in @docs/architecture-pack-part1.md and @docs/architecture-pack-part2.md.
This is a human step. Never read $PRIVATE_EVIDENCE_DIR, never run tools/check_artifact.py yourself, and never write a staff name anywhere.
1. Print the owner's checklist (notice version, signatures, posting photo, the nobody-is-punished briefing).
2. Print the three commands for the founder's own terminal, with the D4 absolute path from BUILD_PLAN §1 written out (the ack_batch one with --count, --absent, --refused and --date), then the human-confirmation line and AWAITING HUMAN CONFIRMATION; wait.
3. From the founder's pasted output only: write docs/build/evidence/STEP-05.md, set status "done", run python tools/check_evidence.py validate --step STEP-05 and show the output, then open the PR with gh (founder approves, then re-runs founder-approval). If any staff are unsigned and counsel's spike_with_unsigned_staff is NOT_ALLOWED, say clearly in the PR that STEP-20 must wait.
Out of scope: console entry, mapping to logins, any data access.
End: Use a subagent to review the diff against this step file and report only gaps that affect correctness or the stated acceptance criteria.
```
