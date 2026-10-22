# STEP-40 Counsel review T17b (fact templates, explanation prompt, deny-list, sample outputs)

Track: human. Lane: legal. Gate kind: human. Size: W (waits on counsel).
Depends on: STEP-25 Explanation service with the model stubbed, STEP-26 Digest build and delivery, STEP-38 V-item branches in templates and checker, STEP-39 Pass-line measurement (D10 may add a template link), STEP-41 Metered cost estimate (its saved real-model samples). Done requires: none. Runs only if STEP-21 recorded GO (`runs_if: "GO"`).
Blocks: STEP-43 pilot-readiness gate.
Sources: Slide 21 (fact-based wording; "Have NY employment counsel review the notice and digest templates before the pilot: TBD"), Slide 3 (P4, L4, L5), Slide 13 step 9, Slide 24 (scenario 2), Slide 29 (RK3: "counsel reviews the templates"), Slide 30 (T17), ADR-006; BUILD_PLAN §7 (templates, findings), design choices 8, 21, 22, 23, 32; D11.

## Outcome
NY employment counsel's signed review of the exact template set is on file, and its manifest hash is recorded. Counsel reviews:
1. every file listed in `tillowl/digest/templates/MANIFEST.json`: the fact templates (both fallback sentences and every V-item branch from STEP-38), the explanation prompt (STEP-25) and the deny-list (STEP-24);
2. the real-model sample outputs saved by STEP-41 in `docs/build/findings/llm-samples.md` (synthetic data only), in the version whose SHA-256 is in STEP-41's evidence.

`docs/build/evidence/STEP-40.md` records `sha256: … label=counsel_t17b` and `sha256: … label=template_manifest`. From then on CI fails any template change, any file in the templates folder missing from the manifest, and any manifest whose hash differs from this evidence (`check_evidence.py`, BUILD_PLAN §7).

## Acceptance criteria
1. Counsel's signed review names the manifest SHA-256 that this step prints before review, and that hash equals the one `python tools/check_evidence.py manifest` prints at the end. If they differ, the step is not done.
2. Counsel confirms in writing that the wording:
   - states facts only;
   - never labels anyone ("thief" or a deny-list word);
   - never suggests a wage deduction (L4);
   - never presents a flag as the only basis for a firing;
   - goes to the owner only (L5, Slide 21);
   - gives the LLM login codes only, never display names.
3. If counsel asks for changes, they land in a separate template PR first. Before T17b is done that PR needs only code-owner review (design choice 32). Counsel then reviews the new manifest hash. Nothing is recorded for a hash counsel did not see.
4. The session never reads `$PRIVATE_EVIDENCE_DIR` and never runs `tools/check_artifact.py`. Counsel's advice text stays out of the repo; only hashes, role and date enter the evidence.
5. If D11 (template-only production) is recorded, counsel still reviews the explanation prompt and samples, because they are in the manifest and STEP-41's findings.

## Human confirmation
"Founder: did counsel sign a review naming manifest SHA-256 `<hash printed above>`, and is it saved as `STEP-40/counsel_t17b.<ext>` in your evidence folder? Paste the output of the command below." Print AWAITING HUMAN CONFIRMATION and wait.

## Out of scope
Editing templates inside this step (changes go in their own PR, then back to counsel); T17a (STEP-02); the cost estimate itself (STEP-41); drafting legal advice.

## Gate
Exact, from `docs/build/status/STEP-40.json`:
`python tools/check_artifact.py --step STEP-40 --label counsel_t17b --role counsel && python tools/check_evidence.py manifest`
The founder runs the first command in their own terminal. The session runs the second while STEP-40's status is still `not_started`. No gate test files (see `docs/build/gates/STEP-40.txt`).

`docs/build/evidence/STEP-40.md` holds two blocks:
1. the founder's pasted block: command with `--date`, `exit_code: 0`, `sha256: … label=counsel_t17b`, `role: counsel`, `date:`;
2. the manifest block: command, `exit_code: 0`, `sha256: … label=template_manifest`, `date:`.

**Any later template change reopens T17b.** It needs a founder-approved gate-change PR that changes the templates and the manifest and sets STEP-40 back from `done`. STEP-40 then runs again, and STEP-43's `pilot-gate` fails until it is done.

## If the gate fails
`check_artifact.py` names the problem without paths: fix the file name or folder and re-run. If `check_evidence.py manifest` reports a template that is missing or changed, or a hash other than the one counsel signed, stop: re-send the current set to counsel. If counsel won't sign off, set the status to `blocked` with `blocked_reason: t17b_changes_requested`.

## Prompt (paste into a fresh Claude Code session, run from an engineer's account)
```text
You are running STEP-40 "Counsel review T17b" for TillOwl. Follow @CLAUDE.md throughout.
Start: git fetch && git rebase origin/main; confirm STEP-25, STEP-26, STEP-38 and STEP-41 are "done" in docs/build/status/ and "decision" in STEP-21.json is "GO" (stop and say which if not); read git log -5; run CLAUDE.md's setup command; read @docs/build/steps/STEP-40-counsel-t17b.md, @tillowl/digest/templates/MANIFEST.json, @docs/build/findings/llm-samples.md, and Slides 3, 13, 21, 24, 29, 30 in @docs/architecture-pack-part1.md and @docs/architecture-pack-part2.md.
This is a human step. Never read $PRIVATE_EVIDENCE_DIR and never run tools/check_artifact.py yourself.
1. Run python tools/check_evidence.py manifest and show the output. Print the review package for the founder to send counsel: the commit SHA (git rev-parse HEAD), the manifest SHA-256, each manifest file with its hash, the llm-samples.md SHA-256 (sha256sum), and the questions in acceptance criterion 2.
2. Print the command for the founder's own terminal, with the D4 absolute path from BUILD_PLAN §1 written out:
   PRIVATE_EVIDENCE_DIR=<absolute path> python tools/check_artifact.py --step STEP-40 --label counsel_t17b --role counsel --date YYYY-MM-DD
   Then print the human-confirmation line and AWAITING HUMAN CONFIRMATION; wait.
3. From the founder's reply only: re-run python tools/check_evidence.py manifest (status still not_started) and show the output; if its hash differs from the one counsel signed, stop and say so. Write docs/build/evidence/STEP-40.md (the pasted block, then the manifest block), set status "done", run python tools/check_evidence.py validate --step STEP-40 and show the output, then open the PR with gh. Its description says the founder must approve and then re-run the founder-approval check.
Out of scope: template edits, T17a, the cost estimate, legal drafting.
End: Use a subagent to review the diff against this step file and report only gaps that affect correctness or the stated acceptance criteria.
```
