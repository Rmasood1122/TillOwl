# STEP-14 Provision our own production tenant (`provision_tenant --kind own|pilot`)

Track: build. Lane: platform. Gate kind: production_job. Size: S.
Depends on: STEP-13 production environment. Done requires: none.
Blocks: STEP-17 provision the friend's tenant (reuses `--kind pilot`), STEP-16 production OAuth check on our own Square account. STEP-17 reuses `--kind pilot` from this module without editing it.
Sources: Slides 15–18 (TEN, OWU, Q1 "has 1 owner login", R1, AUD, Q5), Slide 21 (owner-only access, audit log), Slide 25 (ADR-006, ADR-007); BUILD_PLAN §7 (jobs, `--tenant own|pilot`), design choices 4, 30.

## Outcome
`tillowl/jobs/provision_tenant.py` implements **both** kinds now, because the module is frozen when this step is done. Only `--kind own` runs in this step.
- **Tenant.** `--kind own` creates our own tenant for our Square seller; `--kind pilot` creates the friend's.
  - The `--tenant own|pilot` handle later jobs use is stored as `tenant.kind`, at most one active tenant per kind.
  - If STEP-08's schema lacks the column, add a migration that touches no RLS, policy, grant or role (design choice 33).
- **Owner user.** Each run creates the tenant's single owner user (Q1) in the `invited` state that STEP-10's TOTP enrollment accepts.
  - The owner's address comes from the production secret store: `TILLOWL_OWNER_EMAIL_OWN` for our own tenant, `TILLOWL_OWNER_EMAIL_PILOT` for the friend's.
  - The job emails that address one single-use enrollment link that expires after 24 hours (design choice). The link's token is stored only as its SHA-256.
- **Audit log.** Every run writes audit rows through `audit()`, including a no-op re-run.
- **Output.** `count: 1 tenants` (active tenants of that kind after the run), `date:`, `exit_code:`.

## Acceptance criteria
1. Given an empty local database, `provision_tenant --kind own` and `--kind pilot` each create exactly:
   - one tenant row of that kind;
   - one owner user;
   - one invite;
   - their audit rows (`tenant_provisioned`, `owner_invited`), with the job as actor and the tenant as target.
   Each prints `count: 1 tenants` and exits 0. Neither creates staff accounts, locations, OAuth connections or Square calls.
2. **Re-runs.** A second run of the same kind changes nothing, sends no email, writes a `tenant_provision_noop` audit row, prints `count: 1 tenants` and exits 0. Any state that would give two active tenants of one kind exits 1 and changes nothing.
3. **Isolation.** The two kinds never share rows. Under RLS, a session scoped to one tenant sees zero rows of the other (scenario 3 style).
4. **Refusals.** The job exits 1 and writes nothing if any of these hold:
   - the kind's owner-email secret is unset or not an email address;
   - the email send fails (transaction rolled back);
   - `--kind` is anything else.
5. **Output.** Output and audit rows hold no email, token, link, name or tenant label. They hold only evidence-grammar lines and ids. `test_provision_tenant.py` scans stdout, stderr, logs and the audit table for the fixture address and token.
6. **Email in tests.** The email vendor (Resend, unverified candidate) is a stub in tests, which asserts exactly one message, to the configured address, holding a link under `TILLOWL_PUBLIC_URL`. CI never sends a real email.
7. **Enrollment entry.** If STEP-10 offers no enrollment entry for an invited owner, stop and set `blocked_reason: enrollment_entry_missing`. Don't invent a second sign-in path.

## Human confirmation
"Founder: confirm all of these:
- STEP-13's release is deployed to production and `migrate` has run;
- `TILLOWL_OWNER_EMAIL_OWN` in the production secret store is your own address;
- you will launch `provision_tenant --kind own` yourself, knowing it sends one enrollment email to that address.

Then paste the job's output and enroll your TOTP from the email." Print AWAITING HUMAN CONFIRMATION and wait.

## Out of scope
Running `--kind pilot` (STEP-17); OAuth connect on production (STEP-16); owner enrollment screens (STEP-10); `onboarding_report` (STEP-17).

## Gate
`python -m tillowl.jobs.provision_tenant --kind own` (exact, from `docs/build/status/STEP-14.json`), launched by the founder as a Render one-off job on the production service. Gate files: `docs/build/gates/STEP-14.txt` (`tillowl/jobs/provision_tenant.py`, `tests/gates/step_14/test_provision_tenant.py`).

`docs/build/evidence/STEP-14.md` holds one block: the command, `exit_code: 0`, `job_id:`, `count: 1 tenants` and `date:`.

## If the gate fails
- Revert to the last green commit.
- Set `blocked` with a `blocked_reason` code (`owner_email_unset`, `invite_send_failed`, `duplicate_tenant`, `enrollment_entry_missing`), never values.
- After two failed attempts, restart in a fresh session with a narrower prompt.
- Never delete or edit production rows by hand to make a re-run pass. A fix goes through a code PR (a gate-change PR once this step is done).

## Prompt (paste into a fresh Claude Code session, run from an engineer's account)
```text
You are running STEP-14 "Provision our own production tenant" for TillOwl. Follow @CLAUDE.md throughout.
Start: git fetch && git rebase origin/main; confirm STEP-13 is "done" in docs/build/status/STEP-13.json (stop and say so if not); read git log -5; run CLAUDE.md's setup command; read @docs/build/steps/STEP-14-provision-own-tenant.md, @docs/build/steps/STEP-10-owner-signin-2fa.md, @tillowl/audit.py, @tillowl/db.py, BUILD_PLAN §7, and Slides 15–18, 21, 25 in @docs/architecture-pack-part1.md and @docs/architecture-pack-part2.md.
You never hold production credentials or use the Render CLI.
Work, test first:
- Set docs/build/status/STEP-14.json status to "in_progress".
- Write tests/gates/step_14/test_provision_tenant.py covering both kinds, re-runs, refusals, isolation and the output scan; run it and show it fails (RED TEST (intentional) if you stop here).
- Implement tillowl/jobs/provision_tenant.py (--kind own|pilot) and any tenant.kind migration, to the acceptance criteria for all valid inputs. Email is stubbed in tests.
- Run CLAUDE.md's test command and show the output; commit; open the step PR with gh (it merges on review).
After merge: print the human-confirmation line and the one-off job command (render jobs create <production service id> --start-command "python -m tillowl.jobs.provision_tenant --kind own"; unverified candidate syntax), then AWAITING HUMAN CONFIRMATION; wait.
Done PR: from the founder's pasted output only, write docs/build/evidence/STEP-14.md (job_id, exit_code: 0, count: 1 tenants, date), set status "done", run python tools/check_evidence.py validate --step STEP-14 and show the output, open the PR with gh; the founder approves and re-runs founder-approval. Never claim success without pasted output.
Out of scope: running --kind pilot, production OAuth, enrollment screens, onboarding_report.
Use a subagent to review the diff against this step file and report only gaps that affect correctness or the stated acceptance criteria.
```
