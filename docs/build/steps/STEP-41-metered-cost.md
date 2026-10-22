# STEP-41 Metered cost estimate (T9, scenario 5)

Track: build. Lane: platform. Gate kind: human. Size: S. Runs only if STEP-21 recorded GO.
Depends on: STEP-26 Digest build and delivery, STEP-37 Flags B and the ranker, STEP-38 V-item branches (so the metered digests carry the final wording). Done requires: none. D13 (Render plan, Postgres instance types and their price) must be decided before the founder's run.
Blocks: STEP-40 counsel T17b (it reviews the sample outputs this step saves), STEP-43 pilot-readiness gate.
Sources: Slide 22 (lean line ~$20–25: tokens ~$1 = 8.1M in + 0.56M out at $0.10/$0.50 per million, SMS ~$15 = 1,000 segments + number + 10DLC campaign fee, hosting ~$5, database cost TBD), Slide 24 (scenario 5: "checked on each month's bill"), Slide 25 (ADR-002, ADR-005 "SMS costs scale with message length", ADR-007 Proposed until the database cost is known), Slide 19–20 (LLM and Twilio lines), Slide 30 (T9); planning prompt situation (Haiku 5.5 costs $0.50/$2.50 above 100k tokens); BUILD_PLAN §7, §10, design choices 2, 21, 22; D11, D13.

## Outcome
- `tillowl/jobs/cost_estimate.py`: `--sample PATH [--live] [--check] [--findings PATH]`, findings default `docs/build/findings/llm-samples.md`. It reads only the sample file and opens no database connection.
  - It renders each synthetic digest with STEP-26's pure `render_digest(flags, explanations)` from `tillowl/digest/build.py` (never `build_digest`, which reads the database), so it opens no database connection, and makes each explanation call through STEP-25's `tillowl/explain/`, so the prompt, the pinned model, the low effort and the token metering are the production ones. Without `--live` it uses STEP-25's stub client and makes no network call. With `--live` it calls the real model.
  - It measures tokens in, out and thinking. It extrapolates them to a month at 2 and at 3 digests a week (4.33 weeks a month, design choice), and the `usd_month` lines use 3 a week.
  - It counts SMS segments from the digest bodies. The segment rule is taken from Twilio's official docs, and the findings cite the URL as an unverified candidate.
  - It adds the fixed monthly costs: Render web (production and staging), Render cron (every cron job in both environments), both Postgres instances (staging is a second database, T9), email, and the SMS number and 10DLC campaign fees.
- Prices are never in code or the fixture. Under `--live` the job asks the founder for each price line, with its https source URL and the date it was checked: token in/out per million (≤100k-token tier), SMS per segment, SMS fixed fees, `hosting_web`, `hosting_cron`, `db_staging`, `db_production` and `email`. Re-check every price page on the day of the run. The ~$1 token line assumed $0.10/$0.50 per million for prompts of 100k tokens or fewer.
- Output, evidence-grammar lines only: `count:` in units `sample_flags`, `tokens_in`, `tokens_out`, `tokens_thinking`, `sms_segments`; `model_id: claude-haiku-5-5`; `usd_month:` in units `tokens`, `sms`, `hosting_web`, `hosting_cron`, `db_staging`, `db_production`, `email`, `total`, `lean_line`; `sha256: … label=findings`; and it ends with `date:` then `exit_code:`.
- `--live` writes `docs/build/findings/llm-samples.md` (synthetic data only), for counsel's T17b review in STEP-40. Its sections:
  - **Samples:** each synthetic flag's facts (login codes only), the model's sentence, and STEP-24's checker verdict (kept, or replaced by the template line).
  - **Cost inputs:** each price line with its unit, USD amount, source URL and date checked. The founder must accept this added section.
- `tests/gates/step_41/fixtures/cost_sample.json`: synthetic ranked flags shaped like STEP-37's output (login codes such as `L07`, shift names such as "Dinner", counts such as 9), flags per digest, and `lean_line_usd`. The founder sets `lean_line_usd` in the step PR before the run. Slide 22 gives "~$20–25"; the exact number is the founder's.

## Acceptance criteria
1. Arithmetic holds for all valid inputs. `pytest -c pytest.ini --rootdir=. tests/gates/step_41/test_cost_estimate_offline.py` generates samples and prices with a fixed seed and checks two properties for every case:
   - `total` equals the sum of the other seven `usd_month` units, to the cent;
   - token and SMS cost scale linearly with digests per week.
   It also runs on `cost_sample.json`.
2. `--check` exits 1 exactly when `total` > `lean_line`. A total equal to the line passes. The test pins the cent on each side of the line.
3. Every prompt stays under 100,000 input tokens. A sample whose prompt reaches 100,000 makes the job exit 1 before pricing anything, because above that the price tier changes.
4. Every output token is metered. `tokens_out` and `tokens_thinking` both come from the usage STEP-25 records, and thinking is priced at the output rate. The stub returns non-zero thinking, and the test sees it in the cost.
5. Every call uses the pinned `claude-haiku-5-5` from config and sets effort to low explicitly. The test asserts both on every stub call, and that `model_id:` is printed.
6. The model gets flag facts with login codes only. A sample row with a display-name field is refused (exit 1) before any call. So is a value that isn't in its flag. The test inspects every payload.
7. No price constant exists in `cost_estimate.py` or the fixture. A price line with a blank, negative or non-https source is rejected. The test passes prices in-process, never through a file in the repo.
8. Stdout holds only evidence-grammar lines. The test checks every line against `tools/check_evidence.py`'s `LINE_RULES`. No URL, sentence or name is printed.
9. The `sha256: … label=findings` line equals the SHA-256 of the file written. A model sentence that STEP-24's checker rejects is recorded as replaced, so counsel sees both.
10. The test makes any database connection attempt raise; the job never opens one, and the rendered bodies equal `render_digest` on the same synthetic flags. The last two output lines are `date:` and `exit_code:`.
11. Without `--live`, the test blocks sockets and the job still exits 0. CI never runs `--live`; this test runs in the normal test command on every PR.

