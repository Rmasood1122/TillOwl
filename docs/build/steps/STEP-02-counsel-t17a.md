# STEP-02 Counsel review T17a (notice, spike authorization, DPA, pre-notice history)

Track: human. Lane: legal. Gate kind: human. Size: W (waits on counsel).
Depends on: none (start on day one). Done requires: STEP-01 Square-sandbox spike, because the authorization must name the real scope names.
Blocks: STEP-05 notice, STEP-06 spike authorization, STEP-07 DPA, STEP-20 live spike.
Sources: Slide 21 (notice workflow, "Have NY employment counsel review…: TBD"), Slide 26 (before day one), Slide 30 (T17), Slide 3 (L1, L4, L5), ADR-006; BUILD_PLAN §11 items 8, 9, 14, 15; D15.

## Outcome
NY employment counsel's signed written review is on file, and `docs/build/findings/counsel-t17a-answers.md` records counsel's conclusions as codes only (no names, no advice text):
```
pos_logs_are_monitoring_52c: YES | NO | UNCLEAR   (the notice is given either way)
notice_text_version: <n>                          (the version counsel approved)
authorization_approved: YES | NO
roster_read_scope_approved: YES | NO
support_access_permission_approved: YES | NO
dpa_approved: YES | NO
pre_notice_history: PER_LOGIN_ALLOWED | TOTALS_ONLY
spike_with_unsigned_staff: ALLOWED | NOT_ALLOWED
audit_retention_after_exit_days: <n> | TBD          (input to D9)
```
STEP-20 (spike), STEP-31 and STEP-34 (ingest and history) read these codes.

## What the founder sends counsel (drafted by the founder on day one, not by this step)
1. **The §52-c*2 notice text, with a version number.** Notice at hire, acknowledgment, posting. It says nobody is punished just because data shows up (Slide 21, workflow step 6).
2. **The owner's spike authorization:**
   - the read-only scopes from `docs/build/findings/square-sandbox.md`, including the roster-read scope (design choice 14);
   - counts only, with logins hashed with HMAC in memory;
   - a deletion check;
   - a maximum backup and PITR window of **14 days**;
   - the owner's written permission for vendor support access, so the founder can enter paper acknowledgments (design choice 13).
3. **The Design Partner Agreement (DPA)** — a Design Partner Agreement, not a data processing agreement:
   - fixed 90-day term;
   - 10–20% of the intended annual price up front;
   - no AI training on the restaurant's data;
   - a 30-day CSV export of all flagged events after termination, the same if we shut down, then deletion per contract;
   - the pass line with both V1 variants and the T11 rule for a 0.5–1 point drop (RK2).
4. **The questions behind each code above.** That includes whether POS history from before the notice may feed per-login baselines, or only restaurant totals.

## Acceptance criteria
1. Every code line above has a value; any `NO` is followed by a revised draft and a second review before this step is done.
2. The findings file holds only the code lines, and no names, quotes or advice text.
3. The signed review copy sits at `$PRIVATE_EVIDENCE_DIR/STEP-02/counsel_t17a.<ext>`. The owner and counsel keep the originals.

## Human confirmation
"Founder: is counsel's signed review saved as `STEP-02/counsel_t17a.<ext>` in your evidence folder, and what are counsel's answers to each code line?" Print AWAITING HUMAN CONFIRMATION and wait.

## Out of scope
Drafting legal advice; the digest templates (that's T17b, STEP-40); signing anything (STEP-05 to STEP-07).

## Gate
`python tools/check_artifact.py --step STEP-02 --label counsel_t17a --role counsel`. The founder runs it in their own terminal. No gate test files (see `docs/build/gates/STEP-02.txt`).

`docs/build/evidence/STEP-02.md` holds:
- the pasted block (command with `--date`, `exit_code: 0`, `sha256: … label=counsel_t17a`, `role: counsel`, `date:`);
- then, in the same block, `sha256: <hex> label=findings` from `sha256sum docs/build/findings/counsel-t17a-answers.md`.

One done PR holds the findings file, the evidence and the status; CI allows a step's `findings_path` in its done PR and checks its hash.

## If the gate fails
`check_artifact.py` names the problem without paths: fix the file name or folder and re-run. Never move the copy into the repo. If counsel won't sign off, set the status to `blocked` with the reason as a code (for example `dpa_approved: NO`). The spike can't run until this is done. Otherwise: revert to the last green commit; set the status to `blocked` with a `blocked_reason` that holds no names or values; after two failed attempts, restart in a fresh session with a narrower prompt.

## Prompt (paste into a fresh Claude Code session, run from an engineer's account)
```text
You are running STEP-02 "Counsel review T17a" for TillOwl. Follow @CLAUDE.md throughout.
Start: git fetch && git rebase origin/main; this step has no depends_on; read git log -5; run CLAUDE.md's setup command; read @docs/build/steps/STEP-02-counsel-t17a.md and Slides 3, 21, 26, 30 in @docs/architecture-pack-part1.md and @docs/architecture-pack-part2.md.
This is a human step. Never read $PRIVATE_EVIDENCE_DIR and never run tools/check_artifact.py yourself.
1. Print the "What the founder sends counsel" checklist, filling the scope names from @docs/build/findings/square-sandbox.md (STEP-01 must be done before the done PR merges).
2. Print the command for the founder's own terminal, with the D4 absolute path from BUILD_PLAN §1 written out:
   PRIVATE_EVIDENCE_DIR=<absolute path> python tools/check_artifact.py --step STEP-02 --label counsel_t17a --role counsel --date YYYY-MM-DD
   Then print the human-confirmation line and AWAITING HUMAN CONFIRMATION; wait.
3. From the founder's reply only: write docs/build/findings/counsel-t17a-answers.md (code lines only), write docs/build/evidence/STEP-02.md from the pasted output plus the findings sha256 line, set status "done", run python tools/check_evidence.py validate --step STEP-02 and show the output, then open one PR with gh holding the findings file, the evidence and the status (CI hash-checks the findings). Its description says the founder must approve and then re-run the founder-approval check.
Out of scope: legal drafting, templates, signatures.
End: Use a subagent to review the diff against this step file and report only gaps that affect correctness or the stated acceptance criteria.
```
