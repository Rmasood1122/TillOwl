# STEP-12 First sandbox consent on staging (our own sandbox seller)

Track: human. Lane: connector. Gate kind: human. Size: S.
Depends on: STEP-11 Square OAuth connect. Done requires: none.
Blocks: STEP-13 production environment.
Sources: Slide 5 (A1: OAuth consent on Square's screen), Slides 10–11 (V2, V4), Slide 21 (personal tokens only on our own test account), Slide 24 (scenario 4: refresh every 7 days or less); BUILD_PLAN §7 (STEP-12's commands run as one-off jobs on the staging service; `provision_tenant` built in STEP-10), design choices 4, 14; the planning prompt's "No real sends in CI" (the first sandbox consent is a human gate).

## Outcome
Preconditions, done by the founder in their own dashboards and terminal (no value ever enters the session):
- **STEP-11's config checklist** on the Render staging service: the Square sandbox application id and secret, `TILLOWL_AES_KEY` and `TILLOWL_PUBLIC_URL` are set, and the staging redirect URL is registered in the sandbox application. For the invite: `TILLOWL_OWNER_EMAIL_OWN` is the founder's own address and `TILLOWL_EMAIL_MODE` is switched from `stub` to the email vendor, with its key.
- **Staging owner.** The founder ran `python -m tillowl.jobs.provision_tenant --kind own --env staging` as a Render one-off job on the staging service (output `count: 1 tenants`, `date:`, `exit_code: 0`), opened the enrollment link and enrolled TOTP (STEP-10).

Then the founder has done the following:
1. Signed in to the **staging** console as that staging owner, with TOTP.
2. Clicked Connect Square, and approved consent for **our own Square sandbox test seller**, never the friend's account and never a production seller.

Staging now holds exactly one active `oauth_connection`, with the full `SQUARE_SCOPES` list, including the roster-read scope (design choice 14). A forced refresh of it works.

Square's docs say a sandbox test can't sign in directly on the authorization page: open the Sandbox Dashboard for the test seller first, then use the authorization URL ([OAuth overview](https://developer.squareup.com/docs/oauth-api/overview), unverified candidate). If that doesn't match what the founder sees, record what happened in the PR description as codes only. STEP-01's `sandbox_oauth_flow` finding then needs a gate-change PR.

## Acceptance criteria
1. `oauth_status --env staging --expect-connections 1` exits 0. That means:
   - exactly one active connection;
   - it decrypts with the staging AES key;
   - it was refreshed within 7 days;
   - its scopes equal `SQUARE_SCOPES`.
2. `refresh_tokens --env staging --force` exits 0 with `count: 1 refreshes`. The connection is not left with `reconnect_needed`.
3. The connection came through the OAuth consent screen, never a personal access token.
4. The seller is our sandbox test seller, so staging still holds synthetic data only.
5. The pasted output holds only evidence-grammar lines. No token, merchant id, email or name enters the session, the PR or the evidence.

## Human confirmation
"Founder: (1) Is STEP-11's config checklist done on the staging service and in the sandbox application, plus the owner-email and email-mode settings? (2) Did `provision_tenant --kind own --env staging` exit 0, and did you enroll TOTP from its link? (3) Signed in to the staging console as that owner, did you click Connect Square and approve consent for OUR Square sandbox test seller (not the friend's account, not production)? Then run the two one-off jobs below on the staging service and paste their output." Print AWAITING HUMAN CONFIRMATION and wait.

## Out of scope
Production (STEP-13, 16); the friend's account; any code change (if a job fails, fix it in a STEP-11 gate-change or follow-up PR, not here); reading orders or the roster.

## Gate
Exact, from `docs/build/status/STEP-12.json`. The founder runs each half as a Render one-off job on the staging service, from the founder's own terminal:

`python -m tillowl.jobs.oauth_status --env staging --expect-connections 1 && python -m tillowl.jobs.refresh_tokens --env staging --force`

No gate test files (see `docs/build/gates/STEP-12.txt`). `docs/build/evidence/STEP-12.md` holds two blocks, one per command:
- `command:`, `count: 1 connections`, `count: N scopes`, `date:`, `exit_code: 0`;
- `command:`, `count: 1 refreshes`, `count: 1 connections`, `date:`, `exit_code: 0`.

These are job-only human gates, so no `role` or `job_id` line is required (BUILD_PLAN §7). A `job_id:` line Render printed may be kept.

## If the gate fails
- Set `blocked` with a `blocked_reason` code (`consent_not_completed`, `connection_count_mismatch`, `forced_refresh_failed`), never output values.
- If a job is wrong, fix it through a new PR against STEP-11's code; its gate files need a gate-change PR once STEP-11 is done.
- After two failed attempts, restart in a fresh session with a narrower prompt.
- Never connect a different seller to make the count match.

## Prompt (paste into a fresh Claude Code session, run from an engineer's account)
```text
You are running STEP-12 "First sandbox consent on staging" for TillOwl. Follow @CLAUDE.md throughout.
Start: git fetch && git rebase origin/main; confirm STEP-11 is "done" in docs/build/status/STEP-11.json (stop and say so if not); read git log -5; run CLAUDE.md's setup command; read @docs/build/steps/STEP-12-sandbox-consent.md and Slides 5, 10, 11, 21, 24 in @docs/architecture-pack-part1.md and @docs/architecture-pack-part2.md.
This is a human step. Never use the Render CLI, never hold staging or production credentials, and never ask for a token, merchant id or email.
1. Print the founder's checklist (setting names only, never values): STEP-11's config checklist on the staging service and sandbox application; TILLOWL_OWNER_EMAIL_OWN and TILLOWL_EMAIL_MODE on staging; run python -m tillowl.jobs.provision_tenant --kind own --env staging as a one-off job on the staging service and enroll TOTP from the emailed link; sign in to the staging console as that owner; open our sandbox test seller's Sandbox Dashboard first (Square docs, unverified candidate); click Connect Square; approve consent.
2. Print the two commands for the founder's own terminal, each as a Render one-off job on the staging service (render jobs create <staging service id> --start-command "..."; syntax is an unverified candidate from BUILD_PLAN §10):
   python -m tillowl.jobs.oauth_status --env staging --expect-connections 1
   python -m tillowl.jobs.refresh_tokens --env staging --force
   Then print the human-confirmation line and AWAITING HUMAN CONFIRMATION; wait.
3. From the founder's pasted output only: write docs/build/evidence/STEP-12.md (two blocks, allowlisted lines only), set status "done" (straight from not_started), run python tools/check_evidence.py validate --step STEP-12 and show the output, then open the PR with gh. Its description says the founder must approve and then re-run the founder-approval check. Never claim success without the pasted output.
Out of scope: production, the friend's account, code changes, orders, roster.
Use a subagent to review the diff against this step file and report only gaps that affect correctness or the stated acceptance criteria.
```
