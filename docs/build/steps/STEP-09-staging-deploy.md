# STEP-09 Staging deploy, fake-data cron and alerts

Track: build. Lane: platform. Gate kind: ci_staging. Size: M.
Depends on: STEP-08 Repo skeleton. Done requires: none. Founder decisions first: D13 (Render plan and staging Postgres, T9) and D18 (staging database exposure to GitHub-hosted runners).
Blocks: STEP-11 Square OAuth connect; STEP-24 digest fact checker (done requires: its gate runs in the staging workflow).
Sources: Slides 22–23 (console as a Render web service, jobs as Render cron jobs, managed PostgreSQL; "If this node is down, the restaurant runs normally"), Slide 24 (scenario 1), Slide 29 (TD2), ADR-007 (Proposed); BUILD_PLAN §7 (jobs, migrations, `staging_schema`), §10 (Render notifications, watchdog), design choices 2, 25, 27; D13, D18.

## Outcome
Staging holds synthetic data only and is off the service path: nothing here touches Square, a restaurant or production.
- **Render staging web service.** Start command `python -m tillowl.jobs.migrate --env staging && uvicorn tillowl.console.app:app …`, on the port Render's docs specify. `tillowl/console/app.py` serves `GET /healthz`:
  - after a `SELECT 1`, it returns exactly `{"status":"ok","release":"<git sha>"}`, with the release from `RENDER_GIT_COMMIT` ("The commit SHA for a service or deploy"; unverified candidate, https://render.com/docs/environment-variables);
  - it returns 503 with `"status":"error"` when the database is unreachable;
  - the `staging` workflow's deploy job reads this body. Auto-deploy is off; the workflow deploys through the service's deploy hook (one secret URL per service, GET or POST; unverified candidate, https://render.com/docs/deploy-hooks).
- **Render staging cron service.** It runs `python -m tillowl.jobs.watchdog --env staging` once a day, with `TILLOWL_JOBS_ENABLED=watchdog`; schedules are UTC (unverified candidate, https://render.com/docs/cronjobs). It builds from `main` on push, which is allowed on staging only.
- **`tillowl/jobs/health_check.py --env staging|production`.** It GETs `/healthz` from the configured base URL, and prints `count: 1 health_checks`, `release: <40-hex>`, `date:` and `exit_code: 0` only for status ok with a 40-hex release. STEP-13 reuses it.
- **STEP-08's `run_job` in `tillowl/jobs/__init__.py`** gains one `job_run` row per run (job, env, start, end, exit code). Its output still ends with `date:` then `exit_code: N`, and every job here runs through it.
- **`tillowl/jobs/watchdog.py`** (design choice 27).
  - Inputs: each scheduled job in `TILLOWL_JOBS_ENABLED` and its `config.JOB_MAX_AGE_HOURS` entry.
  - It emails the founder (`TILLOWL_FOUNDER_EMAIL`) one alert per job whose last successful run is older than that, or that never succeeded, then exits 1 so Render's failure email fires too.
  - It also checks its own previous run, so a missed watchdog run is reported after the fact.
  - Sender: STEP-08's `tillowl/email.py` `send_email`; this step adds its real email-vendor transport (Resend, unverified candidate; read its official docs in-session) behind `TILLOWL_EMAIL_MODE`, `stub` by default. It stays `stub` on staging until the founder switches it.
- **Render failure email.** Workspace notifications are set to "Only failure notifications", which covers "A cron job execution fails" by email. One-off job failures notify by Slack only (unverified candidate, https://render.com/docs/notifications).
- **GitHub `staging` environment** (founder): secrets `RENDER_STAGING_DEPLOY_HOOK` and `STAGING_DATABASE_URL`, and variable `STAGING_URL`.
- **The CREATE ROLE answer**, recorded in the step PR description and passed on to STEP-13. Whether the staging database user may run 0003's `CREATE ROLE` is TBD — not in sources. If it can't, the founder creates the four roles once by hand.

## Acceptance criteria
1. **`tests/gates/step_09/test_staging_health.py`.** `GET {STAGING_URL}/healthz` over HTTPS returns 200 and a body with exactly the keys `status` and `release`, `status` equal to `ok`, and `release` 40 lowercase hex characters. The deploy job has already checked that the release contains this commit. `python -m tillowl.jobs.health_check --env staging` prints exactly `count: 1 health_checks`, `release: <the 40-hex release>`, `date: <today UTC>` and `exit_code: 0`, in that order. The body carries nothing else: no environment, no database URL.
2. **`test_cron_fake_data.py`: one cron run on fake data, in a per-run schema.** Using the `staging_schema` fixture, the test seeds `tests/gates/step_09/fixtures/fake_day.json` and runs the cron's exact start command as a subprocess against that schema, with the stub sender.
   - **The fixture** is synthetic only: a fixed `now`, the enabled jobs, and job-run histories for `fresh`, `missed` and `never`. It holds no tenant, staff or Square data.
   - **On `fresh`:** exit 0, every output line in the evidence grammar and the last two `date:` then `exit_code: 0`, exactly one new `job_run` row for `watchdog` with exit code 0, and zero emails.
   - **On `missed`:** exit 1 and exactly one email.
3. **`test_watchdog_alerts.py`.**
   - For every scenario in the fixture: exactly one email per stale or never-run enabled job, and none for fresh or disabled jobs.
   - Each email goes to the founder's address only, and its subject and body hold only the job name, env and whole hours since the last success. No tenant, staff, URL or secret appears.
   - Ages are computed in UTC from `job_run` times, never from a local clock.
   - The watchdog's own missed run is detected.
   - A sender failure still exits 1, so Render's email remains as a backstop.
4. CI never sends real email or SMS and never calls Square. Sessions never hold `STAGING_DATABASE_URL` (G4), so `tests/unit/test_watchdog.py` (not a gate file) covers the same logic on `fresh_db` for local runs.
5. If the database or the whole staging host is down, nothing outside staging is affected (scenario 1's premise). No production credential exists in staging.

## Human confirmation
"Founder: (1) Are D13 and D18 recorded in BUILD_PLAN §12? (2) Did you create the Render staging Postgres and the web and cron services with the settings I printed? (3) Is the workspace notification level set? (4) Are `RENDER_STAGING_DEPLOY_HOOK` and `STAGING_DATABASE_URL` set as secrets, and `STAGING_URL` as a variable, in the GitHub `staging` environment? Answer yes or no to each, and never paste a value here." Print AWAITING HUMAN CONFIRMATION and wait.

## Out of scope
Production (STEP-13), `refresh_tokens` (STEP-11), Square and the nightly pull (STEP-31), sign-in and every route except `/healthz` (STEP-10), digest delivery (STEP-26).

## Gate
`pytest -c pytest.ini --rootdir=. tests/gates/step_09` (exact, from `docs/build/status/STEP-09.json`). It runs only in the `staging` workflow on `main`, in job `gate STEP-09`. Gate files are listed in `docs/build/gates/STEP-09.txt`.

`docs/build/evidence/STEP-09.md` holds:
- the pytest block with `exit_code: 0` and `count: N passed` from that job's log;
- `run_id` of a green `staging` push run on `main`, with the gate files unchanged since;
- `date:`.

## If the gate fails
Revert to the last green commit, or fix forward in a new PR. Set the status to `blocked` with a `blocked_reason` (no URLs, names or values). After two failed attempts, restart in a fresh session with a narrower prompt.

If 0003 fails with a permission error on `CREATE ROLE`, that is the TBD answer:
1. Print the role statements from 0003 for the founder to run once in their own terminal against staging.
2. Print AWAITING HUMAN CONFIRMATION.
3. The founder re-runs the `staging` workflow.

Never ask for the staging URL or database URL in a session.

## Prompt (paste into a fresh Claude Code session)
```text
You are running STEP-09 "Staging deploy, fake-data cron and alerts" for TillOwl. Follow @CLAUDE.md throughout.
Start: git fetch && git rebase origin/main; confirm STEP-08 is "done" in docs/build/status/STEP-08.json (stop and say so if not); read git log -5; run CLAUDE.md's setup command; read @docs/build/steps/STEP-09-staging-deploy.md, @.github/workflows/staging.yml, @conftest.py, BUILD_PLAN §7, §10 and §12 in @docs/build/BUILD_PLAN.md, and Slides 22–24 in @docs/architecture-pack-part2.md.
Human confirmation first: read Render's cron, deploy-hook, notification and environment-variable docs with WebFetch; print the founder's Render and GitHub setup checklist (service names, start commands, schedule, notification level, which secret goes where — never a value); print the human-confirmation line and AWAITING HUMAN CONFIRMATION; wait. Stop if D13 or D18 is not decided.
Work, test first:
- Set docs/build/status/STEP-09.json status to "in_progress".
- Write the gate tests and fixtures/fake_day.json exactly as listed in docs/build/gates/STEP-09.txt, plus tests/unit/test_watchdog.py on fresh_db. Gate files need the staging environment and can't run here; run the unit tests and see them fail. If you stop here, print RED TEST (intentional).
- Implement /healthz, the job_run row in run_job, health_check and watchdog (stub sender by default) to the acceptance criteria; add fastapi, uvicorn and httpx to pyproject.toml.
- Run CLAUDE.md's test command and show the command and its output; commit; open the step PR with gh (status in_progress). It merges on review with CI green.
After merge: the staging workflow runs job "gate STEP-09" on main. If it is red, fix forward in a new PR (for a CREATE ROLE refusal, follow "If the gate fails").
Done PR: one commit on top of main holding only docs/build/evidence/STEP-09.md and the status set to "done". Take run_id from the green staging run, and "count: N passed" from gh run view <id> --log for job "gate STEP-09"; add the date. Run python tools/check_evidence.py validate --step STEP-09, show the command and its output, and open the PR. Record the CREATE ROLE answer (allowed / founder-created) in the PR description.
Out of scope: production, Square, OAuth, sign-in, digests.
Use a subagent to review the diff against this step file and report only gaps that affect correctness or the stated acceptance criteria.
```
