# STEP-43 Pilot-readiness gate (then day one)

Track: human. Lane: gate. Gate kind: human. Size: S. Runs only if STEP-21 recorded GO.
Depends on: STEP-03 10DLC and SMS opt-in, STEP-04 vendor terms, STEP-05 notice, STEP-07 DPA and pass line, STEP-15 T1 resolved, STEP-20 live spike, STEP-21 go/no-go decision, STEP-26 digest delivery, STEP-30 audit coverage, STEP-33 pilot onboarding, STEP-34 history pull, STEP-36 Flags A, STEP-37 Flags B, STEP-38 V-item branches, STEP-39 pass-line measurement, STEP-40 counsel T17b, STEP-41 metered cost. Done requires: none.
Blocks: none. The production nightly, explanation and digest jobs, and day one of the 90-day term, wait for this step's done PR.
Sources: Slide 24 (scenarios 1–4 as tests; scenario 5 "checked on each month's bill"), Slide 26 (Before day one; weekly 30-minute check-in ending "go paid or don't"; digest 2–3 times a week to the owner only), Slide 30 ("Before day one: close V1–V8 and T1, T11, T16, T17"), Slide 21 (owner only; least data to vendors), Slide 29 (RK4, RK8); BUILD_PLAN §5 STEP-43 conditions, §7 job switches and contracts, design choices 17, 20, 22, 25, 48; D10, D11, D21.

## Outcome
Before the gate, the founder fixes pilot day one in production config (`PASS_LINE` day one, from the signed DPA; STEP-39 reads it) and sets the D21 rule constants. Until day one the production cron stays `python -m tillowl.jobs.refresh_tokens && python -m tillowl.jobs.watchdog` with `TILLOWL_JOBS_ENABLED=refresh_tokens,watchdog`. `health_check` does not check the job list, so it passes now and after day one.

