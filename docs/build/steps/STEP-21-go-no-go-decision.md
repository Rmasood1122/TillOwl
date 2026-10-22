# STEP-21 Go/no-go decision recorded (RK1)

Track: human. Lane: gate. Gate kind: human. Size: S.
Depends on: STEP-20 Run the read-only live spike. Done requires: none.
Blocks: on NO-GO, STEP-22 no-go exit only. On GO, STEP-31 ingestion, STEP-32 roster and mapping code, STEP-33 pilot onboarding, STEP-35 rules and baselines, STEP-38 V-item branches, STEP-39 pass-line measurement, STEP-43 pilot-readiness gate (all `runs_if: "GO"`), and through them every step from 31 to 43.
Sources: Slide 29 (RK1: "Test every verify item on the friend's account before day one; start with the fallback wording; stop if the signal is too thin"), Slide 30 (V1–V8 and the rule "nothing on this list appears in a digest until its test passes"), Slide 26 (pass line, Square caveat), Slide 12 (fallback sentence), ADR-004; `docs/build/go-no-go-criteria.md` §1–3 as accepted in STEP-18; BUILD_PLAN design choices 10, 11, 12, 34; D8, D16.

## Outcome
- `docs/build/status/STEP-21.json` has `"decision": "GO"` or `"decision": "NO-GO"` and `"status": "done"`, set in one PR from `not_started`.
- `docs/build/evidence/STEP-21.md` is the exact output of `python tools/check_evidence.py decision`: the decision, one `v_item:` line per V1–V8 (and any sub-item such as `V2.opened_by`), the criteria hash as accepted in STEP-18, `role: founder` and the date.
- On GO, the data steps read the V-item results from `docs/build/findings/square-fields.md` (STEP-20) through their single config map; this step writes no code and no config.
- On NO-GO, only STEP-22 may start. CI refuses to start or finish any `runs_if` step against the other decision (design choice 34).

## Acceptance criteria
1. The decision is the founder's. The session prints the inputs and never recommends a decision.
2. The inputs are read only from the repo:
   - STEP-20's evidence: `v_item:` lines and the `count:` lines (`orders`, `cancelled_orders`, `comps`, `discounts`, `refunds`, `no_sale_opens`, `item_voids`, `logins_hashed`);
   - `docs/build/findings/square-fields.md`;
   - `docs/build/findings/counsel-t17a-answers.md` (STEP-02);
   - STEP-07's status (DPA and pass line signed, so whether the V1 substitute measure and the T11 rule are signed).
3. The session lays out each criteria item for the founder, citing the evidence line it rests on:
   - each hard stop in §1 (no cancelled-order counts per business day; V8; V1 without a signed substitute; V2 and V7 both failing), marked hit or not hit;
   - each §3 threshold, marked met or missed.
   PARTIAL counts as NOT_RETURNED throughout (design choice 10). A threshold the founder rewrote before accepting is read as written in the accepted file.
4. GO is consistent with the accepted file: no hard stop hit unless the accepted file's founder option covers it, and every §3 threshold met unless the accepted file says otherwise. If the founder's call contradicts the accepted file, the step stops (see below); it is never recorded.
5. `python tools/check_evidence.py decision` exits 0. It refuses if `decision` is unset, if STEP-20's evidence lacks any of V1–V8, or if `go-no-go-criteria.md` changed since STEP-18's `sha256: … label=criteria`.
6. The evidence's `decision:` line equals the status file's `decision`. The PR changes only `docs/build/status/STEP-21.json` and `docs/build/evidence/STEP-21.md`.
7. No name, value or staff identifier appears anywhere. Counts and codes only.

## Human confirmation
"Founder: having read the V-item results, counts and criteria checks printed above, is your decision GO or NO-GO under RK1 and the accepted criteria, and which criteria items decide it?" Print AWAITING HUMAN CONFIRMATION and wait.

## Out of scope
- Editing the criteria. Any change after acceptance makes `decision` refuse; a new rule needs a founder-approved gate-change PR that re-accepts the criteria (reopening STEP-18).
- Setting `V_ITEMS` or any config (the data steps read `square-fields.md`).
- The exit itself (STEP-22) and any data step.

## Gate
`python tools/check_evidence.py decision` (exact, from `docs/build/status/STEP-21.json`). It reads only repo files and no private evidence, so the session runs it after the founder's answer. No gate test files (`docs/build/gates/STEP-21.txt`).

`docs/build/evidence/STEP-21.md` starts with `# STEP-21 evidence` followed by the command's output unchanged: `command:`, `exit_code: 0`, `decision:`, the `v_item:` lines, `sha256: … label=criteria`, `role: founder`, `date:`.

## If the gate fails
- Revert to the last green commit. Set the status to `blocked` with a `blocked_reason` code, for example `criteria_changed_since_step_18`, `spike_evidence_incomplete` or `decision_contradicts_criteria`; no names or values. After two failed attempts, restart in a fresh session with a narrower prompt.
- Never edit the criteria, STEP-20's evidence or the findings to make the tool pass.

## Prompt (paste into a fresh Claude Code session, run from an engineer's account)
```text
You are running STEP-21 "Go/no-go decision recorded" for TillOwl. Follow @CLAUDE.md throughout.
Start: git fetch && git rebase origin/main; confirm STEP-20 is "done" in docs/build/status/STEP-20.json (stop and say so if not); read git log -5; run CLAUDE.md's setup command; read @docs/build/steps/STEP-21-go-no-go-decision.md, @docs/build/go-no-go-criteria.md, @docs/build/evidence/STEP-20.md, @docs/build/findings/square-fields.md, @docs/build/findings/counsel-t17a-answers.md, @docs/build/status/STEP-07.json, and Slides 12, 26, 29, 30 in @docs/architecture-pack-part1.md and @docs/architecture-pack-part2.md.
This is a human step: one PR straight from not_started to done. Never read $PRIVATE_EVIDENCE_DIR and never run tools/check_artifact.py.
1. Print a table of V1–V8 results and the count lines from STEP-20's evidence. Then print each hard stop in criteria §1 as hit / not hit and each §3 threshold as met / missed, with the evidence line each rests on. PARTIAL counts as NOT_RETURNED. Do not recommend a decision.
2. Print the human-confirmation line from the step file and AWAITING HUMAN CONFIRMATION; wait.
3. If the founder's decision contradicts the accepted criteria, stop: set status "blocked" with blocked_reason decision_contradicts_criteria and explain that a gate-change PR re-accepting the criteria comes first.
4. Otherwise set "decision" in docs/build/status/STEP-21.json to the founder's answer and status "done". Run python tools/check_evidence.py decision and show the command and its full output. Write docs/build/evidence/STEP-21.md from that output unchanged. Run python tools/check_evidence.py validate --step STEP-21 and show its output. Never claim success without the output.
5. Open the PR with gh. Its description names the decision and the steps it releases: STEP-22 only on NO-GO; STEP-31, 32, 33, 35, 38, 39, 43 on GO, which read V-item results from docs/build/findings/square-fields.md. It also says the founder must approve the PR and then re-run the founder-approval check.
Out of scope: editing the criteria, any config or code, the exit job, any data step.
Use a subagent to review the diff against this step file and report only gaps that affect correctness or the stated acceptance criteria.
```
