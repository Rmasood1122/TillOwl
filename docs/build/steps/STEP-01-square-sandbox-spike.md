# STEP-01 Square-sandbox spike (API shape of V1–V8, scopes, approval rule)

Track: build. Lane: connector. Gate kind: sandbox_spike. Size: M.
Depends on: none (M0 governance installed first). Done requires: none.
Blocks: STEP-02 counsel T17a (done), STEP-08 skeleton, STEP-11 OAuth connect, STEP-15 T1 resolved, STEP-18 criteria (done).
Sources: Slide 3 (T1, T2), Slide 19–20 (Square integration, known gaps), Slide 21 (personal token only on our own test account), Slide 30 (V1–V8, T1); BUILD_PLAN §10, §12 (D5, D6).

## Outcome
`docs/build/findings/square-sandbox.md` records, from observation and Square's official docs:
- `scope:` lines, one per read-only OAuth scope v1 needs, covering orders, refunds, discounts, cash-drawer events and team members for the roster read. This is T1's first half.
- `approval_rule: REDIRECT_URL_ONLY | WORKING_CONNECT_REQUIRED | NOT_REQUIRED | UNCLEAR`, with the doc URLs it rests on. This is the input to D5 and STEP-15; the sandbox can't show it.
- `sandbox_oauth_flow: YES | NO`. If NO, D6 must be decided before STEP-11.
- One `v_shape:` line per V1–V8 (`CAN_RETURN`, `CANNOT_RETURN` or `NOT_OBSERVABLE_IN_SANDBOX`), each followed by `field:` lines (name and type, never values) and the API call that returned them.

## Acceptance criteria
1. `spikes/square_sandbox.py` uses only the standard library. Its host constant is `https://connect.squareupsandbox.com` (Square's docs; unverified until this step). It refuses any other host and reads the token only from `SQUARE_SANDBOX_TOKEN`.
2. `--probe` makes only GET or search (read) calls and prints only evidence-grammar lines: `scope:`, `field:`, `v_shape:`, `count:`, then `date: YYYY-MM-DD` (UTC) and `exit_code: N` last. Given a response containing a person's name or an amount, the output contains the field name and type only.
3. `--seed` (optional, design choice) creates synthetic orders in **our own sandbox seller only**, with one cancelled, one refunded and one discounted, so `--probe` has something to observe. It never runs in the gate.
4. `--check [--findings PATH]` exits 0 only if the findings file has at least one `scope:` line, an `approval_rule:` with at least one `https://developer.squareup.com/` URL, a `sandbox_oauth_flow:` line, and exactly one `v_shape:` per V1–V8. Otherwise it exits 1 and names the missing item. Its output also ends with `date:` then `exit_code:`.
5. `tests/gates/step_01/test_sandbox_check.py` runs `--check` on both fixtures: `findings_complete.md` exits 0 and `findings_missing_item.md` (no V6 line) exits 1. It needs no network.
6. V3 (item voids on paid checks) and V6 (no-sale opens) may be `NOT_OBSERVABLE_IN_SANDBOX`, since Square Point of Sale can't be used in the sandbox (unverified candidate, https://developer.squareup.com/docs/devtools/sandbox/overview). Record that; don't guess.

## Human confirmation
"Confirm that `SQUARE_SANDBOX_TOKEN` in this shell is the personal access token of **our own** Square sandbox test seller (never the friend's), and whether `--seed` may create synthetic orders there." Print AWAITING HUMAN CONFIRMATION and wait.

## Out of scope
Any production Square call, OAuth code (STEP-11), the friend's account, rules, digests, storing any response body.

## Gate
`python spikes/square_sandbox.py --probe && python spikes/square_sandbox.py --check` (exact, from `docs/build/status/STEP-01.json`). Gate files: `docs/build/gates/STEP-01.txt`.

`docs/build/evidence/STEP-01.md` holds the `--probe` block (its `scope:`, `v_shape:`, `field:`, `count:` lines, `date:` and `exit_code: 0`) and the `--check` block with `sha256: <hex> label=findings`, `date:` and `exit_code: 0` (from `sha256sum docs/build/findings/square-sandbox.md`). CI recomputes that hash.

## If the gate fails
Revert to the last green commit. Set the status to `blocked` with a `blocked_reason` (no tokens, names or values). After two failed attempts, restart in a fresh session with a narrower prompt. If the sandbox lacks an OAuth flow, that is a finding, not a failure: record `sandbox_oauth_flow: NO` and flag D6.

## Prompt (paste into a fresh Claude Code session)
```text
You are running STEP-01 "Square-sandbox spike" for TillOwl. Follow @CLAUDE.md throughout.
Start:
1. git fetch && git rebase origin/main
2. This step has no depends_on. Read git log -5.
3. Run CLAUDE.md's setup command.
4. Read @docs/build/steps/STEP-01-square-sandbox-spike.md, then Slides 3, 19, 20, 21 and 30 in @docs/architecture-pack-part1.md and @docs/architecture-pack-part2.md.
5. Print the human-confirmation line from the step file and AWAITING HUMAN CONFIRMATION; wait.
Work, test first:
- Set docs/build/status/STEP-01.json status to "in_progress".
- Write tests/gates/step_01/test_sandbox_check.py and both fixtures exactly as listed in docs/build/gates/STEP-01.txt; run them; they fail (RED TEST (intentional) if you stop here).
- Write spikes/square_sandbox.py (--probe, --seed, --check) to the acceptance criteria. Read Square's official docs with WebFetch for scope names and the production-approval rule; cite each URL in the findings.
- Run --probe (and --seed only if the founder said yes), then write docs/build/findings/square-sandbox.md from the printed lines only. No values, no names.
- Run the test command from CLAUDE.md; commit; open the step PR with gh (status in_progress).
Done PR (after the step PR merges): add docs/build/evidence/STEP-01.md from the real command output (see docs/build/evidence/README.md), set status "done", open the PR. Show every command and its output; never claim success without it.
Out of scope: production Square, the friend's account, OAuth code, rules, digests.
End: Use a subagent to review the diff against this step file and report only gaps that affect correctness or the stated acceptance criteria.
```