All nine BUILD_PLAN §5 conditions hold on one release, the 30-day "before" window is pulled, and the evidence is on file. The founder runs the gate on day one itself (the window ends the day before, so it must be complete in the restaurant's time zone; design choice 18). If the gate fails, nothing is enabled; day one moves only by the founder's decision recorded in config, and the whole gate re-runs.

On day one, after the done PR merges, the founder (and only the founder):
1. Adds `nightly_pull`, `run_rules`, `run_explain` and `run_digest` to production's `TILLOWL_JOBS_ENABLED` and cron, keeping `refresh_tokens` and `watchdog`.
2. Sets `TILLOWL_LLM_ENABLED=1` only if T8 is resolved (STEP-04 recorded `t8_no_training_term: CONFIRMED`). Otherwise it stays `0` and the digest runs template-only (D11).

After day one, during the pilot:
- **Monthly bill check (scenario 5).** The month's actual Render, Anthropic, Twilio and email bills are summed and compared with STEP-41's lean line. An overrun is a founder decision, never a quiet change.
- **Weekly 30-minute check-in with the owner (Slide 26).** It also records the D10 digest-opening measure.

## Acceptance criteria (BUILD_PLAN §5 conditions)
1. **Scenarios 1–4 pass on staging.** `pilot-gate` finds the latest `staging` push run on main green, with jobs `gate STEP-11`, `gate STEP-24`, `gate STEP-26`, `gate STEP-30` and `gate STEP-31` green. It also finds the latest `ci` push run on main green.
2. **The same release is on production and healthy.** The founder deploys the commit that the latest green staging run tested to production by hand, then `health_check --env production` exits 0. `pilot-gate` prints `release: <headSha>` of that staging run and `health_check` prints `release: <deployed commit>`; `check_evidence.py` rejects the evidence unless every `release:` line is the same commit.
3. **Every Slide 26 and Slide 30 before-day-one item is closed.** `pilot-gate` finds every depends_on step done and the decision GO: STEP-07 (DPA, fee, pass line, T11), 05 and 33 (notices, T16), 20 (OAuth, not a personal token; V1–V8 tested), 34 (history pull), 15 (T1), and 40 (T17b, with T17a through STEP-20's dependency on STEP-02).
4. **The "before" window has evidence.** `history_pull --tenant pilot --before-day-one` (STEP-34) pulls the 30 days ending the day before `PASS_LINE` day one on production, exits 0 and prints `count: 30 days`.
5. **T17b is signed and the templates are unchanged.** STEP-40 is done, and the template manifest still matches its hash in STEP-40's evidence.
6. **SMS works.** STEP-03 has `sms_optin`, `tendlc_approval` and `terms_t6` on file. `send_test --env staging --channel sms --to founder` really sends two texts, a synthetic digest and then scenario 4's reconnect text, to the founder's own phone, and the founder confirms both arrived. They carry only synthetic login codes, the reconnect text only asks to reconnect, and neither contains a deny-list word.
7. **Cost is within the lean line.** STEP-41 is done, and its `--check` passed.
8. **T8 is settled.** STEP-04 has `terms_t8`, or `t8_template_only` with LLM calls disabled in production (D11).
9. **Vendor data terms are on file.** STEP-04 has `terms_t5` and STEP-03 has `terms_t6`, because digests carry login codes.
- The test texts go only to the founder's number held in the staging service's secrets, never to the owner or staff, never in the repo or this session. CI never makes this send.

## Human confirmation
"Founder: is `PASS_LINE` day one set to today in production config, is the release from the latest green staging run deployed to production by you, have you put the Twilio credentials and `TILLOWL_SMS_ENABLED=1` on the STAGING service (never production), is your phone ready for two test texts, and will you run the four commands below in your own terminal (the last three as Render one-off jobs) and paste their output?" Print AWAITING HUMAN CONFIRMATION and wait.

## Out of scope
Enabling production jobs or `TILLOWL_LLM_ENABLED` before the done PR merges; any send to the owner or staff; editing any gate, template or manifest; billing (STEP-42, due by day 90); the bill check and check-ins themselves.

## Gate
`python tools/check_evidence.py pilot-gate && python -m tillowl.jobs.health_check --env production && python -m tillowl.jobs.history_pull --tenant pilot --before-day-one && python -m tillowl.jobs.send_test --env staging --channel sms --to founder` (exact, from `docs/build/status/STEP-43.json`). Gate files: `docs/build/gates/STEP-43.txt` (none). The founder runs it, with `gh` authenticated for the `pilot-gate` checks.

`docs/build/evidence/STEP-43.md` holds four blocks; every `release:` line is the same commit. The three job blocks need no `job_id` or `role` line; the founder's PR approval shows who ran them.
- `pilot-gate`: `exit_code: 0`, `count: 17 steps_done`, `release: <40-hex>`, `role: founder`, `date:`;
- `health_check`: `exit_code: 0`, `count: 1 health_checks`, `release: <same 40-hex>`, `date:`;
- `history_pull`: `exit_code: 0`, `count: 30 days`, `count: N orders`, `count: N events`, `date:`;
- `send_test`: `exit_code: 0`, `count: N sms_segments`, `date:`.

One PR, straight from `not_started` to `done`.

## If the gate fails
Set `blocked` with a `blocked_reason` naming the failed condition (for example `scenario_gate_red`, `release_mismatch`, `before_window_incomplete`, `manifest_changed_reopen_t17b`, `sms_not_received`). No names or values. Fix it in the owning step, never here. After two failed attempts, restart in a fresh session with a narrower prompt. Never enable a production job while this step is not done.

## Prompt (paste into a fresh Claude Code session, run from an engineer's account)
```text
You are running STEP-43 "Pilot-readiness gate" for TillOwl. Follow @CLAUDE.md throughout.
Start: git fetch && git rebase origin/main; confirm every depends_on step in docs/build/status/STEP-43.json is "done" and STEP-21's decision is GO (stop and list any that aren't); read git log -5; run CLAUDE.md's setup command; read @docs/build/steps/STEP-43-pilot-readiness-gate.md, @docs/build/BUILD_PLAN.md §5 and §7, and Slides 21, 24, 26, 29, 30 in @docs/architecture-pack-part2.md.
This is a human step. Never read $PRIVATE_EVIDENCE_DIR, never run tools/check_artifact.py or the Render CLI, never hold production or Twilio credentials, and never send anything yourself.
1. Print the nine conditions as a checklist. Print the founder's preparation: set PASS_LINE day one (today) and the D21 constants in production config; keep the production cron at refresh_tokens && watchdog with TILLOWL_JOBS_ENABLED=refresh_tokens,watchdog; put the Twilio credentials and TILLOWL_SMS_ENABLED=1 on the STAGING service only. Then print the founder's commands for their own terminal:
   gh run list --workflow staging --branch main --event push --limit 1 --json headSha   (deploy exactly this commit to production by hand first)
   python tools/check_evidence.py pilot-gate
   render jobs create <production web service id> --start-command "python -m tillowl.jobs.health_check --env production"   (Render CLI form: unverified candidate, BUILD_PLAN §10)
   render jobs create <production web service id> --start-command "python -m tillowl.jobs.history_pull --tenant pilot --before-day-one"
   render jobs create <staging web service id> --start-command "python -m tillowl.jobs.send_test --env staging --channel sms --to founder"
   Then print the human-confirmation line and AWAITING HUMAN CONFIRMATION; wait.
2. From the founder's pasted output and confirmation only: write docs/build/evidence/STEP-43.md (four blocks, every release: line the same commit, no job_id or role on the job blocks), set status "done", run python tools/check_evidence.py validate --step STEP-43 and show the output, open the PR with gh (the founder approves, then re-runs founder-approval).
3. In the PR description, list the founder's day-one actions after merge: add nightly_pull, run_rules, run_explain, run_digest to production's TILLOWL_JOBS_ENABLED and cron, keeping refresh_tokens and watchdog; TILLOWL_LLM_ENABLED=1 only if T8 is resolved, else 0 (D11); then the monthly bill check and the weekly check-in.
Out of scope: enabling anything before merge, sends to the owner or staff, editing gates or templates, billing.
End: Use a subagent to review the diff against this step file and report only gaps that affect correctness or the stated acceptance criteria.
```
