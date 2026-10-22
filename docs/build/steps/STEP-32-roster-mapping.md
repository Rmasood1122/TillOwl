# STEP-32 Roster-read job and acknowledgment mapping

Track: build. Lane: console. Gate kind: ci_fixture. Size: M. Runs only if STEP-21 recorded GO.
Depends on: STEP-21 go/no-go decision recorded (GO), STEP-27 console notices, acknowledgment entry and support access. Done requires: none.
Blocks: STEP-33 pilot onboarding on production, STEP-35 ratio rules and baselines, STEP-36 flags A.
Sources: Slides 15–16 (EMP "login_id, square team member, display name"; R4), Slides 17–18 (ACK; Q4 "signs 1 per notice version"), Slide 13 step 9 ("login codes, no full history"), Slide 21 (least data to vendors; who sees what; vendor support access audit-logged), Slide 29 (TD5), ADR-006; BUILD_PLAN design choices 13, 14, 16; T17a code `roster_read_scope_approved`.

## Outcome
- `tillowl/square/roster.py`: `read_roster(tenant)` reads Square team-member ids and display names through `tillowl/square/client.py`. It makes read calls only, under the roster-read scope named in STEP-01's findings. It upserts one `login` row per team member (`square_team_member_id`, `display_name`, `login_code`).
  - A new team member gets the next free code (`L01`, `L02`, …).
  - Codes are never reused or renumbered.
  - A team member that is no longer returned keeps its row and code, marked inactive, because acknowledgments and history point to it.
  - The data is used **only** for the acknowledgment mapping (design choice 14).
- `tillowl/jobs/roster_read.py` (`python -m tillowl.jobs.roster_read --tenant pilot`) prints only `count: N logins_total` and `exit_code: N`. It audit-logs `roster.read` with the count.
- STEP-27's mapping screen lists logins as code plus display name, to the signed-in owner, or to the founder while an owner's support-access grant is active.
  - Mapping sets `acknowledgment.login_id` (Q4).
  - Each map and unmap is audit-logged by login code, never by name.
- Display names live only in the `login` table and the console's HTML. They are never logged, never in evidence, never sent to the LLM and never in the digest's LLM sentences.

## Acceptance criteria
1. **Roster and mapping** (`test_roster_mapping.py`, given `fixtures/square_team_members.json`, with synthetic names such as `SYNTH_NAME_01`).
   - The roster read creates one login per team member, and a re-run is idempotent (same codes).
   - A new team member gets the next code. A removed one keeps its code and becomes inactive.
   - An acknowledgment maps to exactly one login, and a login has at most one acknowledgment per notice version (Q4).
   - Mapping by the founder without an active grant is refused, and the denial is audit-logged.
   - Every map, unmap and remap writes one audit row.
2. **Display names stay local** (`test_display_names_stay_local.py`).
   - The test runs the roster read and the mapping, then runs STEP-25's explanation payload builder and STEP-26's digest build on synthetic flags for those logins.
   - No fixture display name appears in stdout or stderr, the log records, any `audit_log` row, the LLM request payload or the digest text.
   - A static check fails if the display-name column is referenced outside `tillowl/square/roster.py`, `tillowl/console/` and `migrations/`.
3. **Counsel branch, through `tillowl/config.py` `COUNSEL`.**
   - If `roster_read_scope_approved: YES`: the steps above apply.
   - If `NO`: `roster_read` makes no Square call and prints the count of logins already in the table. The mapping screen accepts a login code and a Square team-member id that the founder types from the Square dashboard, with `display_name` left null.
   - Both branches are tested.
4. **Read-only.** Every request is in `client.py`'s read-only allowlist. A Square error makes the job exit 1, and its output still holds only grammar lines.

## V-item branches
- **Roster fields.** Team-member ids and display names are not V-items, so `roster_read` reads the same fields in every branch.
- **Login-bearing items** (V2, V7, and V3–V6 where they carry a login), read only through `V_ITEMS`.
  - If any of them is RETURNED: mapped logins whose acknowledgment is on file get their login on those events at ingest (STEP-31), and so in baselines and flags.
  - If none is RETURNED (possible only under the go/no-go criteria's shift-level-only GO option): the mapping still runs, because the acknowledgment record is a legal record (L1). Ingest then keeps every login out of stored events, so no login reaches a flag or a digest.

## Out of scope
Running `roster_read` on production and entering the real acknowledgments (STEP-33); ingestion (STEP-31); notice versions and acknowledgment entry, which already exist (STEP-27); any display name in a template, prompt, log or evidence line.

## Gate
`pytest -c pytest.ini --rootdir=. tests/gates/step_32` (exact, from the status file). The gate files are listed in `docs/build/gates/STEP-32.txt`. `docs/build/evidence/STEP-32.md` holds one pytest block: `command:`, `exit_code: 0`, `count: N passed`, the `run_id:` of the green `ci` push run on main for the evidence commit's parent, and `date:`.

## If the gate fails
Revert to the last green commit. Set the status to `blocked` with a `blocked_reason` (no names or values). After two failed attempts, restart in a fresh session with a narrower prompt. If a display name leaks anywhere, fix the leak. Never loosen the test.

## Prompt (paste into a fresh Claude Code session)
```text
You are running STEP-32 "Roster-read job and acknowledgment mapping" for TillOwl. Follow @CLAUDE.md throughout.
Start:
1. git fetch && git rebase origin/main
2. Confirm STEP-21 and STEP-27 are "done" in docs/build/status/, and that STEP-21's "decision" is "GO". If not, stop and say which.
3. Read git log -5.
4. Run CLAUDE.md's setup command.
5. Read @docs/build/steps/STEP-32-roster-mapping.md, @docs/build/findings/square-sandbox.md (roster scope), @docs/build/findings/counsel-t17a-answers.md, and Slides 13, 15, 16, 17, 18 and 21 in @docs/architecture-pack-part1.md and @docs/architecture-pack-part2.md.
Work, test first:
- Set docs/build/status/STEP-32.json status to "in_progress".
- Write the two tests and the fixture exactly as listed in docs/build/gates/STEP-32.txt. Fixture names are synthetic tokens (SYNTH_NAME_01…), never real names.
- Run pytest -c pytest.ini --rootdir=. tests/gates/step_32. It fails (print RED TEST (intentional) if you stop here).
- Implement square/roster.py, jobs/roster_read.py and the mapping hook in STEP-27's screen, to the acceptance criteria, with both COUNSEL branches.
- Run the gate and CLAUDE.md's test command, and show both outputs. Commit, then open the step PR with gh (status in_progress). It merges when CI is green.
Done PR: after the ci push run on main is green, make one commit on top of main holding only docs/build/evidence/STEP-32.md (command, exit_code: 0, count: N passed and run_id from that run via gh run view <id> --log, date) and the status set to "done". Run python tools/check_evidence.py validate --step STEP-32, show the output, and open the PR. Never claim success without output.
Out of scope: production runs, real acknowledgments, ingestion, display names anywhere but the console.
Use a subagent to review the diff against this step file and report only gaps that affect correctness or the stated acceptance criteria.
```
