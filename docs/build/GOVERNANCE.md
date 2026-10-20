# Governance: how TillOwl keeps gates honest

This file says how each governance requirement G1–G8 (from `docs/build/PLANNING_PROMPT.md`) is met, which doc page each mechanism was checked against (Oct 20, 2026), how the founder installs it, the smoke test that proves it, and what it does **not** enforce. Everything to install lives under `docs/build/proposed/` at the path it installs to (`docs/build/proposed/tools/check_evidence.py` → `tools/check_evidence.py`).

**Least machinery.** GitHub settings do most of the work. One CI job, `governance`, enforces G1 and G3 with `tools/check_evidence.py`; a second job in the same workflow, `founder-approval`, enforces the part of G2 that GitHub can't. There are no hooks (G8 is optional and the founder did not ask for it).

**Trust boundary.** The `governance` workflow runs on `pull_request_target`, which "runs in the context of the default branch of the base repository" ([events that trigger workflows](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#pull_request_target)). It checks out the tools from the base branch and reads the PR's files only as data, so a PR can't weaken the checks that judge it. Never add a step to that workflow that runs code from the PR checkout; GitHub warns that "running untrusted code on the `pull_request_target` trigger may lead to security vulnerabilities."

## Required checks and settings at a glance

| Where | Setting | Value |
|---|---|---|
| GitHub plan | Private repo with protected branches, CODEOWNERS enforcement, environments and environment secrets | Pro or Team (D3). Free gives these on public repos only ([protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches), [code owners](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners), [environments](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments)) |
| Branch protection on `main` | Require a pull request before merging | on |
|  | Require approvals | 1 |
|  | Dismiss stale pull request approvals when new commits are pushed | on |
|  | Require review from Code Owners | on |
|  | Require approval of the most recent reviewable push | on |
|  | Require status checks to pass before merging | `governance`, `founder-approval`, `tests` |
|  | Do not allow bypassing the above settings | on |
|  | Allow force pushes / deletions | off |
| Environment `staging` | Deployment branches and tags | Selected: `main` only |
|  | Secrets | `STAGING_DATABASE_URL`, `RENDER_STAGING_DEPLOY_HOOK` |
|  | Variables | `STAGING_URL` |
| Collaborators | Write access | Rmasood1122 (admin), Ahmad317-Engineer and each engineer (write) |

Setting names are quoted from [Managing a branch protection rule](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/managing-a-branch-protection-rule). A required check can be selected only after it "must have completed successfully in the chosen repository during the past seven days" ([troubleshooting required status checks](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/collaborating-on-repositories-with-code-quality-features/troubleshooting-required-status-checks)), so protection is switched on after the install PR's checks go green. No workflow holding a required check has path filters, because a skipped required check stays Pending and blocks merging (same page).

## Install plan (up to three days, before STEP-01)

Do these in order. Record each smoke test's result in the install log at the end of this file.

**Day 1: GitHub**

1. Decide D3. For **Pro**: upgrade the Rmasood1122 account. For **Team**: create an organization, move `TillOwl` into it, and update every clone's remote.
2. Make the repo private (Settings → General → Danger Zone → Change visibility).
3. Add Ahmad317-Engineer and each engineer as collaborators with write access. Code owners "must have write permissions for the repository" ([code owners](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)).
4. From an engineer's account, open the install PR on branch `gate-change/install-governance`. It copies from `docs/build/proposed/`:
   `tools/check_evidence.py`, `tools/check_artifact.py`, `tools/build_progress.py`, `pytest.ini`, `conftest.py`, `.github/workflows/governance.yml`, `.github/workflows/ci.yml`, `.github/workflows/staging.yml`, `.github/CODEOWNERS`, `.claude/settings.json`, `CLAUDE.md`, `.gitignore`.
   On this one PR the `governance` job uses the PR's own copy of the tools, because the base branch has none yet (bootstrap; see G1 residual risk). Pin each `uses:` action to a full commit SHA before merging (look up the current SHAs on the actions' release pages); the proposed files use version tags.
5. Wait for `governance`, `founder-approval` and `tests` to go green on the install PR. The founder approves, then re-runs `founder-approval` (see "The founder's approval ritual"). Merge.
6. Turn on the branch protection settings in the table above and select the three required checks.
7. Create the `staging` environment: deployment branches = `main` only; add its secrets and variable once STEP-09 creates the Render staging service (until then the staging workflow prints "not configured yet" and passes).
8. Run the Day 1 smoke tests: G1-a, G1-b, G2-a, G2-b, G2-c, G3-a, G6-a.

**Day 2: Claude Code on every developer machine** (repeat per operating system, D2)

1. Install Claude Code v2.1.285 or later. Before that version, "a project's `true` overrode a `false` in your user settings" ([sandboxing](https://code.claude.com/docs/en/sandboxing)).
2. On Linux and WSL2, install the sandbox dependencies that `/sandbox` lists on its Dependencies tab (the docs name bubblewrap as one). Native Windows is not supported; use WSL2.
3. Merge `docs/build/proposed/user-settings/settings.json` into `~/.claude/settings.json`. Replace `/ABSOLUTE/PATH/TO/TillOwl-private-evidence` with the real absolute path on the founder's machine (D4); on other machines remove those two entries.
4. Install PostgreSQL 16 server binaries for the test fixture (macOS: `brew install postgresql@16`; Ubuntu/WSL2: `sudo apt install postgresql`). The fixture never uses the system service.
5. Make sure `git` uses HTTPS for GitHub (`git remote -v`). The docs note that on macOS "git over SSH" fails inside the sandbox even when the host is allowed.
6. Run the Day 2 smoke tests: G4-a, G4-b, G5-a, G6-b, G7-a to G7-e.

**Day 3: Render, evidence folder, close-out**

1. Render workspace notifications: set the level to "Only failure notifications" so a failed cron run emails the founder ([Render notifications](https://render.com/docs/notifications)). Failed one-off jobs notify by Slack only, so the founder watches each one-off job's status directly.
2. Create `PRIVATE_EVIDENCE_DIR` on the founder's machine, outside every git checkout, on an encrypted disk, readable only by the founder (`chmod 700`).
3. Run smoke test G5-b.
4. Fill in the install log and commit it on branch `gate-change/governance-install-log` (this file is not protected, but keeping the log on the gate-change path keeps one history).

## G1 Gate integrity

**Mechanism.**
- `governance` runs `check_evidence.py ci` on every PR. It rejects:
  - changes to `tools/`, `.github/`, `.claude/`, `docs/build/gates/`, `conftest.py`, `pytest.ini`, `CLAUDE.md`, `CODEOWNERS`, `docs/build/PLANNING_PROMPT.md` and `docs/build/go-no-go-criteria.md` unless the branch starts with `gate-change/`;
  - a change to any `tests/gates/step_NN/` file once STEP-NN is done on the base branch;
  - any file in `tests/gates/step_NN/` not named in `docs/build/gates/STEP-NN.txt`;
  - edits to `migrations/*_rls*.sql` and `migrations/*_audit_role*.sql` after they first land;
  - edits to `tillowl/digest/templates/MANIFEST.json` after T17b;
  - gate-listed job modules of done steps;
  - findings of done steps;
  - any pytest configuration outside the root `pytest.ini` (a nested `pytest.ini`, a `tox.ini` or `setup.cfg` pytest section, or a `[tool.pytest*]` table in any `pyproject.toml`);
  - any `conftest.py` outside the root and `tests/gates/`.
- CODEOWNERS covers all of `tests/gates/`, so a step's own gate files change with one code owner's review until its done PR merges.
- `founder-approval` requires the founder's approval on every `gate-change/*` PR.

**Doc URLs.**
- [About protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- [About code owners](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)
- [Events that trigger workflows: pull_request_target](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#pull_request_target)

**Install.** Day 1, steps 4–6.

**Smoke tests.**
- **G1-a.** On a branch `test/g1`, append a comment to `tools/build_progress.py` and open a PR. Expect `governance` red, with "protected path changed; use a gate-change/ branch". Close the PR.
- **G1-b.** Push the same change on `gate-change/g1-smoke`. Expect `governance` green and `founder-approval` red until the founder approves. Close the PR without merging.

**Residual risk.**
- **Gate-change PRs can change anything, including the checks themselves.** The only protection is the founder's review.
- **The install PR is judged by its own tools.** This bootstrap gap closes once the tools are on `main`.
- **The `ci` workflow runs on `pull_request`, so a PR's own `ci.yml` runs.** A non-gate-change PR that edits `.github/` is rejected by `governance`, so this matters only for gate-change PRs.
- **No hook checks local edits.** The ask rules in `.claude/settings.json` don't see writes made through Bash ([permissions](https://code.claude.com/docs/en/permissions)), so CI is the first enforcement.
- **One `pull_request_target` behaviour is unverified.** Its check runs are expected to attach to the PR head and to be selectable as required checks, but the docs fetched don't state it; smoke tests G1-a/G1-b and install step 6 confirm it. If they don't, switch both jobs to `pull_request` (fallback). The residual risk then becomes that a gate-change PR could edit `governance.yml`, and CODEOWNERS review is the only guard.

## G2 Approvals

**Mechanism.**
- **Branch protection** gives:
  - 1 approval;
  - code-owner review;
  - stale approvals dismissed;
  - approval of the most recent reviewable push, which "requires approval from someone other than the last person to push";
  - no bypass.
- **CODEOWNERS** lists @Rmasood1122 and @Ahmad317-Engineer for:
  - the G1 paths;
  - `docs/build/evidence/` and `docs/build/findings/`;
  - the status files of steps 01–07, 12–18, 20–22, 33, 34, 40, 41 and 43, which are the human, production_job and sandbox_spike steps.
- **The `founder-approval` job** (`check_evidence.py approval`) closes the gap GitHub leaves. When a PR is on a `gate-change/*` branch, or touches evidence, findings, a protected path, or a founder-gated step's status file:
  - the founder's latest review must be APPROVED on the PR's head commit;
  - if the founder opened the PR, Ahmad317-Engineer's approval plus a line `Founder sign-off: YYYY-MM-DD` in the description is required instead.
- **Pull request authors cannot approve their own pull requests.** This is GitHub's rule ([approving a PR with required reviews](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/reviewing-changes-in-pull-requests/approving-a-pull-request-with-required-reviews)).

**The founder's approval ritual.** Founder-gated PRs are opened from an engineer's account and Claude session, and the founder pastes their terminal or job output into that session. After reviewing:
1. Approve the PR.
2. Open the PR's Checks tab → `founder-approval` → Re-run job. The job reads reviews live; a re-run keeps "the same `GITHUB_SHA`" ([re-running workflows](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/re-run-workflows-and-jobs)) and is allowed for 30 days.
3. Merge when all checks are green.

**Doc URLs.**
- [Managing a branch protection rule](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/managing-a-branch-protection-rule)
- [About code owners](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)
- [Approving a pull request with required reviews](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/reviewing-changes-in-pull-requests/approving-a-pull-request-with-required-reviews)
- [Re-running workflows and jobs](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/re-run-workflows-and-jobs)

**Install.** Day 1, steps 3, 6.

**Smoke tests.**
- **G2-a.** An engineer opens a PR changing only `README.md`. Expect one approval from any other collaborator to be enough, and `founder-approval` to print "founder approval not required".
- **G2-b.** An engineer opens a PR that edits `docs/build/findings/smoke.md`. Expect merge blocked until a code owner approves and `founder-approval` is green. Ahmad's approval alone leaves `founder-approval` red.
- **G2-c.** After an approval, the author pushes one more commit. Expect the approval dismissed.

**Residual risk.**
- **Admins can switch protection off.** The founder is the repo admin, so break-glass is a team rule, logged below.
- **The ritual needs a manual re-run** of `founder-approval` after each approval.
- **The sign-off line on a founder-opened PR is trusted text.**
- **Who opens founder-gated PRs** (an engineer's account, with the founder's output pasted in) is a team rule GitHub can't see.
- **Code-owner review bottleneck.** With five engineers and two code owners, every `tests/gates/` change waits on Rmasood1122 or Ahmad317-Engineer.

**Break-glass log.** Each time "Do not allow bypassing the above settings" is switched off, add a row in the same PR that switches it back on.

| Date | Who | What changed | Why | Re-enabled |
|---|---|---|---|---|
|  |  |  |  |  |

## G3 Done means evidence

**Mechanism.** The `governance` job runs `check_evidence.py ci`. On a PR that marks STEP-NN done:
- `docs/build/evidence/STEP-NN.md` must pass the allowlist grammar in `docs/build/evidence/README.md`;
- its commands must equal the status file's `gate`, in order;
- every exit code is 0;
- all `depends_on` and `done_requires` steps are done;
- the PR changes only that step's status and evidence files.

CI then checks evidence by gate kind:
- **ci_fixture:** CI verifies the cited `run_id` with `gh run view` using `GITHUB_TOKEN` (`actions: read`). The run must be a green `ci` run on the evidence commit's parent, with the step `in_progress` there, and the evidence commit must change only that step's evidence and status.
- **ci_staging:** the run must be a `staging` run on `main` whose job `gate STEP-NN` is green, on this branch's history, with the step's gate files unchanged since.
- **sandbox_spike** and steps with `findings_path`: CI recomputes the findings file's SHA-256.
- **production_job** and **human:** evidence only (format, role, job ids, hashes).

The `tests` job runs `pytest -c pytest.ini --rootdir=.` with `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` over the full suite. It covers the gate files of every ci_fixture step that is `in_progress` or `done`, and leaves out ci_staging gates, which run in the staging workflow. `check_evidence.py junit` then reads the JUnit report (`junit_family = xunit1`, so each test case names its file) and fails on:
- any skip;
- any xfail (and `xfail_strict` fails any xpass);
- any failure;
- any gate file with zero passing tests.

**Doc URLs.**
- [gh run view](https://cli.github.com/manual/gh_run_view): fields `headSha`, `conclusion`, `workflowName`, `headBranch`, `event`, `jobs`
- [Workflow runs REST API](https://docs.github.com/en/rest/actions/workflow-runs): "Actions" read permission
- [Workflow syntax: permissions](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax)
- [About status checks](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/collaborating-on-repositories-with-code-quality-features/about-status-checks): "A job that is skipped will report its status as 'Success'", which is why no required job is conditional on PRs

**Network to the staging database (T9, D18).** GitHub-hosted runner IP ranges are "updated once a week" and GitHub does "not recommend that you use these as allowlists" ([GitHub-hosted runners](https://docs.github.com/en/actions/reference/runners/github-hosted-runners)). Render Postgres accepts TLS connections on its external URL, with a per-database IP allowlist whose default is `0.0.0.0/0` ([Render connecting](https://render.com/docs/postgresql-creating-connecting)).
- Proposed: keep `0.0.0.0/0` on **staging only**. Staging holds synthetic data, needs TLS and a strong generated password, and the URL lives only in the `staging` environment.
- Production keeps external access closed.
- The alternative is larger runners with static IPs, at a cost that is TBD — not in sources.

**Install.** Day 1, steps 4–7.

**Smoke tests.**
- **G3-a.** On a throwaway branch, add a status file through a `gate-change/g3-smoke` PR, then in a second PR mark it done with an evidence line `note: it works`. Expect `governance` red with "not in the evidence grammar". Close both PRs.
- **G3-b** (after STEP-08 exists). A gate file containing `@pytest.mark.skip` makes `tests` red.

**Residual risk.**
- **Production-job and human evidence is only as true as the pasted output.** CI can't call Render (it holds no Render key), so `job_id` lines are checked for format only.
- **A person's name could be mistyped as an identifier-shaped `field:` value.** The grammar can't tell a name from a field name.
- **CI checks the order of cause and effect, not authorship.** An engineer who forges a run id still has to match a real green run on the right commit.

## G4 Secrets

**Mechanism.**
- **Production credentials live only in Render's secret store** for the production services, and only the founder holds the Render account. Claude sessions and CI never see production credentials, and production deploys are manual.
- **Staging secrets live in the GitHub `staging` environment**, limited to `main`. Environment secrets are "only available to workflow jobs that reference the environment" ([deployments and environments](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments)).
- **Local sessions get only the Square sandbox token** (STEP-01) and vendor test credentials, exported in the developer's own shell for that session. They never go in `.env` files or committed settings, and never include the staging database URL.
- **The sandbox can read most of the disk by default**, including "credential files such as `~/.ssh` and `~/.aws/credentials`" ([sandboxing](https://code.claude.com/docs/en/sandboxing)). Each developer's `~/.claude/settings.json` therefore:
  - adds `sandbox.filesystem.denyRead` and matching `Read(...)` deny rules for cloud, database, Render CLI, SSH and netrc credentials, and for `PRIVATE_EVIDENCE_DIR`. gh's own credentials are left readable, because opening PRs needs them.
  - sets `sandbox.network.strictAllowlist: true`, so sandboxed commands can reach only the project's allowed domains (GitHub, PyPI, Square sandbox) instead of prompting. That setting has no effect in a repository's settings files.

**Doc URLs.**
- [Sandboxing](https://code.claude.com/docs/en/sandboxing): `filesystem.denyRead`; "A denyRead entry doesn't stop the Read tool", which is why Read rules are added too; `strictAllowlist`
- [Permissions](https://code.claude.com/docs/en/permissions): `//path` is absolute, `~/path` is home
- [Deployments and environments](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments)
- [Render environment variables and secret files](https://render.com/docs/configure-environment-variables)

**Install.** Day 1, step 7; Day 2, step 3.

**Smoke tests.**
- **G4-a.** In a Claude session, ask Claude to run `cat ~/.aws/credentials` (or any listed credential file that exists). Expect a sandbox read denial.
- **G4-b.** Ask Claude to run `curl -sS https://api.render.com`. Expect the proxy to refuse the host without offering a prompt.

**Residual risk.**
- **Two Render CLI config paths in the deny list are unverified candidates.** `~/.render` and `~/.config/render` are not confirmed by Render's docs, so check where your Render CLI stores its key and add that path.
- **Some things run outside the sandbox.** MCP servers and hooks do. Don't connect a Render, database or cloud MCP server in step sessions.
- **The engineer's own `gh` token is readable inside sessions.** It can do whatever that engineer can on GitHub (see G6).
- **Staging database exposure** is D18.

## G5 Private evidence and staff data

**Mechanism.**
- **Signed documents stay in `PRIVATE_EVIDENCE_DIR`**, an absolute path outside every git checkout (D4). It holds copies named `STEP-NN/<label>.<ext>`; the owner keeps the signed originals.
- **Only the founder runs `tools/check_artifact.py`**, in their own terminal. It refuses a folder inside a git checkout, links, empty files and future dates. It prints only the command, exit code, SHA-256, signer role, counts (staff acknowledgments as signed/absent/refused counts only) and date, never a path, file name or content.
- **Claude sessions can't read the folder by any route.** The user settings deny it to both the Read tool and sandboxed commands. The project settings deny `python tools/check_artifact.py *`, and `CLAUDE.md` forbids running it.
- **Human-step prompts print the full command** with the absolute path written out, for example `PRIVATE_EVIDENCE_DIR=/Users/rehan/TillOwl-private-evidence python tools/check_artifact.py --step STEP-05 --label notice --role owner --date 2026-11-02`, then print AWAITING HUMAN CONFIRMATION.

**Doc URLs.**
- [Sandboxing](https://code.claude.com/docs/en/sandboxing) (`filesystem.denyRead`)
- [Permissions](https://code.claude.com/docs/en/permissions) (Read rules)

**Install.** Day 2, step 3; Day 3, steps 2–3.

**Smoke tests.**
- **G5-a.** In a Claude session on the founder's machine, ask Claude to list the evidence folder with `ls` and with the Read tool. Expect both denied.
- **G5-b.** In the founder's terminal, put a test file at `$PRIVATE_EVIDENCE_DIR/STEP-99/notice.txt` and run `python tools/check_artifact.py --step STEP-99 --label notice --role owner`. Expect only allowlisted lines and exit 0. Then delete the test folder.

**Residual risk.**
- **Bash deny patterns are fragile.** The deny on the command text doesn't match `sh -c` or other paths ([permissions](https://code.claude.com/docs/en/permissions)). The sandbox's `denyRead` is what actually protects the folder.
- **The folder is protected only on machines whose user settings name it.** Keep it on the founder's machine only.

## G6 Claude can't approve, merge or push to main

**Mechanism.**
- **`.claude/settings.json` deny rules block:**
  - `gh pr review *`, `gh pr merge *`, `gh api *`, `gh run rerun *`, `gh workflow run *`, `gh secret *`, `gh variable *`, `gh repo edit *`;
  - `git push origin main` and `git push origin HEAD:main` in all forms;
  - `git push --force`, `-f` and `--no-verify`;
  - `git commit --no-verify` and `-n`;
  - `render *` and `psql *`.
- **Branch protection is the real stop:** no direct pushes to `main` for anyone, and merges need approvals and green checks.

**Doc URLs.**
- [Permissions](https://code.claude.com/docs/en/permissions): space form `Bash(gh pr merge *)`. "Bash permission patterns that try to constrain command arguments are fragile", and a pattern "doesn't match the same program by path or inside `sh -c`".
- [Managing a branch protection rule](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/managing-a-branch-protection-rule)

**Install.** Day 1, step 6; the project settings arrive with the install PR.

**Smoke tests.**
- **G6-a.** From a terminal, `git push origin HEAD:main` on a scratch commit. Expect GitHub to reject it.
- **G6-b.** In a Claude session, ask Claude to run `gh pr merge 1`. Expect a permission denial.

**Residual risk.**
- **Deny rules don't bound what a program does.** A script Claude writes could call the GitHub API with the engineer's `gh` token, and approve another engineer's PR. GitHub would accept that as the engineer.
- **The main defences** are branch protection, the founder-approval check, and code review of every PR.

## G7 Sandbox

**Mechanism.**
- **Both `.claude/settings.json` (project) and each developer's `~/.claude/settings.json` (user) set:**
  - `sandbox.enabled: true`;
  - `sandbox.allowUnsandboxedCommands: false`, which closes the escape hatch: "Claude Code ignores the `dangerouslyDisableSandbox` parameter";
  - `sandbox.failIfUnavailable: true`, so Claude Code exits at startup instead of running unsandboxed.
- **The user setting holds even if a project says otherwise.** A `false` "in your user settings ... holds even when a project's settings set `true`" (v2.1.285+).
- **We don't use managed settings or `--settings`.** Either makes the sandbox admin-required, and "Claude Code then ignores the settings in a repository's files that loosen the sandbox, `excludedCommands` entries included".
- **The project allows only a few network domains:** GitHub, PyPI and the Square sandbox host `connect.squareupsandbox.com`, which Square's docs name ([Square Sandbox](https://developer.squareup.com/docs/devtools/sandbox/overview)). It also sets `network.allowLocalBinding: true`, which applies on macOS only.
- **The test database works inside the sandbox.** The proposed `conftest.py` starts PostgreSQL on 127.0.0.1 inside the pytest process tree with no Unix socket. On Linux and WSL2 "a sandboxed command's localhost is private to that command", which is enough because the server and the tests share the tree. On macOS, binding a local port needs `allowLocalBinding`. Database drivers "can't connect, even to an allowed host" through the proxy, so local sessions never reach a remote database (consistent with G4). Docker and testcontainers are not used.

**Doc URLs.**
- [Sandboxing](https://code.claude.com/docs/en/sandboxing): strict sandbox mode, `failIfUnavailable`, admin-required sandbox, `allowLocalBinding`, the macOS TLS note
- [Settings precedence](https://code.claude.com/docs/en/settings)

**Does `.claude/settings.local.json` reopen the escape hatch?** The docs don't say so explicitly. They say a user-level `false` holds "even when a project's settings set `true`", and that `/sandbox` saves to `settings.local.json`. Smoke test G7-e checks it on each machine. Until it passes, treat it as residual risk.

**Smoke tests** (on each operating system, D2):
- **G7-a.** `/sandbox` → Overrides tab shows **Strict sandbox mode** on.
- **G7-b.** Ask Claude to run `touch ~/sandbox-probe`. Expect a write denial with no offer to retry unsandboxed.
- **G7-c.** In a sandboxed session, run CLAUDE.md's setup command and `.venv/bin/pip install -q 'psycopg[binary]==3.*'`, then the fixture test `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -c pytest.ini --rootdir=. docs/build/proposed/smoke/test_pg_fixture.py`. Expect 1 passed. If it fails on macOS with a bind error, confirm `allowLocalBinding` is set.
- **G7-d.** In a session, `git push` a scratch branch and `gh pr create --draft` on it. Expect both to work. On macOS, if `gh` fails TLS verification ("may fail TLS verification under Seatbelt"), the documented fix is excluding `gh *` via `excludedCommands`, which then "runs with your full access and its stored credentials". That is D17: exclude `gh` (residual risk), or open PRs from the founder's own terminal.
- **G7-e.** Put `{"sandbox": {"allowUnsandboxedCommands": true}}` in `.claude/settings.local.json`, restart, and repeat G7-a and G7-b. Expect strict mode still on. Remove the file afterwards. If strict mode turns off, record it as residual risk and add `.claude/settings.local.json` to each engineer's review checklist.

**Residual risk.**
- **Commands typed at the `!` shell prompt run outside the sandbox.**
- **Hooks and MCP servers run outside it.**
- **Older Claude Code versions** let a project's `true` win over the user's `false`.
- **Whether `settings.local.json` can reopen the escape hatch** is unconfirmed (G7-e).

## G8 Hooks

**Skipped.** G8 is optional, and the founder did not ask for hooks. CI is the only check of evidence format, so a session can stop with a malformed evidence file, and CI catches it on the PR.

If the founder asks later, the plan allows at most two hooks:
- They are G1-protected and fail closed.
- They never run app or test code.
- Each one is mirrored in CI, because a hook on the edit tools doesn't see Bash writes.

A Stop hook would only run `check_evidence.py validate --step` on the step's evidence. It would always allow the stop when:
- `stop_hook_active` is true;
- the last message contains AWAITING HUMAN CONFIRMATION or RED TEST (intentional);
- the step is blocked;
- the gate kind isn't ci_fixture.

`"onFailure": "block"` needs v2.1.295 and "has no effect" on Stop hooks ([hooks](https://code.claude.com/docs/en/hooks)). The docs fetched did not confirm the `stop_hook_active` field.

## Install log

| Smoke test | Machine / OS | Date | Result | Notes |
|---|---|---|---|---|
| G1-a |  |  |  |  |
| G1-b |  |  |  |  |
| G2-a |  |  |  |  |
| G2-b |  |  |  |  |
| G2-c |  |  |  |  |
| G3-a |  |  |  |  |
| G4-a |  |  |  |  |
| G4-b |  |  |  |  |
| G5-a |  |  |  |  |
| G5-b |  |  |  |  |
| G6-a |  |  |  |  |
| G6-b |  |  |  |  |
| G7-a to G7-e |  |  |  |  |
