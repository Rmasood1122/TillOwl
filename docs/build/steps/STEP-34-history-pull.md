# STEP-34 30-day history pull (V8)

Track: build. Lane: connector. Gate kind: production_job. Size: S. Runs only if STEP-21 recorded GO.
Depends on: STEP-31 Square event ingestion (scenario 1), STEP-33 pilot onboarding on production. Done requires: none.
Blocks: STEP-43 pilot-readiness gate.
Sources: Slide 26 (pass line "for 30 days before and 60 days after"; "30 days of pre-pilot history pulled: availability is a verify item"), Slides 12–13 (flow steps 1–2), Slide 30 (V8), ADR-004, ADR-006 ("baselines start later"); `docs/build/go-no-go-criteria.md` §1 hard stop 2; BUILD_PLAN design choices 15, 17, 18, 25; T17a code `pre_notice_history`.

## Outcome
**`tillowl/jobs/history_pull.py`** (`--tenant pilot --days 30 [--end YYYY-MM-DD]`) ingests each business day of the window through STEP-31's `ingest_day`, oldest first, with the same normalization, V-item branches and acknowledgment stripping.
- The default window is the 30 business days ending with yesterday's business day, in the restaurant's time zone (design choice 18). Re-running a window replaces its rows, and `location.last_pulled_business_day` never moves backwards.
- It prints `count: N days` (days whose pull completed, closed days included), `count: N orders`, `count: N events` and `exit_code: N`, and exits 1 if any day in the window fails.
- It is a founder-launched one-off job, never scheduled; `nightly_pull` stays off (design choice 25).

**`tillowl/jobs/onboarding_report.py --history`** (added here) prints `count: N days` (business days in the same default window with at least one order, so closed days don't count), `count: N events` and `count: N orders`. It exits 1 if `orders` is 0.

**The pass line's "before" window** is the 30 days ending the day before pilot day one (design choice 17). If this step runs earlier, the founder re-runs `history_pull --tenant pilot --days 30 --end <day before day one>` when enabling the jobs at STEP-43. That re-run is a separate one-off job recorded in STEP-43's PR.

The history feeds per-shift totals for STEP-35's baselines and STEP-39's "before" figure.

## Acceptance criteria
`tillowl/jobs/history_pull.py` is a gate file, frozen once this step is done.

1. **Window** (`test_history_pull_window.py`, on `fresh_db` with a stub Square). The window is exactly 30 business days ending yesterday in the location's time zone, including across a daylight-saving change and with windows that cross midnight. `--end` moves the window. Each day is pulled once, a re-run leaves the same row counts, one failing day makes the job exit 1, and the output holds only grammar lines.
2. **Stripping, in the same test.** Logins without an acknowledgment on file are stripped. With `pre_notice_history: TOTALS_ONLY`, every row dated before its login's acknowledgment has `login_id` null; with `PER_LOGIN_ALLOWED`, those rows keep the login for acknowledged logins. Restaurant totals are the same under both codes.
3. **Production gate.** Both gate jobs exit 0, and `history_pull` prints `count: 30 days`.
4. **Read-only.** Every Square call is a read call from `client.py`'s allowlist.

## V-item branches
- **V8 (30 days of history).** If V8 is RETURNED: as above; baselines (STEP-35) start from this history. If NOT_RETURNED or PARTIAL: the decision was NO-GO (hard stop 2), and this step never runs. The exception is when the criteria's collect-first option was accepted and signed in the DPA. Then, before this step starts, the founder approves a gate-change PR that replaces this gate. The "before" figure is then built by `nightly_pull` over the first 30 pilot days, the 90-day term starts after them, and STEP-39 measures from there. The exact replacement command is TBD in that PR.
- **V1–V7.** These follow STEP-31's branches unchanged, because the history pull calls the same `ingest_day` and reads `V_ITEMS` only. For example, with V2 NOT_RETURNED, the history's cancelled orders are counted per shift window only.

## Human confirmation
"Founder: confirm that the owner agrees to the 30-day history pull on their live Square account now, that STEP-33 is done, and whether pilot day one is set. If it isn't, this run's window ends yesterday, and you will re-run it with `--end` at STEP-43."

Print AWAITING HUMAN CONFIRMATION and wait.

## Out of scope
Baselines (STEP-35) and the pass-line computation (STEP-39); enabling `nightly_pull`; pulling more than 30 days; storing raw responses.

## Gate
`python -m tillowl.jobs.history_pull --tenant pilot --days 30 && python -m tillowl.jobs.onboarding_report --tenant pilot --history` (exact, from the status file). The gate files are listed in `docs/build/gates/STEP-34.txt`. The founder launches each command as a Render one-off job: `render jobs create <production service id> --start-command "<command>"` (unverified candidate, BUILD_PLAN §10).

`docs/build/evidence/STEP-34.md` holds one block per command: `command:`, `exit_code: 0`, `job_id:`, the `count:` lines and `date:`.

## If the gate fails
Revert to the last green commit for code failures. Set the status to `blocked` with a `blocked_reason` such as `history_days_short`, with no values. After two failed attempts, restart in a fresh session with a narrower prompt. Never retry against the live account without the owner's OK. A window that comes back short means V8 behaves differently from STEP-20's result: raise it with the founder under RK1, and don't widen the window.

## Prompt (paste into a fresh Claude Code session, run from an engineer's account)
```text
You are running STEP-34 "30-day history pull (V8)" for TillOwl. Follow @CLAUDE.md throughout.
Start:
1. git fetch && git rebase origin/main
2. Confirm STEP-31 and STEP-33 are "done" in docs/build/status/, and that STEP-21's "decision" is "GO". If not, stop and say which.
3. Read git log -5.
4. Run CLAUDE.md's setup command.
5. Read @docs/build/steps/STEP-34-history-pull.md, @docs/build/findings/square-fields.md (V8), @docs/build/findings/counsel-t17a-answers.md, @docs/build/go-no-go-criteria.md, and Slides 12, 13, 26 and 30 in @docs/architecture-pack-part1.md and @docs/architecture-pack-part2.md.
6. Print the human-confirmation line and AWAITING HUMAN CONFIRMATION, then wait.
Work, test first:
- Set docs/build/status/STEP-34.json status to "in_progress".
- Write tests/gates/step_34/test_history_pull_window.py and run it. It fails (print RED TEST (intentional) if you stop here).
- Implement jobs/history_pull.py and onboarding_report --history to the acceptance criteria, reusing square/ingest.py.
- Run the test and CLAUDE.md's test command, and show both outputs.
- Commit, then open the step PR with gh. It merges on review.
Production (after merge):
- Print the founder's steps: deploy this release by hand, then run each gate command as: render jobs create <production service id> --start-command "<command>"
- Print AWAITING HUMAN CONFIRMATION, then wait for the pasted job id, exit code and output.
Done PR: from the pasted output only, write docs/build/evidence/STEP-34.md (one block per command, with job_id and exit_code: 0) and set the status to "done". Run python tools/check_evidence.py validate --step STEP-34, show the output, and open the PR with gh. Its description says the founder approves, then re-runs founder-approval. Never claim success without output.
Out of scope: baselines, the pass-line computation, enabling jobs, pulls beyond 30 days.
Use a subagent to review the diff against this step file and report only gaps that affect correctness or the stated acceptance criteria.
```
