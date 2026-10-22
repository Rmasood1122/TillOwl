# STEP-18 Go/no-go criteria accepted

Track: human. Lane: gate. Gate kind: human. Size: S.
Depends on: none. Done requires: STEP-01 Square-sandbox spike, because the criteria use its findings.
Blocks: STEP-20 Run the read-only live spike.
Sources: Slide 12 (fallback sentence), Slide 26 (pass line, Square caveat, before day one), Slide 29 (RK1 "stop if the signal is too thin", RK2), Slide 30 (V1–V8 and the rule), ADR-004; BUILD_PLAN design choices 10, 11, 12; D8, D16.

## Outcome
`docs/build/go-no-go-criteria.md` is accepted by the founder and merged on branch `gate-change/step-18-accept-criteria`, because the file is G1-protected. In the accepted file:
- the §3 RK1 thresholds (D16) are the founder's own numbers, or the proposed ones kept on purpose;
- the two founder options in §1 are each chosen or struck:
  - hard stop 2: a collect-first V8 variant, only if the signed DPA already holds it;
  - hard stop 4: a shift-level-only digest, only with the owner's written agreement;
- every occurrence of the word DRAFT is gone, including the title, the status line and the sentence that tells the founder to remove it.

The same PR adds `docs/build/evidence/STEP-18.md` and sets the status to `done`. STEP-21 later refuses to record a decision if the file's hash differs from this evidence.

## Acceptance criteria
1. `python tools/check_evidence.py criteria` exits 0 on the branch. It refuses while the whole word DRAFT appears anywhere in the file. It prints `sha256: … label=criteria`, `role: founder` and `date:`.
2. The criteria are decided before any live data exists: this step is done before STEP-20 starts, and nothing in the file depends on the friend's account.
3. Every number in §3 is marked as the founder's choice. None is presented as coming from the pack or R2.
4. §2 keeps both fallback sentences word for word:
   - with the login clause, "9 checks cancelled during shift Y (opened by login X)", used when V2 is RETURNED;
   - without it, "9 checks cancelled during shift Y", used when V2 is NOT_RETURNED or PARTIAL.
   PARTIAL still counts as NOT_RETURNED.
5. Where STEP-01's findings mark an item `NOT_OBSERVABLE_IN_SANDBOX` (likely V3 and V6), the criteria say what happens if the live spike also fails it. The default is "left out", per §2.

## Human confirmation
"Founder: what are your D16 thresholds (orders, events per metric, distinct logins)? Do you keep or strike the hard-stop-2 and hard-stop-4 options? Edit the file on this branch yourself, or reply with the values for me to apply. Then run the command below in your own terminal and paste its output." Print AWAITING HUMAN CONFIRMATION and wait.

## Out of scope
- Running the spike (STEP-20).
- Recording GO or NO-GO (STEP-21).
- Changing the criteria after STEP-20 has run: STEP-21's hash check refuses that, and it would defeat the point of deciding first.
- Any code.

## Gate
`python tools/check_evidence.py criteria` (exact, from `docs/build/status/STEP-18.json`). No gate test files (`docs/build/gates/STEP-18.txt`). The founder runs it in their own terminal, from a checkout of the branch.

`docs/build/evidence/STEP-18.md` holds one block, pasted as printed:
- `command: python tools/check_evidence.py criteria`
- `exit_code: 0`
- `sha256: <hex> label=criteria`
- `role: founder`
- `date:`

## If the gate fails
- If the tool reports DRAFT still present, remove the remaining occurrence and re-run.
- If CI says STEP-01 isn't done, the PR waits; it can't merge before then (done_requires).
- Revert to the last green commit. Set `blocked` with a `blocked_reason` code, for example `criteria_thresholds_pending`. After two failed attempts, restart in a fresh session with a narrower prompt.

## Prompt (paste into a fresh Claude Code session, run from an engineer's account)
```text
You are running STEP-18 "Go/no-go criteria accepted" for TillOwl. Follow @CLAUDE.md throughout.
Start:
1. git fetch && git rebase origin/main
2. This step has no depends_on. Check whether STEP-01 is "done" in docs/build/status/STEP-01.json; it must be done before the PR merges. Read git log -5.
3. Run CLAUDE.md's setup command.
4. Read @docs/build/steps/STEP-18-go-no-go-criteria.md, @docs/build/go-no-go-criteria.md, @docs/build/findings/square-sandbox.md (if it exists yet), and Slides 12, 26, 29, 30 in @docs/architecture-pack-part1.md and @docs/architecture-pack-part2.md.
This is a human step. Never read $PRIVATE_EVIDENCE_DIR and never run tools/check_artifact.py.
5. Run: git switch -c gate-change/step-18-accept-criteria
6. Print a short checklist for the founder:
   - the §3 thresholds, with the proposed numbers;
   - the hard-stop-2 and hard-stop-4 options;
   - any STEP-01 v_shape that is NOT_OBSERVABLE_IN_SANDBOX or CANNOT_RETURN.
   Then print the human-confirmation line and AWAITING HUMAN CONFIRMATION; wait.
7. Apply only the founder's edits (or check the founder's own edits), then run grep -nw DRAFT docs/build/go-no-go-criteria.md and show that it prints nothing.
8. Print for the founder's own terminal, run from a checkout of this branch:
   python tools/check_evidence.py criteria
   Print AWAITING HUMAN CONFIRMATION; wait for the pasted output.
9. From the pasted output only, write docs/build/evidence/STEP-18.md and set docs/build/status/STEP-18.json status to "done". Run python tools/check_evidence.py validate --step STEP-18 and show its output.
10. Commit the criteria, evidence and status together and open one PR with gh from this branch. Its description says: gate-change PR; the founder approves, then re-runs founder-approval; it can't merge until STEP-01 is done.
Out of scope: running the spike, recording the decision, any code.
Use a subagent to review the diff against this step file and report only gaps that affect correctness or the stated acceptance criteria.
```
