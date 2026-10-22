# STEP-17 Provision the friend's tenant and owner two-factor

Track: build. Lane: platform. Gate kind: production_job. Size: S.
Depends on: STEP-06 Owner signs the spike authorization and support-access permission, STEP-13 Production environment, STEP-14 Provision our own production tenant (it freezes `provision_tenant --kind own|pilot`, built earlier in the console lane). Done requires: none.
Blocks: STEP-20 Run the read-only live spike.
Sources: Slide 11 (OWN, CON), Slides 17–18 (Owner user: "the only sign-in"; Q1 has 1 owner login; Q5 audit), Slide 21 (owner-only access with two-factor, no staff accounts, who sees what), Slide 24 (scenario 3), ADR-006; BUILD_PLAN §3, §7, design choices 4, 25, 29.

## Outcome
- **Tenant and owner.** Production tenant `pilot` and its one `owner_user` exist, created by `python -m tillowl.jobs.provision_tenant --kind pilot`. STEP-10 built that module and STEP-14 froze it; this step does not edit it. Creation is audit-logged.
- **Invite.** One owner invite email has gone to the friend's real address. The founder sets that address in the production secret store; it never appears in the repo, the session or the evidence. The owner follows the invite to the console and enrolls TOTP through STEP-10's flow, on their own phone.
- **Report job.** `tillowl/jobs/onboarding_report.py --tenant pilot --expect-2fa` runs through STEP-08's `run_job` wrapper and prints `count: N owners_2fa`, then `date: YYYY-MM-DD` and `exit_code: N`: 0 only when N is 1, otherwise 1.
  - This module is not gate-listed, so it stays editable: STEP-33 adds the default counts mode and STEP-34 adds `--history`.
  - Without `--expect-2fa`, it exits 2 for now.
- **No Square.** No Square call and no Square data. The owner connects Square only in STEP-20, under that step's own confirmation.

## Acceptance criteria
1. Given `tests/gates/step_17/test_owner_invite.py`, with the email sender stubbed (CI never sends), `provision_tenant --kind pilot` on the local test database:
   - creates exactly one `pilot` tenant and one `owner_user`;
   - sends exactly one invite, to the configured address;
   - stores the invite token only as a hash, makes it single-use (a second use fails) and makes it expire;
   - lets the invite do only one thing: TOTP enrollment of that owner (no second user, no staff account);
   - keeps the address and token out of stdout and audit rows;
   - puts no login code, POS data or staff data in the email.
   If the frozen `provision_tenant` misses any of these, don't edit it: set `blocked` with `blocked_reason: provision_pilot_invite_gap` and raise a gate-change PR on it.
2. Given `tests/gates/step_17/test_onboarding_report_2fa.py`, `--expect-2fa` exits 0 only when tenant `pilot` has exactly one `owner_user` with a confirmed TOTP enrollment. This is tested for every combination of 0, 1 or 2 owner users, each enrolled or not. An enrolled owner seeded in tenant `own` never changes the result (row-level security, scenario 3).
3. Output is only `count: N owners_2fa`, then `date: YYYY-MM-DD`, then `exit_code: N`: no address, user id or tenant name.
4. In this mode the job imports no Square client and reads no POS table. The test fails if `tillowl.square` is imported or any HTTP call is made.

## Human confirmation
Before the founder launches `provision_tenant`: "Founder: is STEP-06's signed authorization on file? Has the owner agreed to get the invite email? Is their address set in the production secret store (don't paste it here)?" Print AWAITING HUMAN CONFIRMATION and wait.

Before `onboarding_report`: "Founder: has the owner opened the invite and enrolled TOTP on their own phone?" Print AWAITING HUMAN CONFIRMATION and wait.

## Out of scope
- Connecting Square, or any Square read (STEP-20).
- Shift windows and acknowledgments (STEP-28, STEP-33).
- Editing `provision_tenant.py`.
- Staff accounts, which never exist.
- The default and `--history` modes of `onboarding_report` (STEP-33, STEP-34).

