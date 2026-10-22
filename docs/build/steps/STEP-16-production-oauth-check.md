# STEP-16 Production OAuth check on our own Square account (connect, refresh, revoke)

Track: build. Lane: connector. Gate kind: production_job. Size: S.
Depends on: STEP-14 Provision our own production tenant, STEP-15 T1 resolved (default T1 branch, D5). Done requires: none.
Blocks: STEP-20 Run the read-only live spike.
Sources: Slide 3 (T1: OAuth only, tokens expire every 30 days), Slides 19–20 (I1: refresh every 7 days or less, AES-encrypted), Slide 21 (encrypted OAuth tokens; personal tokens only on our own test account), Slide 24 (scenario 4), Slide 30 (T1), ADR-003; BUILD_PLAN §1, §3, §7, design choices 5, 25, 29, 30; D5, D15.

## Outcome
- `tillowl/jobs/oauth_check.py`: a one-off production job that, for tenant `own` only, checks the connection the founder made in the production console:
  - **connect**: exactly one stored connection, and its token decrypts in the job's process with the production AES key;
  - **refresh**: a forced refresh through STEP-11's refresh path in `tillowl/square/oauth.py`;
  - **revoke**: a revoke through `revoke()` in the same module, then proof that Square no longer accepts the old token.
- It prints `count: 1 connections`, `count: 1 refreshes`, `count: 1 revokes`, then `exit_code: 0`.
- `revoke()` in `tillowl/square/oauth.py`, if STEP-11 didn't build it. STEP-20 (if D7 is revoke) and STEP-22 reuse it. Square's revoke endpoint comes from Square's official OAuth docs, cited in the PR as an unverified candidate.
- One `audit()` row per check: actor `job:oauth_check`, target tenant `own`, result code. No token, ciphertext or merchant id.

## Acceptance criteria
1. `--tenant` other than `own` exits 1 before any decryption or Square call. This job can never touch the friend's account.
2. Given `tests/gates/step_16/test_oauth_check.py` (Square mocked with `httpx.MockTransport`, local test database), the job exits 0 only when all of these hold:
   - tenant `own` has exactly one connection before the check;
   - the forced refresh stores a new ciphertext and a later `refreshed_at` and `expires_at`;
   - the revoke call succeeds and the stored token is gone;
   - a later refresh with the old credentials is refused.
   For zero or two connections, a refresh error, a revoke error, or a token still accepted after revoke, it exits 1 and prints no `count:` line for the failed check. The failed check is named by its audit row's code (`connect`, `refresh`, `revoke`).
3. For every mocked response, error bodies included, stdout holds only evidence-grammar lines. No token, ciphertext, merchant id or URL appears in stdout or audit rows.
4. Tokens stay AES-256-GCM at rest (design choice 5). The job makes no POS read: no orders, refunds, team or cash-drawer call.
5. Tenants other than `own` are untouched: their connection rows, ciphertexts and `refreshed_at` are byte-identical after the run (tested with a seeded second tenant).

## Human confirmation
"Founder: is our own Square production seller account open under the D15 entity (never the friend's; BUILD_PLAN §1 records none yet)? Is tenant `own` provisioned (STEP-14)? Have you deployed this release to production yourself? If so, sign in to the production console as tenant `own`'s owner with TOTP, click Connect Square, approve the consent screen, and reply 'connected'." Print AWAITING HUMAN CONFIRMATION and wait.

## Out of scope
The friend's account and the pilot tenant (STEP-17, STEP-20). Any POS read. Scheduling anything: only `refresh_tokens` with `watchdog` stays scheduled. Square approval paperwork (STEP-15). Personal access tokens.

## T1 branch (D5)
This file follows the default branch: STEP-16 depends on STEP-15. If STEP-01 found that Square approval needs a working production connect, a founder-approved gate-change PR makes STEP-16 depend on STEP-14 only and STEP-15 depend on STEP-16. The job is the same either way.

## Gate
`python -m tillowl.jobs.oauth_check --tenant own` (exact, from `docs/build/status/STEP-16.json`). Gate files: `docs/build/gates/STEP-16.txt`. `tillowl/jobs/oauth_check.py` is frozen once this step is done.

The founder launches the job as a Render one-off job from their own terminal: `render jobs create <service id> --start-command "…"` (unverified candidate, BUILD_PLAN §10). `docs/build/evidence/STEP-16.md` holds one block:
- `command:` equal to the gate;
- `exit_code: 0`;
- `job_id:`;
- the three `count:` lines;
- `date:`.

## If the gate fails
- Revert to the last green commit.
- Set the status to `blocked` with `blocked_reason: oauth_check_<connect|refresh|revoke>`. No tokens, ids or values.
- After two failed attempts, restart in a fresh session with a narrower prompt.
- A re-run needs the founder to reconnect first, because the revoke removed the connection.
- Never point this job, or a variant of it, at the pilot tenant.

## Prompt (paste into a fresh Claude Code session)
```text
You are running STEP-16 "Production OAuth check on our own Square account" for TillOwl. Follow @CLAUDE.md throughout.
Start:
1. git fetch && git rebase origin/main
2. Confirm STEP-14 and STEP-15 are "done" in docs/build/status/STEP-14.json and STEP-15.json; if not, stop and say which. Read git log -5.
3. Run CLAUDE.md's setup command.
4. Read @docs/build/steps/STEP-16-production-oauth-check.md, @tillowl/square/oauth.py, @docs/build/findings/square-sandbox.md, and Slides 3, 19, 20, 21, 24, 25, 30 in @docs/architecture-pack-part1.md and @docs/architecture-pack-part2.md.
You never hold production credentials, never use the Render CLI and never connect to a production database.
Body, test first:
5. Set docs/build/status/STEP-16.json status to "in_progress".
6. Write tests/gates/step_16/test_oauth_check.py to acceptance criteria 1–5 (Square mocked with httpx.MockTransport, the root conftest's local database). Run it; it fails. Print RED TEST (intentional) if you stop here.
7. Implement tillowl/jobs/oauth_check.py, and revoke() in tillowl/square/oauth.py if it is missing. Cite Square's revoke doc URL in the PR as an unverified candidate.
8. Run CLAUDE.md's test command and show its output. Commit, then open the step PR with gh (status in_progress, job code and tests). It merges on review.
Run phase (after the step PR merges):
9. Print the human-confirmation line from the step file and AWAITING HUMAN CONFIRMATION; wait.
10. Print for the founder's own terminal: deploy the merged release to production by hand, then
    render jobs create <production service id> --start-command "python -m tillowl.jobs.oauth_check --tenant own"
    (unverified candidate; the founder checks `render jobs create --help`). Ask for the job id, exit code and full output. Print AWAITING HUMAN CONFIRMATION; wait.
Evidence and done PR:
11. From the pasted output only, write docs/build/evidence/STEP-16.md (command, exit_code: 0, job_id, the three count lines, date) and set the status to "done".
12. Run python tools/check_evidence.py validate --step STEP-16 and show its output. Open the done PR with gh. Its description says the founder approves and then re-runs founder-approval. Never claim success without the pasted output.
Out of scope: the friend's account or tenant, POS reads, scheduling any job, STEP-15 paperwork.
Use a subagent to review the diff against this step file and report only gaps that affect correctness or the stated acceptance criteria.
```
