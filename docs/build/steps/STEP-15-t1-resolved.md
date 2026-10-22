# STEP-15 T1 resolved: Square production approval granted, or confirmed not required

Track: human. Lane: vendor. Gate kind: human. Size: W (waits on Square).
Depends on: STEP-01 Square-sandbox spike (scope names and `approval_rule`), STEP-13 production environment (the production redirect URL is live). This is D5's default branch. Done requires: none. D15 (the legal entity that owns the Square application) must be recorded in BUILD_PLAN §12 first.
Blocks: STEP-16 production OAuth check, STEP-20 live spike, STEP-43 pilot-readiness gate.
Sources: Slide 3 (T1: partner apps must use OAuth), Slide 25 (ADR-003: "Square app approval is unconfirmed"), Slide 26 (before day one: Square connected through OAuth), Slide 28 (N12), Slide 30 (T1); BUILD_PLAN §1 (T1 starts after the spike), §3 "T1 dependency"; D5, D15.

## Outcome
T1's second half is closed for the Square application owned by the D15 entity. The first half, the scope names, was closed by STEP-01. Which branch applies depends on `approval_rule` in `docs/build/findings/square-sandbox.md`:
- **`REDIRECT_URL_ONLY` (default):**
  - The founder registers the production redirect URL in the app's production settings. That URL is `TILLOWL_PUBLIC_URL` + `SQUARE_REDIRECT_PATH`, the one STEP-13's `redirect_check` proved live.
  - The founder then follows whatever Square's process requires.
  - Square's approval notice is saved as `STEP-15/t1_approval.<ext>` (role `vendor`).
- **`NOT_REQUIRED`:**
  - The founder saves a dated copy of Square's official statement that no approval is needed, as `STEP-15/t1_not_required.<ext>` (role `vendor`).
  - A founder-approved gate-change PR then swaps the gate's label to `--label t1_not_required --role vendor`.
- **`UNCLEAR`:**
  - The founder asks Square in writing, through a support channel.
  - Square's written answer is the artifact, under whichever label it supports.
- **`WORKING_CONNECT_REQUIRED`:**
  - D5's alternate branch applies, before this step starts. A founder-approved gate-change PR sets STEP-16 to depend on STEP-14 only, and this step to depend on STEP-16 (BUILD_PLAN §3).
  - This step then runs after our own production connect works.

What the docs say so far (unverified candidates, not a basis on their own; STEP-01's `approval_rule` governs):
- [Move OAuth to production](https://developer.squareup.com/docs/oauth-api/movetoprod) asks for production credentials and an HTTPS production redirect URL. It names no approval or review step.
- A Square staff answer on Square's developer forum (Feb 1, 2023, [thread](https://developer.squareup.com/forums/t/do-we-need-to-get-approved-to-use-our-square-integration-in-production/8413)) says production credentials work once the app is created unless it is listed in the App Marketplace. This is a forum post, not an official doc page.

Don't describe any other approval process. Square's process beyond these pages is TBD — not in sources.

## Acceptance criteria
1. **What the artifact is.** It is Square's own words, not ours: an approval notice, a dated copy of an official Square doc page, or Square support's written answer. It names our application, holds no seller data, and is dated.
2. **Redirect URL.** The production redirect URL registered with Square equals the one `redirect_check` proved live. The founder confirms this; no Claude session reads Square's dashboard.
3. **D15.** The application belongs to the D15 entity. If it doesn't, the step is not done.
4. **Order.** Under the default branch, no production OAuth with any seller happens before this step is done: STEP-16 waits for it.
5. **What enters the repo.** No Square credentials, application ids, emails or names enter the repo, the evidence or a Claude session.

## Human confirmation
"Founder, please confirm:
- Is Square's notice saved as `STEP-15/t1_approval.<ext>` in your evidence folder? (Or, after the gate-change PR, the statement saved as `STEP-15/t1_not_required.<ext>`.)
- Which entity owns the Square application (D15)?
- Does the production redirect URL in Square's app settings equal the URL STEP-13's `redirect_check` proved live?"

Print AWAITING HUMAN CONFIRMATION and wait.

## Out of scope
Any production connect (STEP-16, except under the `WORKING_CONNECT_REQUIRED` branch); App Marketplace listing; changing scopes (that reopens STEP-01 and T17a); writing to Square.

## Gate
`python tools/check_artifact.py --step STEP-15 --label t1_approval --role vendor` (exact, from `docs/build/status/STEP-15.json`; the `NOT_REQUIRED` branch changes the label only through the gate-change PR). The founder runs it in their own terminal. No gate test files (see `docs/build/gates/STEP-15.txt`).

`docs/build/evidence/STEP-15.md` holds the pasted block: the command with `--date`, `exit_code: 0`, `sha256: … label=t1_approval` (or `t1_not_required`), `role: vendor`, `date:`.

## If the gate fails
- Fix the artifact's name or folder and re-run. Never move the copy into the repo.
- If Square refuses or asks for changes, set `blocked` with `blocked_reason: t1_rejected` or `t1_changes_requested`, and raise it with the founder. A scope change reopens STEP-01 and T17a.
- After two failed attempts, restart in a fresh session with a narrower prompt.

## Prompt (paste into a fresh Claude Code session, run from an engineer's account)
```text
You are running STEP-15 "T1 resolved: Square production approval" for TillOwl. Follow @CLAUDE.md throughout.
Start: git fetch && git rebase origin/main; confirm STEP-01 and STEP-13 are "done" in docs/build/status/ and D15 is recorded in BUILD_PLAN §12 (stop and say which if not); read git log -5; run CLAUDE.md's setup command; read @docs/build/steps/STEP-15-t1-resolved.md, @docs/build/findings/square-sandbox.md, BUILD_PLAN §3 "T1 dependency", and Slides 3, 25, 26, 28, 30 in @docs/architecture-pack-part1.md and @docs/architecture-pack-part2.md.
This is a human step. Never read $PRIVATE_EVIDENCE_DIR and never run tools/check_artifact.py yourself.
1. Read approval_rule. If it is WORKING_CONNECT_REQUIRED and docs/build/status/STEP-15.json still depends on STEP-13, stop: tell the founder D5's alternate branch needs a gate-change PR first. If it is NOT_REQUIRED and the gate still says t1_approval, tell the founder the label swap needs a gate-change PR first.
2. Use WebFetch on Square's current official docs for moving OAuth to production; print a short checklist for the founder, citing each URL as an unverified candidate. Don't add steps the pages don't state.
3. Print the command for the founder's own terminal, with the D4 absolute path from BUILD_PLAN §1 written out:
   PRIVATE_EVIDENCE_DIR=<absolute path> python tools/check_artifact.py --step STEP-15 --label t1_approval --role vendor --date YYYY-MM-DD
   Then print the human-confirmation line and AWAITING HUMAN CONFIRMATION; wait.
4. From the founder's pasted output only: write docs/build/evidence/STEP-15.md, set status "done", run python tools/check_evidence.py validate --step STEP-15 and show the output, then open the PR with gh. Its description says the founder must approve and then re-run the founder-approval check. Never claim success without the pasted output.
Out of scope: production connect, App Marketplace, scope changes, writes to Square.
Use a subagent to review the diff against this step file and report only gaps that affect correctness or the stated acceptance criteria.
```
