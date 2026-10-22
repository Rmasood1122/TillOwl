# STEP-20 Run the read-only live spike on the friend's account (closes V1–V8)

Track: build. Lane: connector. Gate kind: production_job. Size: S.
Depends on: STEP-02 Counsel review T17a, STEP-05 Notice given, acknowledged on paper and posted, STEP-06 Owner signs the spike authorization, STEP-11 Square OAuth connect, STEP-13 Production environment, STEP-15 T1 resolved, STEP-16 Production OAuth check, STEP-17 Provision the friend's tenant, STEP-18 Go/no-go criteria accepted, STEP-19 Live-spike job code. Done requires: none.
Blocks: STEP-21 Go/no-go decision recorded, STEP-43 Pilot-readiness gate.
Sources: Slide 21 (OAuth only; notice before monitoring), Slide 26 ("Every 'verify on live account' item tested on the friend's account"), Slide 29 (RK1), Slide 30 (V1–V8; results to the audit log), ADR-003, ADR-004, ADR-006; BUILD_PLAN design choices 9, 10, 19, 25, 29; D7, D8.

## Outcome
- **Connected.** The owner connected Square to tenant `pilot` in the production console, through the consent screen. No personal token was used.
- **Jobs run.** The founder ran `square_live_report --tenant pilot --check` and `verify_deleted --tenant pilot --scope spike` as one-off jobs on the production host. Both exited 0.
- **Findings.** `docs/build/findings/square-fields.md` holds only the `v_item:`, `field:` and `count:` lines that job printed. No values, no names.
- **Audit log.** Every V-item result is in the audit log. The spike kept no per-login rows and no values, and `verify_deleted` proved zero spike rows remain.
- **Evidence.** The evidence records `backup_expires` and `oauth_connection: kept|revoked` (D7).
- **If revoked.** STEP-33 starts with the owner reconnecting, under human confirmation.

## Acceptance criteria
1. Every `depends_on` step is done. If STEP-05's evidence shows any `staff_absent` or `staff_refused` above 0, `docs/build/findings/counsel-t17a-answers.md` must say `spike_with_unsigned_staff: ALLOWED`; otherwise stop.
2. The findings file is exactly the job's printed `v_item:`, `field:` and `count:` lines, in order. It has 8 top-level `v_item:` lines and `count: 8 v_items`, plus any sub-field lines.
3. The evidence carries:
   - `sha256: … label=findings`, which CI recomputes;
   - each job's `job_id`;
   - `backup_expires`;
   - `oauth_connection`.
   It holds no free text and no identifiers.
4. `backup_expires` is no later than the deletion date plus the 14-day cap in the owner's authorization.
5. PARTIAL is recorded as PARTIAL, and it counts as NOT_RETURNED for digests (design choice 10).

## V-item branches
This step records the results; STEP-21 judges them against the accepted criteria. Every later step reads them from the findings file through `tillowl/config.py` `V_ITEMS`.
- **V1:** If RETURNED, the pass line is measured in dollars as written. If NOT_RETURNED or PARTIAL, no dollar amounts are shown, and the pass line uses the DPA's substitute (hard stop 3 if none is signed).
- **V2:** If RETURNED, the digest says "9 checks cancelled during shift Y (opened by login X)". If NOT_RETURNED or PARTIAL, it says "9 checks cancelled during shift Y". A sub-field that passes alone (for example `V2.opened_by`) stands on its own line.
- **V3:** If RETURNED, item-void counts are shown per login and shift. If NOT_RETURNED or PARTIAL, they are left out.
- **V4:** If RETURNED, "approved by code Y" is added. If NOT_RETURNED or PARTIAL, it is left out.
- **V5:** If RETURNED, comp counts and amounts are shown per login and shift. If NOT_RETURNED or PARTIAL, they are left out.
- **V6:** If RETURNED, no-sale counts are shown per login and shift. If NOT_RETURNED or PARTIAL, they are left out.
- **V7:** If RETURNED, discounts and refunds are shown per login and shift window. If NOT_RETURNED or PARTIAL, they are shown per shift window only, with no login named. If V2 also fails, hard stop 4 applies.
- **V8:** If RETURNED, baselines start from STEP-34's history pull. If NOT_RETURNED or PARTIAL, hard stop 2 applies.

