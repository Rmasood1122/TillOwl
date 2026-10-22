# STEP-23 Fact templates and template manifest

Track: build. Lane: digest. Gate kind: ci_fixture. Size: S.
Depends on: STEP-08 Repo skeleton. Done requires: none.
Blocks: STEP-24 digest fact checker and deny-list, STEP-25 explanation service (it sends the explanation prompt this step creates).
Sources: Slide 3 (P4 "State facts, never labels"; L4 no wage deduction; L5 facts only, owner only), Slide 12 (target sentence and the day-one fallback "9 checks cancelled during shift Y (opened by login X)"), Slide 21 (fact-based wording: "counts, times, logins, codes. Never 'thief', never a wage deduction, never the only basis for a firing"; owner only), Slide 24 (scenario 2; scenario 4's reconnect text), Slide 30 (T17), ADR-004, ADR-006; BUILD_PLAN §7 (templates), design choices 8, 12, 14, 23, 32; `docs/build/go-no-go-criteria.md` §2.

## Outcome
`tillowl/digest/templates/` holds:
- `fact_lines.json`: fixed fact-line templates keyed by name, each with only these placeholders: `{count}`, `{shift}`, `{login}`, `{code}`, `{start}`, `{end}`, `{console_url}`:
  - cancelled orders with the login clause: `{count} checks cancelled during shift {shift} (opened by login {login})`;
  - cancelled orders without it: `{count} checks cancelled during shift {shift}`;
  - with and without a login clause: comps, discounts, refunds, no-sale drawer opens, item voids on paid checks;
  - the approval-code clause `approved by code {code}`, the time clause `between {start} and {end}`, and the scenario 4 reconnect text asking the owner to sign in and reconnect Square;
  - a footer saying the lines are POS facts for the owner's review, not findings about any person.
- `explain_prompt.txt`: the explanation prompt STEP-25 sends. It asks for one plain sentence per flag that restates only the given numbers, times, shift names and codes. It forbids judging, guessing motives, suggesting discipline, a wage deduction or a firing, and any deny-list word.
- `deny_list.txt`: one lower-case word per line. At least design choice 23's words ("theft", "stole", "steal", "suspicious", "likely", "fraud", "thief", "dishonest", "caught"), their inflections, and wage-deduction and firing words (L4; Slide 21). Counsel reviews it under T17b.
- `MANIFEST.json`: `{"files": {"<path relative to templates/>": "<sha256>"}}`, covering every other file in the folder.

`tillowl/digest/facts.py` (design choice: the one loader every caller uses):
- `load_templates()` refuses to load if any file's hash differs from the manifest;
- `fact_line(flag)` renders one line from a flag row.

## Acceptance criteria
1. Given `tests/gates/step_23/test_fact_templates.py`, `pytest -c pytest.ini --rootdir=. tests/gates/step_23` passes, for **every** combination of:
   - metric (`cancelled_orders`, `comps`, `discounts`, `refunds`, `no_sale_opens`, `item_voids`);
   - login code present or absent;
   - approval code present or absent;
   - time range present or absent;
   - counts 0, 1, 9 and 1000.
   For each, `fact_line` returns exactly one line, and every number, time and code in it comes from that flag.
2. The canonical lines render exactly: "9 checks cancelled during shift Dinner (opened by login L07)" for a flag with login `L07`, and "9 checks cancelled during shift Dinner" for the same flag without a login (design choice 12).
3. `fact_line` uses the login clause only when the flag row carries a login code. It raises on a `login` value that isn't a login code (`^L\d+$`, design choice), so a display name can't be rendered. Whether a flag may carry a login (V2, V7, acknowledgment) is decided upstream (STEP-36, 37, 38), not here.
4. No template, rendered line or prompt file contains a deny-list word, an accusation, wage or deduction wording, or firing or discipline wording (case-insensitive, whole words). Every template addresses the owner only; no template is addressed to staff.
5. Given `tests/gates/step_23/test_template_manifest.py`:
   - every file in `tillowl/digest/templates/` other than `MANIFEST.json` is listed with its correct SHA-256;
   - a file added or changed without a manifest update fails (tested on a temporary copy);
   - `python tools/check_evidence.py manifest` exits 0.
6. Any `{…}` placeholder outside the allowed set fails the test.

## Out of scope
- The checker (STEP-24).
- The V1 dollar clause and wiring V-item results into line choice (STEP-38).
- Calling the model (STEP-25); building or sending a digest (STEP-26); counsel's sign-off (STEP-40).

## Gate
`pytest -c pytest.ini --rootdir=. tests/gates/step_23` (exact, from `docs/build/status/STEP-23.json`). Gate files: `docs/build/gates/STEP-23.txt`. The manifest is G1-protected but editable with code-owner review until STEP-40 is done (design choice 32).

`docs/build/evidence/STEP-23.md`: `command:`, `exit_code: 0`, `count: N passed`, `run_id:`, `date:`.
- `run_id` is the green `ci` push run on main for the evidence commit's parent.
- `count` comes from that run (`gh run view <id> --log` or the JUnit summary).

## If the gate fails
Revert to the last green commit. Set `blocked` with a `blocked_reason` (no names or values). After two failed attempts, restart in a fresh session with a narrower prompt. Never change a template to dodge a wording test; fix the wording.

## Prompt (paste into a fresh Claude Code session)
```text
You are running STEP-23 "Fact templates and template manifest" for TillOwl. Follow @CLAUDE.md throughout.
Start: git fetch && git rebase origin/main; confirm STEP-08 is "done" in docs/build/status/STEP-08.json (stop and say so if not); read git log -5; run CLAUDE.md's setup command; read @docs/build/steps/STEP-23-fact-templates.md, @docs/build/go-no-go-criteria.md, and Slides 3, 12, 21, 24, 30 in @docs/architecture-pack-part1.md and @docs/architecture-pack-part2.md.
Step PR, test first:
- Set docs/build/status/STEP-23.json status to "in_progress".
- Write tests/gates/step_23/test_fact_templates.py and tests/gates/step_23/test_template_manifest.py exactly as listed in docs/build/gates/STEP-23.txt, to the acceptance criteria (all combinations, not a few examples). Run them; they fail (print RED TEST (intentional) if you stop here).
- Write the four files in tillowl/digest/templates/ and tillowl/digest/facts.py. Use synthetic codes only (L07, Dinner); no real names.
- Run the gate command and CLAUDE.md's test command; show each command and its output; never claim success without it. Commit; open the step PR with gh. It merges when CI is green.
Done PR: one commit on top of main holding only docs/build/evidence/STEP-23.md and status "done". run_id is the green ci push run on main for that commit's parent, and count: N passed comes from that run (gh run view <id> --log). Run python tools/check_evidence.py validate --step STEP-23, show the output, and open the PR with gh.
Out of scope: the checker, V-item wiring and the V1 dollar clause, the model call, delivery, counsel review.
Use a subagent to review the diff against this step file and report only gaps that affect correctness or the stated acceptance criteria.
```
