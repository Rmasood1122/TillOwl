# STEP-06 Owner signs the spike authorization and support-access permission

Track: human. Lane: legal. Gate kind: human. Size: W (waits on the owner).
Depends on: STEP-02 Counsel review T17a (codes `authorization_approved: YES` and `support_access_permission_approved: YES`). Done requires: none. D7 (keep or revoke the OAuth connection after the spike) must be recorded in BUILD_PLAN §12 before the owner signs, because the text states it.
Blocks: STEP-17 provision the friend's tenant, STEP-20 run the read-only live spike.
Sources: Slide 3 (P3 read-only, T1), Slide 21 (encrypted OAuth tokens; "Us (vendor): support access only when the owner allows it, and every access is in the audit log"), Slide 26 (before day one), Slide 30 (V1–V8 on the friend's account), ADR-003, ADR-004; BUILD_PLAN §1 (14-day backup cap, T16 paper, T14), design choices 9, 13, 14, 19, 28; D7, D15.

## Outcome
Two documents the owner signed, each the exact text counsel approved under T17a. The founder keeps copies at `$PRIVATE_EVIDENCE_DIR/STEP-06/authorization.<ext>` and `$PRIVATE_EVIDENCE_DIR/STEP-06/support_permission.<ext>`; the owner keeps the originals. The founder drafts both on day one as inputs to T17a, not in this step.

**1. `authorization`: the owner's written authorization for the read-only live spike.** It states:
- **Scopes.** Every `scope:` line in `docs/build/findings/square-sandbox.md`, by name, and no others. That includes the team-member (roster-read) scope, which is requested at first connect but used only after GO and a signed DPA, and only to map acknowledgments to logins (design choice 14).
- **What is kept.** Field names, types and counts only. Where counting distinct logins needs identifiers, they are hashed with HMAC in memory, with a key from the host's secret store, and only the count is kept. No per-login rows and no values (design choice 9).
- **Where it runs.** A one-off job on the production host, so the token is never decrypted on a laptop. Nothing is written to the POS (P3).
- **Deletion.** The spike ends with `verify_deleted`, which proves the spike data is gone from the live database; the deletion date is audit-logged.
- **Backups.** Backups and point-in-time recovery keep the data until they expire, **at most 14 days** after deletion. The date the last backup holding spike data expires is recorded (`backup_expires:` in STEP-20's evidence) and reported to the owner.
- **The OAuth connection after the spike**, as D7 records it: either kept, with the production refresh job keeping it alive (proposed, design choice 19), or revoked. Either way the owner may revoke it in Square at any time.
- **Audit.** Each V-item result goes into the audit log (Slide 30 rule).

**2. `support_permission`: the owner's written permission for vendor support access** (design choice 13; Slide 21 "who sees what"). It allows the founder to:
- enter the signed paper acknowledgments and map each one to a Square login (STEP-33, after GO);
- enter the shift windows if the owner can't (BUILD_PLAN §1, T14).

The founder acts only through the console's time-boxed support-access grant, which the owner gives and can end (STEP-27). Every access is audit-logged.

## Acceptance criteria
1. Each signed text equals the version counsel reviewed: `authorization_approved: YES` and `support_access_permission_approved: YES` in `docs/build/findings/counsel-t17a-answers.md`. Any change after review goes back to counsel before signing.
2. The scope list in the authorization equals the `scope:` lines in the sandbox findings exactly. STEP-11 requests exactly that list at connect, so no scope reaches the friend's account that counsel and the owner didn't see.
3. The 14-day cap is at least as long as the production database's backup and PITR retention. STEP-13 keeps the database inside it (Render Pro PITR "Past 7 days" is an unverified candidate until STEP-13).
4. The OAuth clause matches D7 as recorded in BUILD_PLAN §12.
5. The owner signs before any Square data is read from the friend's account. D15 names the legal entity on our side.
6. No staff name, login or identifier enters the repo, the evidence or a session; they hold only hashes, roles and dates.

## Human confirmation
"Founder: are `STEP-06/authorization` and `STEP-06/support_permission` saved in your evidence folder, are both the counsel-approved versions, is D7 recorded, and does the authorization's OAuth clause match it?" Print AWAITING HUMAN CONFIRMATION and wait.

## Out of scope
Connecting to the friend's Square (STEP-20 runs the spike; STEP-17 provisions the tenant). The DPA and pass line (STEP-07). The support-access screen (STEP-27). Entering acknowledgments (STEP-33).

## Gate
Exact, from `docs/build/status/STEP-06.json`. The founder runs it in their own terminal:
`python tools/check_artifact.py --step STEP-06 --label authorization --role owner && python tools/check_artifact.py --step STEP-06 --label support_permission --role owner`

No gate test files (`docs/build/gates/STEP-06.txt`). `docs/build/evidence/STEP-06.md` holds two pasted blocks. Each has:
- the command with `--date`;
- `exit_code: 0`;
- `sha256: … label=authorization` (or `label=support_permission`);
- `role: owner`;
- `date:`.

## If the gate fails
Fix the artifact name or folder and re-run; never move a copy into the repo. If the owner won't sign, or counsel answered `NO`, set the status to `blocked` with `blocked_reason: authorization_not_signed` (or `support_permission_not_signed`). STEP-17 and STEP-20 wait, and nobody connects to the friend's account. After two failed attempts, restart in a fresh session with a narrower prompt.

## Prompt (paste into a fresh Claude Code session, run from an engineer's account)
```text
You are running STEP-06 "Owner signs the spike authorization and support-access permission" for TillOwl. Follow @CLAUDE.md throughout.
Start: git fetch && git rebase origin/main; confirm STEP-02 is "done" in docs/build/status/STEP-02.json (stop and say so if not); read git log -5; run CLAUDE.md's setup command; read @docs/build/steps/STEP-06-spike-authorization.md, @docs/build/findings/square-sandbox.md, @docs/build/findings/counsel-t17a-answers.md, and Slides 3, 21, 26, 30 in @docs/architecture-pack-part1.md and @docs/architecture-pack-part2.md.
This is a human step. Never read $PRIVATE_EVIDENCE_DIR, never run tools/check_artifact.py yourself, and never write a staff name anywhere.
1. Stop and tell the founder if authorization_approved or support_access_permission_approved is not YES, or if BUILD_PLAN §12 doesn't record D7 yet.
2. Print the owner's checklist: each clause of the authorization from the step file, with the scope names copied from the sandbox findings, and the support-permission clauses.
3. Print both commands for the founder's own terminal, with the D4 absolute path from BUILD_PLAN §1 written out:
   PRIVATE_EVIDENCE_DIR=<absolute path> python tools/check_artifact.py --step STEP-06 --label authorization --role owner --date YYYY-MM-DD
   PRIVATE_EVIDENCE_DIR=<absolute path> python tools/check_artifact.py --step STEP-06 --label support_permission --role owner --date YYYY-MM-DD
   Then print the human-confirmation line and AWAITING HUMAN CONFIRMATION; wait.
4. From the founder's pasted output only: write docs/build/evidence/STEP-06.md, set status "done", run python tools/check_evidence.py validate --step STEP-06 and show the command and its output, then open the PR with gh. Its description says the founder must approve and then re-run the founder-approval check.
Out of scope: any Square connection, the DPA, console code, acknowledgment entry.
Use a subagent to review the diff against this step file and report only gaps that affect correctness or the stated acceptance criteria.
```