## Human confirmation
Before the owner connects: "Founder: are the owner's signed authorization (STEP-06) and the posted notice (STEP-05) on file? Is D7 set as `SPIKE_OAUTH_AFTER`, and `BACKUP_RETENTION_DAYS` (≤ 14), on the production service environment, where `tillowl/config.py` reads them? Is `TILLOWL_HMAC_KEY` in the secret store? Is the release with STEP-19's code deployed by you? If so, have the owner sign in to the production console with TOTP, click Connect Square, approve the consent screen, and tell me 'connected'." Print AWAITING HUMAN CONFIRMATION and wait.

## Out of scope
- Keeping any Square data after the spike.
- The roster read and the history pull (STEP-33, STEP-34).
- Any rule, digest or decision code.
- Re-running against the live account without the owner's OK.

## Gate
`python -m tillowl.jobs.square_live_report --tenant pilot --check && python -m tillowl.jobs.verify_deleted --tenant pilot --scope spike` (exact, from `docs/build/status/STEP-20.json`). Gate files: `docs/build/gates/STEP-20.txt` (`tillowl/jobs/square_live_report.py`, `tillowl/jobs/verify_deleted.py` and the report logic `tillowl/square/live_report.py`), all frozen once this step is done; STEP-22 reuses `verify_deleted --scope tenant` unchanged.

The founder launches each command with `render jobs create` from their own terminal (unverified candidate, BUILD_PLAN §10). `docs/build/evidence/STEP-20.md` holds two blocks, each the job's pasted output (it ends `date:` then `exit_code: 0`, via STEP-08's `run_job`) plus its `job_id:`:
- `square_live_report`: its `v_item:`, `field:` and `count:` lines and `oauth_connection:`, plus `sha256: <hex> label=findings` (from `sha256sum docs/build/findings/square-fields.md`);
- `verify_deleted`: `count: 0 rows_remaining` and `backup_expires:`.

## If the gate fails
- Never retry against the live account without the owner's OK.
- Revert to the last green commit.
- Set `blocked` with a code such as `v_item_missing_V6` or `rows_remaining`. No values.
- After two failed attempts, restart in a fresh session with a narrower prompt.
- If `verify_deleted` exits 1, keep the status blocked until a reviewed fix deletes the rows and the job is re-run with the owner's OK.

## Prompt (paste into a fresh Claude Code session)
```text
You are running STEP-20 "Run the read-only live spike" for TillOwl. Follow @CLAUDE.md throughout.
Start:
1. git fetch && git rebase origin/main
2. Confirm STEP-02, 05, 06, 11, 13, 15, 16, 17, 18 and 19 are "done" in their status files; if not, stop and say which. Then check acceptance criterion 1 against @docs/build/evidence/STEP-05.md and @docs/build/findings/counsel-t17a-answers.md. Read git log -5.
3. Run CLAUDE.md's setup command.
4. Read @docs/build/steps/STEP-20-live-spike-run.md, @docs/build/go-no-go-criteria.md, and Slides 21, 26, 29, 30 in @docs/architecture-pack-part2.md.
You never hold production credentials, never use the Render CLI, and never see a token, name or value.
5. Set docs/build/status/STEP-20.json status to "in_progress"; commit it alone and open the step PR with gh (it merges on review). Print the human-confirmation line and AWAITING HUMAN CONFIRMATION; wait.
6. Print for the founder's own terminal:
   render jobs create <production service id> --start-command "python -m tillowl.jobs.square_live_report --tenant pilot --check"
   (unverified candidate). Ask for the job id, exit code and output; wait. If the exit code isn't 0, stop: follow "If the gate fails" and do not ask for a re-run without the owner's OK.
7. Print the same command with --start-command "python -m tillowl.jobs.verify_deleted --tenant pilot --scope spike". Ask for the job id, exit code and output; wait.
Done PR (one commit on top of main holding only the findings, the evidence and the status; CI hash-checks the findings):
8. From the pasted output only, write docs/build/findings/square-fields.md (the v_item, field and count lines, in order); run sha256sum on it and show the output. Write docs/build/evidence/STEP-20.md (two blocks, per the Gate section) and set the status to "done".
9. Run python tools/check_evidence.py validate --step STEP-20 and show its output. Open the PR with gh; the founder approves, then re-runs founder-approval. Say in it whether oauth_connection is kept or revoked; if revoked, STEP-33 starts with the owner reconnecting.
Out of scope: keeping Square data, roster read, history pull, rules, digests, the decision.
Use a subagent to review the diff against this step file and report only gaps that affect correctness or the stated acceptance criteria.
```
