# STEP-28 Console: shift windows and digest settings

Track: build. Lane: console. Gate kind: ci_fixture. Size: S.
Depends on: STEP-10 owner sign-in with TOTP two-factor. Done requires: none.
Blocks: STEP-30 audit coverage, STEP-31 Square event ingestion, STEP-33 pilot onboarding, STEP-35 ratio rules and baselines.
Sources: Slide 4–5 (A1: the owner "sets digest preferences"), Slide 15–16 (SHF: "v1 windows set by owner"; LOC: time zone; R3), Slide 17–18 (Q5, Q6, Q7), Slide 21 (audit log of every setting change; owner-only access), Slide 26 ("Digest 2–3 times a week, to the owner only"), Slide 29 (TD1), Slide 30 (T14), ADR-005; BUILD_PLAN §1 (T14: the owner sets windows at onboarding), design choices 18 and 20.

## Outcome
- `tillowl/console/settings.py`, shift windows: the owner sets, per location:
  - a name (for example "Dinner"), a start and an end in local wall-clock time, in the location's IANA time zone (the Location entity's time zone);
  - an end at or before the start means the window crosses midnight and ends on the next calendar day. Start equal to end is refused;
  - windows of one location may not overlap, so every instant belongs to at most one window;
  - every write goes through the console's access check with the action `shift_windows.write`. The owner always passes it. STEP-27's support grant lets the founder pass it when the owner can't enter windows (BUILD_PLAN §1); STEP-30 tests that path once both steps are merged.
- `tillowl/business_day.py` gains `shift_window_for(ts_utc, location) -> (shift_id, business_day) | None`, which STEP-31 and STEP-35 import:
  - a window instance belongs to the business day on which it starts (design choice 18), so "yesterday" is the restaurant's business day, never the UTC date;
  - an instant outside every window returns `None`.
- An edit takes effect from the next business day. Events already ingested keep the shift STEP-31 tagged them with.
- `settings.py`, digest settings:
  - digest days: 2 or 3 distinct weekdays (Slide 26);
  - the owner's SMS phone (`owner_user.phone`, owner-only: a support user gets 403; changes audit-logged as `settings_changed` without the number itself), entered only after the owner's signed SMS opt-in (STEP-03);
  - channels: email, and SMS only when the owner's phone is on file. SMS still sends only when STEP-26's switch is on (design choice 20);
  - recipients are not a setting: the digest goes to the tenant's `owner_user` only. STEP-26's `run_digest` reads these days.
- Every change, owner or support, writes one `settings_changed` audit row with actor, target, and before and after values (window times and weekdays are not personal data).

## Acceptance criteria
1. `test_shift_windows.py`: valid windows, including ones crossing midnight, are stored. Start = end, overlapping windows, an unknown time zone and a time outside 00:00–23:59 are refused, with no row written. Owner A can't read or change tenant B's windows (RLS, connected as the application role). A session that fails the `shift_windows.write` check gets 403 and an `access_denied` audit row.
2. `test_window_business_day.py`: for generated sets of non-overlapping windows, some crossing midnight, and every 5-minute instant across a synthetic year in `America/New_York`, including the DST change days 2026-11-01 and 2027-03-14:
   - `shift_window_for` returns at most one window, and that window contains the instant's local wall-clock time;
   - the business day it returns is the local date on which that window instance started; an instant outside every window returns `None`;
   - a second time zone (for example `America/Los_Angeles`) gives the same properties, so no code assumes New York.
3. `test_settings_audit.py`:
   - digest days must be 2 or 3 distinct weekdays, and channels must be non-empty;
   - no field, route or request parameter adds a recipient other than the tenant's `owner_user`;
   - every accepted change to a window or a digest setting writes exactly one `settings_changed` audit row, through `audit()`, with the right actor; a refused change writes none.
4. Tests run on `fresh_db` as the application role, with synthetic data only.

## Out of scope
Tagging events with windows (STEP-31). Baselines per window (STEP-35). Sending digests (STEP-26). Real shifts from timecards (v2, TD1). The owner entering the real windows on production (STEP-33).

## Gate
`pytest -c pytest.ini --rootdir=. tests/gates/step_28`, exact, from `docs/build/status/STEP-28.json`; the gate files are in `docs/build/gates/STEP-28.txt`. `docs/build/evidence/STEP-28.md` holds one block: `command:` (the gate), `exit_code: 0`, `count: N passed`, `run_id:` (the green `ci` push run on main for the evidence commit's parent), `date:`.

## If the gate fails
Revert to the last green commit. Set the status to `blocked` with a `blocked_reason` that holds no names or values (for example `dst_day_misassigned`). After two failed attempts, restart in a fresh session with a narrower prompt.

## Prompt (paste into a fresh Claude Code session)
```text
You are running STEP-28 "Console: shift windows and digest settings" for TillOwl. Follow @CLAUDE.md throughout.
Start:
1. git fetch && git rebase origin/main
2. Confirm STEP-10 is "done" in docs/build/status/STEP-10.json; if not, stop and say so. Read git log -5.
3. Run CLAUDE.md's setup command.
4. Read @docs/build/steps/STEP-28-console-shift-windows.md, @docs/build/BUILD_PLAN.md §1, §7 and §11, @tillowl/business_day.py, @tillowl/audit.py, @tillowl/console/, and Slides 4, 5, 15, 16, 17, 18, 21, 26, 29, 30 in @docs/architecture-pack-part1.md and @docs/architecture-pack-part2.md.
Work, test first:
- Set docs/build/status/STEP-28.json status to "in_progress".
- Write the gate files exactly as listed in docs/build/gates/STEP-28.txt, with synthetic data built in the tests (shift names like "Dinner"). Run them: they fail (print RED TEST (intentional) if you stop here).
- Implement settings.py and shift_window_for to the acceptance criteria, using zoneinfo, never fixed UTC offsets. Writes call the console's access check with action shift_windows.write; don't build support-grant logic here (STEP-27 owns it).
- Verify with CLAUDE.md's test command and with: PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -c pytest.ini --rootdir=. tests/gates/step_28. Commit; open the step PR with gh (status in_progress). It merges when CI is green.
Done PR: one commit on top of main holding only docs/build/evidence/STEP-28.md and the status set to "done". The run_id is the green "ci" push run on main for that commit's parent, and count: N passed comes from that run. Run python tools/check_evidence.py validate --step STEP-28, show the output, and open it with gh. Show every command and its output; never claim success.
Out of scope: event tagging (STEP-31), baselines (STEP-35), sending (STEP-26), timecards (v2), production entry (STEP-33).
Use a subagent to review the diff against this step file and report only gaps that affect correctness or the stated acceptance criteria.
```
