# STEP-24 Digest fact checker and deny-list (scenario 2)

Track: build. Lane: digest. Gate kind: ci_staging. Size: M.
Depends on: STEP-23 Fact templates and template manifest. Done requires: STEP-09 staging deploy (this ci_staging gate runs in the staging workflow).
Blocks: STEP-26 digest build and delivery, STEP-38 V-item branches in templates and checker.
Sources: Slide 12 ("Step 11 rejects any number that is not in the stored flag"), Slide 13 (flow step 11), Slide 24 (scenario 2: "The sentence is dropped and the plain template fact line is sent instead. Nothing calls anyone a thief." Measure: "100% of numbers in every digest trace to stored flag rows"), Slide 21 (fact-based wording; least data to vendors), Slide 3 (P4, L4, L5), ADR-006; BUILD_PLAN §7, design choices 14, 23, 24.

## Outcome
`tillowl/digest/checker.py`:
- `check_sentence(sentence, flag_row)` returns accept, or reject with reason codes (`number`, `time`, `name`, `deny_word`). It loads `deny_list.txt` only through `tillowl.digest.facts.load_templates()`, so the manifest hash is checked.
- `checked_lines(flag_rows, explanations)` returns, for each flag, the LLM sentence if accepted, else `fact_line(flag_row)` from STEP-23. A flag with no explanation gets its fact line.
- `untraced(text, flag_rows)` lists every number, time or name token in a finished digest text that no stored flag row holds. The digest build (STEP-26) refuses to send unless it is empty.

## Acceptance criteria
1. **Numbers.** Every number in a candidate sentence must equal a value in that flag row; otherwise the sentence is rejected. That covers:
   - integers and decimals, counts, money (`$412`, `$1,204.50`, `412 dollars`) and percentages;
   - spelled-out numbers ("nine", "twenty-one");
   - ordinals and numbers inside dates.
   Money compares in integer cents: a stored amount of 41200 cents matches "$412" and "$412.00" (and "412 dollars"), and "$412.50" doesn't match it. `9` doesn't match a stored 90. The same rules apply in `check_sentence` and `untraced`.
2. **Times.** Every time ("10:40", "10:40 pm", "22:40", "11 pm") must equal a time in the flag's evidence, in the restaurant's time zone (design choice 18). Every date or weekday must be the flag's business day.
3. **Names.** Login codes and approval codes must be the flag's own, and a shift name must be the flag's shift. Any other capitalised word, the sentence's first word included, is treated as a name and rejected unless it is in a short fixed allowlist of non-name words in `checker.py` (for example "The", "On", "During", "Between", "Square"). A display name is rejected even when the flag row carries one.
4. **Deny-list.** Any `deny_list.txt` word rejects the sentence. That includes STEP-23's accusation, wage-deduction and firing words, so no explanation can label anyone a thief (L5), suggest deducting a loss from wages (L4) or present a flag as the basis for a firing (Slide 21). Matching is case-insensitive, on whole words, inside hyphenated words and next to punctuation.
5. A rejected sentence is replaced by the flag's template fact line, exactly once and in the same position. Accepted sentences pass through unchanged.
6. Given `tests/gates/step_24/fixtures/week_with_3_flags.json` (three synthetic flag rows, for example cancelled orders on Dinner with login `L07` and count 9) and `tests/gates/step_24/fixtures/llm_sentences.json` (synthetic candidates, each labelled with the expected verdict: good, added number, added time, added name, deny-list word, spelled-out number, display-name leak):
   - `pytest -c pytest.ini --rootdir=. tests/gates/step_24` passes;
   - every labelled verdict holds;
   - in `test_scenario2_facts_only.py`, the flags are written to and read back from the staging schema's flag table, and `untraced` is empty for the assembled digest: 100% of numbers trace to stored flag rows (Slide 24 scenario 2).
7. Property tests in `test_fact_checker.py` generate many flag rows. For each, (a) inserting any number, time or capitalised word not in the row into an accepted sentence makes it rejected, and (b) every `fact_line` output is accepted by `check_sentence` against its own row.
8. `test_deny_list.py` checks every deny-list word in several casings and inflections, and checks that no template line is rejected.
9. Fixtures hold only synthetic codes and placeholder names; no real names, values or Square ids.
10. Every gate test pins `tillowl.config.V_ITEMS` explicitly with monkeypatch (BUILD_PLAN §7), so findings recorded after GO never change this frozen test.

## Out of scope
- Choosing lines by V-item result (STEP-38).
- Calling the model (STEP-25).
- Building, logging or sending the digest (STEP-26).
- Changing templates or the deny-list (STEP-23 files, under the manifest).

## Gate
`pytest -c pytest.ini --rootdir=. tests/gates/step_24` (exact, from `docs/build/status/STEP-24.json`). Gate files: `docs/build/gates/STEP-24.txt`.
- Locally, run `test_fact_checker.py` and `test_deny_list.py` by path; they need no database.
- `test_scenario2_facts_only.py` uses the `staging_schema` fixture and runs only in the `staging` workflow (job `gate STEP-24`) on main after merge.

`docs/build/evidence/STEP-24.md`: `command:`, `exit_code: 0`, `count: N passed`, `run_id:` (that staging run on main, green for job `gate STEP-24`, gate files unchanged since), `date:`.

## If the gate fails
Revert to the last green commit. Set `blocked` with a `blocked_reason` (no names or values). After two failed attempts, restart in a fresh session with a narrower prompt. Never loosen a rule or a fixture label to pass; a red staging run blocks only this step.

## Prompt (paste into a fresh Claude Code session)
```text
You are running STEP-24 "Digest fact checker and deny-list (scenario 2)" for TillOwl. Follow @CLAUDE.md throughout.
Start: git fetch && git rebase origin/main; confirm STEP-23 is "done" in docs/build/status/STEP-23.json (stop and say so if not); read git log -5; run CLAUDE.md's setup command; read @docs/build/steps/STEP-24-digest-fact-checker.md, @tillowl/digest/facts.py, the files in @tillowl/digest/templates/, @conftest.py (the staging_schema fixture), and Slides 3, 12, 13, 21, 24 in @docs/architecture-pack-part1.md and @docs/architecture-pack-part2.md.
Step PR, test first:
- Set docs/build/status/STEP-24.json status to "in_progress".
- Write the three tests and two fixtures exactly as listed in docs/build/gates/STEP-24.txt, to the acceptance criteria (property tests, not only fixed examples; money as integer cents; V_ITEMS pinned with monkeypatch). Run the two database-free tests by path; they fail (print RED TEST (intentional) if you stop here).
- Write tillowl/digest/checker.py. Run the two database-free tests by path and CLAUDE.md's test command; show each command and its output; never claim success without it. Commit; open the step PR with gh. It merges when CI is green.
Done PR: after merge, the staging workflow runs job "gate STEP-24" on main. Take that run's id and its count: N passed (gh run view <id> --log). Make one commit on top of main holding only docs/build/evidence/STEP-24.md and status "done". Run python tools/check_evidence.py validate --step STEP-24, show the output, and open the PR with gh.
Out of scope: V-item line choice, the model call, digest build and delivery, template edits.
Use a subagent to review the diff against this step file and report only gaps that affect correctness or the stated acceptance criteria.
```
