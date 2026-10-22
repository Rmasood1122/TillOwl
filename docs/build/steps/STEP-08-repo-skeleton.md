# STEP-08 Repo skeleton (schema with RLS, audit role, business day, migrations, config)

Track: build. Lane: platform. Gate kind: ci_fixture. Size: M.
Depends on: STEP-01 Square-sandbox spike (D14 default: no overlap). Done requires: none.
Blocks: STEP-09 staging deploy, STEP-10 owner sign-in, STEP-23 fact templates, STEP-25 explanation service.
Sources: Slides 15–18 (v1 entities, R1–R13, Q1–Q12, "Every table also carries tenant_id"), Slide 21 (tenant isolation, audit log), Slide 24 (scenario 3), Slides 22–23 (Render, managed PostgreSQL), Slide 29 (TD1), Slide 30 (V-item rule), ADR-004, ADR-006, ADR-007; BUILD_PLAN §7, design choices 1, 6, 10, 18, 22, 25, 33; D14.

## Outcome
- **`pyproject.toml`.** Python 3.12 package `tillowl`, runtime dependency `psycopg[binary]` 3, and a `dev` extra with `pytest` 8. Dependencies only: no pytest section (CI rejects one).
- **`migrations/0001_schema.sql`.** Tables, keys and indexes only; no security DDL.
  - Slide entities, with the FK names from Slides 16 and 18: `tenant`, `oauth_connection`, `location` (with `time_zone` and `business_day_start`), `shift`, `login`, `approval_code`, `no_sale`, `pos_check` (a Square order; `check` is an SQL keyword), `cancelled_order`, `line_item`, `discount`, `comp`, `refund`, `owner_user` (`UNIQUE (tenant_id)`, Q1), `staff_notice`, `acknowledgment` (`login_id` nullable until mapped), `audit_log`, `csv_export`, `baseline`, `flag`, `digest`, `digest_flag`.
  - Supporting tables, so later steps need no new RLS (design choice 33): `owner_recovery_code` and `owner_session` (STEP-10), `support_access_grant` (STEP-27), `explanation` and `llm_usage` (STEP-25), and three operational tables with no restaurant data: `job_run` (STEP-09; job name, env, times and exit code only), `restore_canary` (STEP-13) and `support_user` (STEP-27: the founder's TOTP support sign-in, which belongs to no tenant).
  - Every table carries `tenant_id uuid NOT NULL`, except the operational tables `job_run`, `restore_canary` and `support_user`, which hold no restaurant data, and `audit_log`, whose `tenant_id` is NULL only for events with no tenant (an unknown-email sign-in, a job run).
  - Fields that wait on a V-item (V1 amount, V2 `opened_by_login`, V4–V7) are nullable. Money is integer cents, times are `timestamptz`, and events carry `business_day date`.
  - The timecard (TMC) is v2 and is not created. Later steps add columns through ordinary migrations.
- **`migrations/0002_rls.sql`.** `ENABLE` and `FORCE ROW LEVEL SECURITY` on every table with `tenant_id`, with one policy per table: `tenant_id = current_setting('app.tenant_id', true)::uuid` for both USING and WITH CHECK. On `audit_log`, an insert may also carry a NULL `tenant_id`.
- **`migrations/0003_audit_role.sql`.** Roles created idempotently (`IF NOT EXISTS` on `pg_roles`), because staging gates share one cluster:
  - `tillowl_app`: LOGIN, NOBYPASSRLS, DML on tenant tables, and no UPDATE, DELETE or TRUNCATE on `audit_log`.
  - `tillowl_audit_writer`: INSERT on `audit_log` only.
  - `tillowl_signin`: SELECT on `owner_user` across tenants and on `support_user`, for the email lookup before a tenant is known.
  - `tillowl_scheduler`: SELECT on `tenant` across tenants, so jobs can list tenants and then work in each one.
  - It also holds the grants (including membership in all four for the migrating user, so `db.py` can `SET ROLE`), the two role-scoped policies, and a trigger that rejects UPDATE, DELETE and TRUNCATE on `audit_log` for every role, the table owner included.
- **`tillowl/db.py`.** Connects from `DATABASE_URL`, runs `SET ROLE tillowl_app`, and gives `tenant_tx(conn, tenant_id)`, which sets `app.tenant_id` for one transaction only.
- **`tillowl/audit.py`.** `audit(conn, *, tenant_id, actor, action, target=None)` writes one `audit_log` row as `tillowl_audit_writer`. `AUDIT_ACTIONS` is the allowlist of action names; later steps add to it.
- **`tillowl/business_day.py`** (design choice 18). `business_day(ts, tz, day_start)` gives the restaurant's business day; `day_bounds(day, tz, day_start)` gives its UTC start and end ("yesterday" for the nightly pull); `in_window(local_time, start, end)` handles windows that cross midnight. `location.business_day_start` is the owner's setting, defaulting to 04:00 local (design choice proposed here).
- **The job wrapper.** `tillowl/jobs/__init__.py` `run_job(main)`, which every job's `__main__` uses (BUILD_PLAN §7). `main(emit)` returns an exit code; `emit(line)` accepts only evidence-grammar lines (`docs/build/evidence/README.md`) and refuses anything else. `run_job` then prints `date: YYYY-MM-DD` (UTC) and `exit_code: N` as the last two lines and exits N. An uncaught exception or a refused line becomes `exit_code: 1`, and its text is never printed. STEP-09 adds the `job_run` row.
- **The migration runner.** `tillowl/jobs/migrate.py`, run through `run_job` as `python -m tillowl.jobs.migrate [--env staging|production]`. It records each applied file's name and SHA-256 in `schema_migrations`, which it creates itself.
- **`tillowl/config.py`.**
  - `TILLOWL_JOBS_ENABLED` is a comma list. A scheduled job not on it exits 0 without work.
  - `TILLOWL_LLM_ENABLED` is true only for the exact value `1`; the default is off (design choice 22).
  - `V_ITEMS` maps `V1`–`V8` and any sub-item (such as `V2.opened_by`) to `RETURNED` or `NOT_RETURNED`. Every item is NOT_RETURNED until `docs/build/status/STEP-21.json` records `"decision": "GO"`. After that, the `v_item:` lines of `docs/build/findings/square-fields.md` decide, with PARTIAL or a missing line read as NOT_RETURNED (design choice 10). It is the only place later steps read V-items.

## Acceptance criteria
1. **`test_schema_rls.py`** (with `fresh_db`).
   - The catalog shows that every table except `job_run`, `restore_canary`, `support_user` and `schema_migrations` has a `tenant_id` column, RLS enabled and forced, and at least one policy. This holds for every table the catalog lists, so a later table without RLS fails it.
   - For every table in 0001, with two tenants seeded inline: `tillowl_app` and the table owner each see only the tenant in `app.tenant_id`, see zero rows when it is unset, and fail to insert a row for the other tenant. Superusers always bypass RLS, so the test makes a non-superuser role the owner of the tables first. Whether Render's database user is a superuser is TBD — not in sources; STEP-09 finds out with the CREATE ROLE check.
   - `tillowl_signin` and `tillowl_scheduler` can read only their one table each.
2. **`test_audit_role.py`.** `audit()` writes exactly one row, timed by the database clock, and rejects an action not in `AUDIT_ACTIONS` or a `target` that isn't `<table>:<uuid>`, so names and values can't enter. UPDATE, DELETE and TRUNCATE on `audit_log` fail as `tillowl_app`, as `tillowl_audit_writer` and as the (non-superuser) table owner. Applying 0003 a second time, and to a second database on the same server, both succeed.
3. **`test_business_day.py`.** For every minute of the 2026 DST-change weeks in `America/New_York` and `America/Los_Angeles`, `ts` falls inside `day_bounds(business_day(ts))`; each day's end equals the next day's start; days last 23, 24 or 25 hours. `in_window` is right for every minute of the day against a window that crosses midnight and one that doesn't; a window whose start equals its end is rejected.
4. **`test_migrate_runner.py`.** On an empty database it applies every file in lexical order, each in its own transaction; a second run applies none; a failing file rolls back only itself and exits non-zero; a changed hash for an applied file exits 1 and applies nothing. It works under a non-`public` `search_path` (no migration names a schema). Its output is only `count: <n> rows`, then `date:` and `exit_code: <n>`.
   - The same file tests `run_job` with inline `main` functions that return 0, return 3, raise an exception whose message holds a marker string, and emit a non-grammar line: every output line is in the evidence grammar, the last two are `date: <today in UTC>` then `exit_code: N`, N equals the process exit status (1 for the raise and the refused line), and the marker never appears in stdout or stderr.
5. **`test_governance_tools.py`** runs `tools/check_evidence.py` and `tools/build_progress.py` as subprocesses on temporary git repos in `tmp_path`, with no network:
   - valid status files pass, and a bad `gate_kind` or a missing field fails;
   - a valid ci_fixture evidence file passes; a `note:` line, a nonzero exit code or a missing date fails;
   - `ci` rejects a `tools/` change unless the branch starts with `gate-change/`, and rejects a pytest section in `pyproject.toml`, a nested `conftest.py`, and a post-STEP-08 migration containing `GRANT`;
   - `junit` fails a report with a skip, an xfail or a gate file with zero tests.
6. `tests/unit/test_config.py`, which is not a gate file, covers the `V_ITEMS` rules, the job switch and the LLM flag.
7. Security DDL appears only in 0002 and 0003. Automations are written in code, not n8n (Slide 3, C2). All test data is inline and synthetic (login codes like `L07`). No tables, columns or fields come from spike samples.

## Out of scope
Console routes (STEP-09, 10), `crypto.py` (STEP-10), Square code, job modules other than `migrate`, deployment. The root `conftest.py`, `pytest.ini` and `tools/` are installed by the founder and protected; never edit them.

## Gate
`pytest -c pytest.ini --rootdir=. tests/gates/step_08` (exact, from `docs/build/status/STEP-08.json`). Gate files: the five tests in `docs/build/gates/STEP-08.txt`; no other file goes under `tests/gates/step_08/`.

`docs/build/evidence/STEP-08.md` holds the pytest block: `exit_code: 0`, `count: N passed` and `run_id` from the green `ci` push run on main for the evidence commit's parent, and `date:`.

## If the gate fails
Revert to the last green commit, set the status to `blocked` with a `blocked_reason` (no names or values), and after two failed attempts restart in a fresh session with a narrower prompt. A failure inside `tools/` or `conftest.py` is a gate-change matter for the founder: never patch it here. If PostgreSQL won't start inside the sandbox, that is a G7 smoke-test failure; say so and stop.

## Prompt (paste into a fresh Claude Code session)
```text
You are running STEP-08 "Repo skeleton" for TillOwl. Follow @CLAUDE.md throughout.
Start: git fetch && git rebase origin/main; confirm STEP-01 is "done" in docs/build/status/STEP-01.json (stop and say so if not); read git log -5; run CLAUDE.md's setup command; read @docs/build/steps/STEP-08-repo-skeleton.md, BUILD_PLAN §7 and §11 in @docs/build/BUILD_PLAN.md, @conftest.py, and Slides 15–18, 21, 24 in @docs/architecture-pack-part1.md and @docs/architecture-pack-part2.md.
Work, test first:
- Set docs/build/status/STEP-08.json status to "in_progress".
- Write the five gate tests named in docs/build/gates/STEP-08.txt, using the root fixtures fresh_db and pg_server, plus tests/unit/test_config.py. Run them; they fail. If you stop here, print RED TEST (intentional).
- Write pyproject.toml, migrations 0001–0003, tillowl/db.py, audit.py, business_day.py, config.py, tillowl/jobs/__init__.py (run_job) and tillowl/jobs/migrate.py to the acceptance criteria. Keep every grant, policy, role and audit_log rule in 0002 or 0003.
- Run CLAUDE.md's test command inside this sandboxed session and show the command and its full summary line. Paste that output into the PR description as the "database test run inside a sandboxed Claude session". It is not the evidence.
- Commit and open the step PR with gh (status in_progress). It merges when CI is green and a reviewer approves.
Done PR, after the step PR merges: one commit on top of main holding only docs/build/evidence/STEP-08.md and the status set to "done". Take run_id from the green ci push run on main for that commit's parent, and "count: N passed" from that run's log (gh run view <id> --log); add the date. Run python tools/check_evidence.py validate --step STEP-08, show the command and its output, and open the PR. Never claim success without output.
Out of scope: console, crypto, Square code, deployment, and any edit to tools/, conftest.py or pytest.ini.
Use a subagent to review the diff against this step file and report only gaps that affect correctness or the stated acceptance criteria.
```
