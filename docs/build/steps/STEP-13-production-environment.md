# STEP-13 Production environment (own secrets, RLS, PITR, restore test, redirect URL live)

Track: build. Lane: platform. Gate kind: production_job. Size: M.
Depends on: STEP-11 Square OAuth connect, STEP-12 first sandbox consent on staging. Done requires: none. D13 (Render plan, instance types, price) must be recorded in BUILD_PLAN §12 before this step starts.
Blocks: STEP-14 own tenant, STEP-15 T1 resolved, STEP-17 friend's tenant, STEP-20 live spike, STEP-33 pilot onboarding.
Sources: Slide 21 (encrypted tokens, key in the host's secret store, tenant isolation), Slides 22–23 (Render web service, cron jobs, managed PostgreSQL, D6–D10), Slide 24 (scenario 1: off the service path), Slide 25 (ADR-007), Slide 29 (TD2); BUILD_PLAN §1 (Render Postgres, 14-day cap), §7, §10, design choices 2, 25–29; D13.

## Outcome
Production exists on Render, separate from staging:
- **Web service and Postgres.** Its own web service (the Owner Console, serving `SQUARE_REDIRECT_PATH` over HTTPS) and its own Render Postgres instance.
- **Fresh secrets** in Render's secret store, never staging's: the database URL (internal), `TILLOWL_AES_KEY`, `TILLOWL_HMAC_KEY` (for STEP-19/20), the email key the watchdog alerts use, `TILLOWL_PUBLIC_URL`, `TILLOWL_ENV=production`, `TILLOWL_JOBS_ENABLED=refresh_tokens,watchdog`, `TILLOWL_LLM_ENABLED=0`. The Square production application id and secret are set here if Square has issued them; if Square issues them only after approval (TBD — not in sources), the founder sets them in STEP-16.
- **Schema.** All migrations, with `FORCE ROW LEVEL SECURITY` on every tenant table.
- **Deploys.** Auto-deploy off; every deploy manual and founder-confirmed. The founder runs `python -m tillowl.jobs.migrate --env production` as a one-off job at each deploy.
- **Schedule.** Until STEP-43, one cron job whose command is `python -m tillowl.jobs.refresh_tokens && python -m tillowl.jobs.watchdog`, with `TILLOWL_JOBS_ENABLED=refresh_tokens,watchdog` (BUILD_PLAN §7).
- **Database access.** External access closed (no IP allowlist entries; design choice 26).
- **Backups.** A plan whose PITR window is inside the 14-day cap: 7 days on Pro per [Render backups](https://render.com/docs/postgresql-backups), unverified candidate. Whatever else Render keeps (exports) must also fall inside 14 days.
- **Job modules.** `tillowl/jobs/restore_check.py` and `tillowl/jobs/redirect_check.py` (frozen when this step is done). `health_check` gains its production checks. Every job runs through STEP-08's `run_job`.
- **Restore canary.** A `restore_canary` table (an operational table like `schema_migrations`: no tenant data, no RLS, policy, grant or role change).

## Acceptance criteria
1. **`health_check --env production`** exits 0 only if all of these hold, and prints `count: 1 health_checks`, `release: <40-hex>`, `date:`, `exit_code:`:
   - `/healthz` at the production URL answers 200 over HTTPS with a valid certificate and status ok;
   - the release it reports is 40 lowercase hex characters;
   - migrations are current: every file in `migrations/` is recorded in `schema_migrations` with a matching SHA-256.
   It does **not** check which jobs are enabled, so it stays valid after STEP-43 (BUILD_PLAN §7); the jobs lockdown is a founder-confirmed item below. Key presence and length are covered by STEP-10's startup key check. `test_health_check.py` makes it fail for each broken condition in turn and passes with any `TILLOWL_JOBS_ENABLED` value.
2. **`restore_check`.** `restore_check --env production --write-canary` (a preparation run, not the gate) writes a batch of random canary rows and audit-logs it. The gate run `restore_check --env production` then reads `TILLOWL_RESTORE_DATABASE_URL` (the restored instance) and compares that batch's row count and SHA-256 there and in production. It exits 0 only if they match, the batch has at least 1 row, and the restored URL is a different instance from production. It prints `count: N rows`, `sha256: <hex> label=restore_canary`, `date:`, `exit_code:`.
   `test_restore_check.py` uses two local databases and checks four cases:
   - match → 0;
   - restore point before the canary → 1;
   - same database twice → 1;
   - variable unset → 1.
3. **`redirect_check --env production`** builds the redirect URL from `TILLOWL_PUBLIC_URL` and `SQUARE_REDIRECT_PATH`. It exits 0 only if the scheme is `https`, the certificate verifies, and an unsigned-in GET reaches our console (sent to sign-in or rejected with 400), not a 404 or 5xx. Square's docs say the production redirect URL must use HTTPS ([move to production](https://developer.squareup.com/docs/oauth-api/movetoprod), unverified candidate). `test_redirect_check.py` covers http, a bad certificate, 404, 5xx and the good case with a stub server.
4. **What jobs print.** Every job prints only evidence-grammar lines, ending with `date:` then `exit_code:`. On failure it prints `exit_code: 1` and one fixed reason code; never a URL, host, key or value.
5. **What the restored copy holds.** At this point production holds no tenant data, so the restored copy holds only the schema and the canary. The founder deletes it after the gate.
6. **What runs.** Nothing in production runs the nightly, explain or digest jobs. Nothing calls Square with data scopes. Nothing sits in the restaurant's order or payment path (scenario 1).

## Human confirmation
"Founder: in Render, confirm the following.
- Production has its own web service, cron job and Postgres, with freshly generated `TILLOWL_AES_KEY` and `TILLOWL_HMAC_KEY` and none of staging's secrets.
- Auto-deploy is off, external database access has no allowlist entries, and the PITR window is within 14 days.
- Jobs lockdown: the only cron job's command is `python -m tillowl.jobs.refresh_tokens && python -m tillowl.jobs.watchdog`, `TILLOWL_JOBS_ENABLED` is exactly `refresh_tokens,watchdog`, and `TILLOWL_LLM_ENABLED` is `0`.
- You deployed this release manually and ran `migrate`.

After the canary run, restore to a NEW instance at a time after the canary, set `TILLOWL_RESTORE_DATABASE_URL` for the restore_check job only, run the three gate jobs, then delete the restored instance and remove the variable." Print AWAITING HUMAN CONFIRMATION and wait.

## Out of scope
Any tenant (STEP-14, 17), any Square call with a seller (STEP-16), enabling other jobs (STEP-43), staging changes, prices (D13, STEP-41).

## Gate
Exact, from `docs/build/status/STEP-13.json`; each command is a Render one-off job the founder launches (`render jobs create`, unverified candidate):

`python -m tillowl.jobs.health_check --env production && python -m tillowl.jobs.restore_check --env production && python -m tillowl.jobs.redirect_check --env production`

Gate files: `docs/build/gates/STEP-13.txt` (the two job modules and three tests). `docs/build/evidence/STEP-13.md` holds three blocks, each with `job_id:`, then the job's lines ending `date:` and `exit_code: 0`. The restore block also carries `count: N rows` and `sha256: … label=restore_canary`.

## If the gate fails
- Revert to the last green commit.
- Set `blocked` with a `blocked_reason` code (`health_failed`, `restore_mismatch`, `redirect_not_https`, `d13_not_recorded`), never values.
- After two failed attempts, restart in a fresh session with a narrower prompt.
- Always delete a restored instance, even after a failure. Whether changing a variable redeploys the service is TBD — not in sources; check Render's docs before doing it.

## Prompt (paste into a fresh Claude Code session, run from an engineer's account)
```text
You are running STEP-13 "Production environment" for TillOwl. Follow @CLAUDE.md throughout.
Start: git fetch && git rebase origin/main; confirm STEP-11 and STEP-12 are "done" in docs/build/status/ and D13 is recorded in BUILD_PLAN §12 (stop and say which if not); read git log -5; run CLAUDE.md's setup command; read @docs/build/steps/STEP-13-production-environment.md, BUILD_PLAN §1, §7, §10, §11 (choices 2, 25–29), and Slides 21–25, 29 in @docs/architecture-pack-part2.md.
You never hold production credentials or use the Render CLI.
Work, test first:
- Set docs/build/status/STEP-13.json status to "in_progress".
- Write the three tests in docs/build/gates/STEP-13.txt; run them and show they fail (RED TEST (intentional) if you stop here).
- Implement restore_check.py (--write-canary and the gate mode), redirect_check.py, the health_check production checks and the restore_canary migration, to the acceptance criteria for all valid inputs.
- Run CLAUDE.md's test command; commit; open the step PR with gh. It also prints the founder's Render checklist from the Outcome. It merges on review.
After merge: print the human-confirmation line, the canary command, and the three gate commands as one-off jobs; then AWAITING HUMAN CONFIRMATION; wait.
Done PR: from the founder's pasted output only, write docs/build/evidence/STEP-13.md (three blocks with job_id and exit_code: 0), set status "done", run python tools/check_evidence.py validate --step STEP-13 and show the output, then open the PR with gh. The founder approves and re-runs founder-approval. Never claim success without pasted output.
Out of scope: tenants, Square sellers, other jobs, staging, prices.
Use a subagent to review the diff against this step file and report only gaps that affect correctness or the stated acceptance criteria.
```
