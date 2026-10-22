# STEP-25 Explanation service with the model stubbed

Track: build. Lane: explain. Gate kind: ci_fixture. Size: M.
Depends on: STEP-08 Repo skeleton, STEP-23 Fact templates and template manifest (it reads STEP-23's `explain_prompt.txt`). Done requires: none.
Blocks: STEP-26 digest build and delivery, STEP-40 counsel review T17b.
Sources: Slide 5 (A7 "Flagged facts only; never full history"), Slide 9 / 11 (C11 = V9, C14 = V10), Slide 13 (flow steps 8–10: "Facts of each flag; login codes, no full history"), Slide 19 (LLM ~$1 a month at $0.10/$0.50 per million; T8 gap), Slide 21 (least data to vendors; no AI training), Slide 22 (lean cost), Slide 30 (T8), ADR-002; BUILD_PLAN §7 (job switches), design choices 1, 14, 21, 22; D11.

## Outcome
`tillowl/explain/`:
- `MODEL_ID = "claude-haiku-5-5"` (pinned) and `EFFORT = "low"`, set explicitly on every request. Haiku 5.5 defaults to medium.
- `build_payload(flag_rows)` keeps only whitelisted flag fields: metric, count, shift name, login code, approval code, evidence times, business day. Any other key is dropped, including display names, events and history.
- `explain(flag_rows, client)` sends the prompt from `tillowl/digest/templates/explain_prompt.txt` (STEP-23; loaded through `tillowl.digest.facts.load_templates()`) with the payload. It splits requests so that each request stays under 100,000 input tokens. A single flag that alone exceeds the limit is refused, and its flag falls back to the template line.
- One `explanation` row per flag, with text only. The checker (STEP-24) judges the text later in STEP-26.
- One `llm_usage` row per call: model id, input tokens, output tokens and, when reported separately, thinking tokens. Both tables come from STEP-08's schema.

`tillowl/jobs/run_explain.py` runs it per tenant. In production it stays off behind `TILLOWL_JOBS_ENABLED` until STEP-43. With `TILLOWL_LLM_ENABLED` not `1` (default `0`), no client is built, no API call is made, no explanation rows are written, and the digest uses template lines (design choice 22; T8 or D11).

Unverified candidate, which the session must re-check against the current Anthropic docs and SDK, citing the URL in the PR:
- [Effort](https://platform.claude.com/docs/en/build-with-claude/effort) says effort is set with `output_config={"effort": "low"}`, that Haiku 5.5 supports `low`, and that its thinking is on by default.
- [Thinking](https://platform.claude.com/docs/en/build-with-claude/thinking) says thinking is "billed as output tokens" and documents no separate usage field.

## Acceptance criteria
1. Given `tests/gates/step_25/fixtures/flags_for_explain.json`, `pytest -c pytest.ini --rootdir=. tests/gates/step_25` passes. The fixture holds synthetic flags; some carry a `display_name` sentinel and a `history` list.
2. `test_explanation_stubbed.py` uses a stub client that records every request; the Anthropic client is stubbed in every test, and no test opens a network connection. For every fixture flag and generated flag:
   - the request's model is exactly `claude-haiku-5-5`;
   - effort is `low`, set explicitly;
   - the payload holds only whitelisted fields, and no sentinel, display name or history appears anywhere in the request;
   - each call writes exactly one `llm_usage` row whose token counts equal the stub's usage values;
   - output tokens are recorded as billed, thinking included.
3. `test_prompt_limits.py` covers prompts below, at and above 100,000 tokens, using the token-counting method the docs describe (stubbed): every request sent is under the limit, batches cover each flag exactly once, and a flag over the limit alone is refused without a call.
4. `test_llm_switch.py` covers `TILLOWL_LLM_ENABLED` unset, `0`, `false` and `1`: only `1` builds a client. In the other cases the stub records zero calls and zero explanation and usage rows.
5. A client error or timeout writes no explanation row for that batch and exits non-zero with a reason code; no retry storm. The digest then uses template lines (P5: off the service path).
6. `claude-haiku-5-5` appears in exactly one place in `tillowl/`; no other model id appears there.
7. Gate tests pin `tillowl.config.V_ITEMS` explicitly with monkeypatch wherever a payload field could depend on it (BUILD_PLAN §7); no test reads `square-fields.md`.
8. If `explanation` or `llm_usage` is missing from STEP-08's schema, stop and set `blocked` (`needs_schema_tables`). Adding a tenant table needs RLS, so it comes through a gate-change migration (design choice 33).

## Out of scope
- Any real model call. Real calls happen only in STEP-41, in the founder's terminal.
- Judging sentences (STEP-24); building or sending the digest (STEP-26).
- Writing the prompt file (STEP-23); turning on production LLM calls (T8, D11, STEP-43); disabling thinking.

## Gate
`pytest -c pytest.ini --rootdir=. tests/gates/step_25` (exact, from `docs/build/status/STEP-25.json`). Gate files: `docs/build/gates/STEP-25.txt`.

`docs/build/evidence/STEP-25.md`: `command:`, `exit_code: 0`, `count: N passed`, `run_id:`, `date:`.
- `run_id` is the green `ci` push run on main for the evidence commit's parent.
- `count` comes from that run.

## If the gate fails
Revert to the last green commit. Set `blocked` with a `blocked_reason` (no names or values). After two failed attempts, restart in a fresh session with a narrower prompt. Never set `TILLOWL_LLM_ENABLED=1` or use a real API key to make a test pass.

## Prompt (paste into a fresh Claude Code session)
```text
You are running STEP-25 "Explanation service with the model stubbed" for TillOwl. Follow @CLAUDE.md throughout.
Start: git fetch && git rebase origin/main; confirm STEP-08 and STEP-23 are "done" in docs/build/status/ (stop and say which if not); read git log -5; run CLAUDE.md's setup command; read @docs/build/steps/STEP-25-explanation-service.md, @tillowl/config.py, the migrations in @migrations/,, @tillowl/digest/facts.py, @tillowl/digest/templates/explain_prompt.txt (STEP-23; read it, never edit it) and Slides 5, 13, 19, 21, 22, 30 in @docs/architecture-pack-part1.md and @docs/architecture-pack-part2.md.
Before writing code, use WebFetch on the current Anthropic docs (effort, extended thinking, token counting, the Messages API usage object) and the installed anthropic SDK. Confirm how effort is set, how tokens are counted, and how thinking tokens appear in usage; cite each URL in the PR description. Use no parameter name you have not seen there.
Step PR, test first:
- Set docs/build/status/STEP-25.json status to "in_progress".
- Write the three tests and the fixture exactly as listed in docs/build/gates/STEP-25.txt, to the acceptance criteria. Use synthetic flags only and a stub client; no network; pin V_ITEMS with monkeypatch where relevant. Run them; they fail (print RED TEST (intentional) if you stop here).
- Write tillowl/explain/ and tillowl/jobs/run_explain.py. Run the gate command and CLAUDE.md's test command; show each command and its output; never claim success without it. Commit; open the step PR with gh. It merges when CI is green.
Done PR: one commit on top of main holding only docs/build/evidence/STEP-25.md and status "done". run_id is the green ci push run on main for that commit's parent, and count: N passed comes from that run (gh run view <id> --log). Run python tools/check_evidence.py validate --step STEP-25, show the output, and open the PR with gh.
Out of scope: real model calls, the checker, digest delivery, the prompt file's wording, enabling production LLM calls.
Use a subagent to review the diff against this step file and report only gaps that affect correctness or the stated acceptance criteria.
```