## V-item branches
Digest bodies, and so SMS segments, follow `tillowl/config.py` `V_ITEMS` as recorded from `docs/build/findings/square-fields.md`, never a per-call-site flag. The offline test pins `V_ITEMS` with monkeypatch and runs both the all-RETURNED and the all-NOT_RETURNED configuration. The live run uses the recorded one.
- V1: If RETURNED, dollar totals appear in cancelled-order lines. If NOT_RETURNED or PARTIAL, no dollar amounts.
- V2: If RETURNED: "9 checks cancelled during shift Y (opened by login X)". If NOT_RETURNED or PARTIAL: "9 checks cancelled during shift Y".
- V4: If RETURNED, "approved by code Y" is added. If NOT_RETURNED or PARTIAL, it is left out.
- V3, V5, V6, V7: lines appear or are left out as in the go/no-go criteria table.

## Human confirmation
"Founder: on the step PR's head commit, in your own terminal, export a NON-production Anthropic key (never paste it here), run the command below, enter each current price with its source URL when asked, and paste the full output." Print AWAITING HUMAN CONFIRMATION and wait.

## Out of scope
Production data or the production database; scheduling; the monthly bill check itself (STEP-43, after day one); billing (STEP-42); the Render CLI; changing prices or `lean_line_usd` to make `--check` pass.

## Gate
`python -m tillowl.jobs.cost_estimate --sample tests/gates/step_41/fixtures/cost_sample.json --live --check` (exact, from `docs/build/status/STEP-41.json`). Gate files: `docs/build/gates/STEP-41.txt`; the job module is frozen once this step is done.

`docs/build/evidence/STEP-41.md` holds one block: the command, `exit_code: 0`, the five `count:` lines, `model_id:`, the nine `usd_month:` lines, `sha256: <hex> label=findings` and `date:`. CI recomputes the findings hash. No `role` line is needed; the founder's PR approval shows who ran it.

Two PRs, not one, because CI lets a done PR change only its status and evidence files:
1. **Step PR:** status `in_progress`; code, offline test and fixture; then the findings file from the founder's run on that PR's final commit. A later code commit means re-running `--live`.
2. **Done PR:** after the step PR merges; evidence plus status `done`.

## If the gate fails
Revert to the last green commit. Set `blocked` with a `blocked_reason` (no keys, names or values). After two failed attempts, restart in a fresh session with a narrower prompt.
- **`total` over the line:** set `blocked_reason: cost_over_lean_line`. That raises a founder decision (D13 plan, price, or a recorded new lean line in BUILD_PLAN §12), never a quiet edit.
- **Prompt of 100k tokens or more:** shrink the prompt in `tillowl/explain/` through its own PR, then re-run.

## Prompt (paste into a fresh Claude Code session, run from an engineer's account)
```text
You are running STEP-41 "Metered cost estimate" for TillOwl. Follow @CLAUDE.md throughout.
Start: git fetch && git rebase origin/main; confirm STEP-26 and STEP-37 are "done" and STEP-21's decision is GO in docs/build/status/ (stop and say which if not); confirm D13 is decided in @docs/build/BUILD_PLAN.md §12 (stop if not); read git log -5; run CLAUDE.md's setup command; read @docs/build/steps/STEP-41-metered-cost.md and Slides 19, 20, 22, 24, 25, 30 in @docs/architecture-pack-part1.md and @docs/architecture-pack-part2.md.
Work, test first:
- Set docs/build/status/STEP-41.json status to "in_progress".
- Write tests/gates/step_41/test_cost_estimate_offline.py and fixtures/cost_sample.json exactly as listed in docs/build/gates/STEP-41.txt (synthetic login codes only; lean_line_usd as the founder states it); run them; they fail (print RED TEST (intentional) if you stop here).
- Implement tillowl/jobs/cost_estimate.py to the acceptance criteria, reusing tillowl/explain/ and STEP-26's pure render_digest (no database connection; output ends with date: and exit_code:). Use WebFetch on Twilio's official SMS segment docs and Anthropic's official pricing and models pages; print the URLs as unverified candidates for the founder. Put no price in code.
- Run the test command from CLAUDE.md and show the output; commit; open the step PR with gh.
Human gate: print the human-confirmation line, then the founder's command
  python -m tillowl.jobs.cost_estimate --sample tests/gates/step_41/fixtures/cost_sample.json --live --check
and AWAITING HUMAN CONFIRMATION; wait. Never ask for or hold the key. From the founder's reply only: commit docs/build/findings/llm-samples.md (the founder's run wrote it) to the step PR, and check that sha256sum matches the pasted findings line.
Done PR (after the step PR merges): write docs/build/evidence/STEP-41.md from the pasted output, set status "done", run python tools/check_evidence.py validate --step STEP-41 and show the output, open the PR with gh (the founder approves, then re-runs founder-approval). If --check exited 1, set blocked (cost_over_lean_line) instead and stop.
Out of scope: production data, scheduling, billing, the monthly bill check, the Render CLI, editing prices or lean_line_usd to pass.
End: Use a subagent to review the diff against this step file and report only gaps that affect correctness or the stated acceptance criteria.
```