## Gate
`python -m tillowl.jobs.provision_tenant --kind pilot && python -m tillowl.jobs.onboarding_report --tenant pilot --expect-2fa` (exact, from `docs/build/status/STEP-17.json`). Gate files: `docs/build/gates/STEP-17.txt`.

The founder launches each command as a Render one-off job from their own terminal (`render jobs create`; unverified candidate, BUILD_PLAN §10). `docs/build/evidence/STEP-17.md` holds two blocks, each the job's pasted output (ending `date:` then `exit_code: 0`) plus its `job_id:`:
- `provision_tenant`: `count: 1 tenants`;
- `onboarding_report`: `count: 1 owners_2fa`.

## If the gate fails
- Revert to the last green commit.
- Set the status to `blocked` with a `blocked_reason` code, for example `owner_2fa_missing`. No address or name.
- After two failed attempts, restart in a fresh session with a narrower prompt.
- Never create a second pilot tenant. If the invite expired, re-issue it only through the frozen `provision_tenant`; if it can't re-issue, that needs a gate-change PR on it.

## Prompt (paste into a fresh Claude Code session)
```text
You are running STEP-17 "Provision the friend's tenant and owner two-factor" for TillOwl. Follow @CLAUDE.md throughout.
Start:
1. git fetch && git rebase origin/main
2. Confirm STEP-06 and STEP-13 are "done" in their status files, and that STEP-14 (which froze the provision_tenant module STEP-10 built) is done too. If not, stop and say which. Read git log -5.
3. Run CLAUDE.md's setup command.
4. Read @docs/build/steps/STEP-17-provision-pilot-tenant.md, @tillowl/jobs/provision_tenant.py, the STEP-10 sign-in code under @tillowl/console/, and Slides 11, 17, 18, 21, 24 in @docs/architecture-pack-part1.md and @docs/architecture-pack-part2.md.
You never hold production credentials, never use the Render CLI, and never see or write the owner's address.
Body, test first:
5. Set docs/build/status/STEP-17.json status to "in_progress".
6. Write tests/gates/step_17/test_owner_invite.py and tests/gates/step_17/test_onboarding_report_2fa.py to acceptance criteria 1–4. Run them; they fail. Print RED TEST (intentional) if you stop here.
7. Build tillowl/jobs/onboarding_report.py (--expect-2fa only) on STEP-08's run_job wrapper, so its output ends with date: then exit_code:. Do not edit tillowl/jobs/provision_tenant.py. If criterion 1 fails against it, follow "If the gate fails".
8. Run CLAUDE.md's test command and show its output. Commit, then open the step PR with gh (status in_progress). It merges on review.
Run phase (after the step PR merges):
9. Print the first human-confirmation line and AWAITING HUMAN CONFIRMATION; wait.
10. Print for the founder's own terminal: deploy the release by hand, then
    render jobs create <production service id> --start-command "python -m tillowl.jobs.provision_tenant --kind pilot"
    (unverified candidate). Ask for the job id, exit code and output; wait.
11. Print the second human-confirmation line and AWAITING HUMAN CONFIRMATION; wait. Then print the same render command with --start-command "python -m tillowl.jobs.onboarding_report --tenant pilot --expect-2fa". Ask for the job id, exit code and output; wait.
Evidence and done PR:
12. From the pasted output only, write docs/build/evidence/STEP-17.md (two blocks: each pasted output plus its job_id) and set the status to "done".
13. Run python tools/check_evidence.py validate --step STEP-17 and show its output. Open the done PR with gh; the founder approves, then re-runs founder-approval. Never claim success without the pasted output.
Out of scope: Square, shift windows, acknowledgments, editing provision_tenant, staff accounts.
Use a subagent to review the diff against this step file and report only gaps that affect correctness or the stated acceptance criteria.
```
