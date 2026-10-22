# STEP-43 Pilot-readiness gate (then day one)

Track: human. Lane: gate. Gate kind: human. Size: S. Runs only if STEP-21 recorded GO.
Depends on: STEP-03 10DLC and SMS opt-in, STEP-04 vendor terms, STEP-05 notice, STEP-07 DPA and pass line, STEP-15 T1 resolved, STEP-20 live spike, STEP-21 go/no-go decision, STEP-26 digest delivery, STEP-30 audit coverage, STEP-33 pilot onboarding, STEP-34 history pull, STEP-36 Flags A, STEP-37 Flags B, STEP-38 V-item branches, STEP-39 pass-line measurement, STEP-40 counsel T17b, STEP-41 metered cost. Done requires: none.
Blocks: none. The production nightly, explanation and digest jobs, and day one of the 90-day term, wait for this step's done PR.
Sources: Slide 24 (scenarios 1–4 as tests; scenario 5 "checked on each month's bill"), Slide 26 (Before day one; weekly 30-minute check-in ending "go paid or don't"; digest 2–3 times a week to the owner only), Slide 30 ("Before day one: close V1–V8 and T1, T11, T16, T17"), Slide 21 (owner only; least data to vendors), Slide 29 (RK4, RK8); BUILD_PLAN §5 STEP-43 conditions, §7 job switches, design choices 17, 20, 22, 25; D10, D11.

## Outcome
All eight BUILD_PLAN §5 conditions hold on one release, and the evidence is on file. After the done PR merges, the founder (and only the founder) does the following:
1. Sets `TILLOWL_JOBS_ENABLED` on production to add `nightly_pull`, `run_rules`, `run_explain` and `run_digest`, keeping `refresh_tokens` and `watchdog`.
2. Sets `TILLOWL_LLM_ENABLED=1` only if STEP-04 recorded `t8_no_training_term: CONFIRMED`. Otherwise it stays `0` and the digest runs template-only (D11).
3. Re-runs `python -m tillowl.jobs.history_pull --tenant pilot --days 30` as a Render one-off job if STEP-34's pull did not end the day before day one (design choice 17).
4. Day one of the 90-day term is the date the jobs are enabled. It is the pass line's before/after boundary (STEP-39).

After day one, during the pilot:
- **Monthly bill check (scenario 5).** The month's actual Render, Anthropic, Twilio and email bills are summed and compared with STEP-41's lean line. An overrun is a founder decision, never a quiet change.
- **Weekly 30-minute check-in with the owner (Slide 26).** It also records the D10 digest-opening measure.

## Acceptance criteria (BUILD_PLAN §5 conditions)
1. **Scenarios 1–4 pass on staging.** `pilot-gate` finds the latest `staging` push run on main green, with jobs `gate STEP-11`, `gate STEP-24`, `gate STEP-26`, `gate STEP-30` and `gate STEP-31` green. It also finds the latest `ci` push run on main green.
2. **The same release is on production and healthy.** The founder deploys the commit that the latest green staging run tested to production by hand, then `health_check --env production` exits 0. `pilot-gate` prints `release: <headSha>` of the latest green staging run and `health_check` prints `release: <deployed commit>`; `check_evidence.py` rejects STEP-43's evidence unless every `release:` line is the same commit.
3. **Every Slide 26 and Slide 30 before-day-one item is closed.** `pilot-gate` finds every depends_on step done and the decision GO: STEP-07 (DPA, fee, pass line, T11), 05 and 33 (notices, T16), 20 (OAuth, not a personal token; V1–V8 tested), 34 (30-day history), 15 (T1), and 40 (T17b, with T17a through STEP-20's dependency on STEP-02).
4. **T17b is signed and the templates are unchanged.** STEP-40 is done, and the template manifest still matches its hash in STEP-40's evidence.
5. **SMS works.** STEP-03 has `sms_optin`, `tendlc_approval` and `terms_t6` on file. `send_test --env staging --channel sms --to founder` really sends a synthetic digest and scenario 4's reconnect text to the founder's own phone, and the founder confirms both arrived. They carry only synthetic login codes, the reconnect text is one text asking to reconnect, and neither contains a deny-list word.
6. **Cost is within the lean line.** STEP-41 is done, and its `--check` passed.
7. **T8 is settled.** STEP-04 has `terms_t8`, or `t8_template_only` with LLM calls disabled in production (D11).
8. **Vendor data terms are on file.** STEP-04 has `terms_t5` and STEP-03 has `terms_t6`, because digests carry login codes.
- The recipient is the founder, never the owner or staff, and the text goes only to the founder's number held in the staging service's secrets, never in the repo or this session. CI never makes this send.

## Human confirmation
"Founder: is the release from the latest green staging run deployed to production by you, is your phone ready to receive two test texts from staging, and will you run the three commands below in your own terminal (the last two as Render one-off jobs) and paste their output?" Print AWAITING HUMAN CONFIRMATION and wait.

## Out of scope
Setting `TILLOWL_JOBS_ENABLED` or `TILLOWL_LLM_ENABLED` before the done PR merges; any send to the owner or staff; editing any gate, template or manifest; billing (STEP-42, due by day 90); the bill check and check-ins themselves.

## Gate
`python tools/check_evidence.py pilot-gate && python -m tillowl.jobs.health_check --env production && python -m tillowl.jobs.send_test --env staging --channel sms --to founder` (exact, from `docs/build/status/STEP-43.json`). Gate files: `docs/build/gates/STEP-43.txt` (none). The founder runs it, with `gh` authenticated for the `pilot-gate` checks.

`docs/build/evidence/STEP-43.md` holds three blocks:
- `pilot-gate`: `exit_code: 0`, `count: 17 steps_done`, `release: <40-hex>`, `role: founder`, `date:`;
- `health_check`: `exit_code: 0`, its `job_id:`, `count: 1 health_checks`, `release: <same 40-hex>`, `date:`;
- `send_test`: `exit_code: 0`, its `job_id:`, `count: N sms_segments`, `date:`.

One PR, straight from `not_started` to `done`.

## If the gate fails
Set `blocked` with a `blocked_reason` naming the failed condition (for example `scenario_gate_red`, `manifest_changed_reopen_t17b`, `sms_not_received`). No names or values. Fix it in the owning step, never here. After two failed attempts, restart in a fresh session with a narrower prompt. Never enable a production job while this step is not done.

## Prompt (paste into a fresh Claude Code session, run from an engineer's account)
```text
You are running STEP-43 "Pilot-readiness gate" for TillOwl. Follow @CLAUDE.md throughout.
Start: git fetch && git rebase origin/main; confirm every depends_on step in docs/build/status/STEP-43.json is "done" and STEP-21's decision is GO (stop and list any that aren't); read git log -5; run CLAUDE.md's setup command; read @docs/build/steps/STEP-43-pilot-readiness-gate.md, @docs/build/BUILD_PLAN.md §5 and Slides 21, 24, 26, 29, 30 in @docs/architecture-pack-part2.md.
This is a human step. Never read $PRIVATE_EVIDENCE_DIR, never run tools/check_artifact.py or the Render CLI, never hold production or Twilio credentials, and never send anything yourself.
1. Print the eight conditions as a checklist. Print the founder's commands for their own terminal:
   gh run list --workflow staging --branch main --event push --limit 1 --json headSha   (deploy exactly this commit to production by hand first)
   python tools/check_evidence.py pilot-gate
   render jobs create <production web service id> --start-command "python -m tillowl.jobs.health_check --env production"   (Render CLI form: unverified candidate, BUILD_PLAN §10)
   render jobs create <staging web service id> --start-command "python -m tillowl.jobs.send_test --env staging --channel sms --to founder"
   Then print the human-confirmation line and AWAITING HUMAN CONFIRMATION; wait.
2. From the founder's pasted output and confirmation only: write docs/build/evidence/STEP-43.md (three blocks), set status "done", run python tools/check_evidence.py validate --step STEP-43 and show the output, open the PR with gh (the founder approves, then re-runs founder-approval).
3. In the PR description, list the founder's post-merge actions: TILLOWL_JOBS_ENABLED on production adds nightly_pull, run_rules, run_explain, run_digest; TILLOWL_LLM_ENABLED=1 only if STEP-04 recorded T8 CONFIRMED, else 0 (D11); re-run history_pull for the 30 days ending the day before day one if needed; day one is the enable date; then the monthly bill check and the weekly check-in.
Out of scope: enabling anything before merge, sends to the owner or staff, editing gates or templates, billing.
End: Use a subagent to review the diff against this step file and report only gaps that affect correctness or the stated acceptance criteria.
```
