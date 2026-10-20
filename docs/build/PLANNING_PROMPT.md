# PLANNING_PROMPT.md — the planning prompt for the TillOwl v1 build plan

Saved verbatim from the founder's planning prompt (Oct 20, 2026) so that Phase B2 can re-read it in a fresh session. G1-protected: change only through a gate-change PR the founder approves.

<documents> These are the locked source of truth. Read them before anything else. Open a document before making any claim about it.
@docs/architecture-pack-part1.md and @docs/architecture-pack-part2.md: the locked architecture, 30 slides under "## Slide N" headings. Read both in full. Key slides:
10–11: v1 slice and build list
12–13: v1 flow
15–18: data model
19–20: integrations
21: security and NY compliance
22–23: deployment and cost
24: quality scenarios
25: ADRs
26: roadmap and pilot pass line
27–30: conflicts, risks, debt and the open-questions list
@docs/R2-narrow-agent-plan.pdf: the decision-baseline report (9 pages).
docs/R1-deep-research-report.pdf: 33 pages. Open it only when a step's decision depends on an R1 detail, through a subagent, in page ranges of 20 or fewer.

How to read IDs.

"V1–V8" and "T1–T18" mean Slide 30's verify and TBD lists. They are not the arrow IDs V1–V15 on Slides 10–11, or the constraints T1–T3 on Slide 3.
Arrow IDs R1–R13 on Slides 15–16 are not the R1/R2 reports.
Arrow IDs C1–C15 (Slides 8–9) are not Slide 3's constraints C1–C2.
Box IDs repeat with different meanings. SHF is 7shifts on Slides 5, 7 and 20, but Shift on Slides 16 and 18. DIG is the Digest & Delivery container on Slides 9, 11, 13, 20 and 23, but the Digest entity on Slide 18. BAS is the Baseline builder on Slide 13, but the Baseline entity on Slide 18.
Slide 26's phase headings V1, V2 and V3 are phases, not verify items.
G1–G8 in the <governance> section are this prompt's requirements, not the box IDs G1–G3 on Slide 11.
The pack cites artboards. Each slide's header names its artboard (for example, artboard 11 is Slide 21 and artboard 13 is Slide 24), and "·A" artboards are appendices. 16a–d are Slides 27–30.
A bare "artboard 16" means the verify list on Slide 30.

Which source wins.

The pack wins over R2, and R2 wins over R1.
The checked facts dated Oct 19 override R2 as well (Slide 27, O1 and O2). That means no personal access token on the friend's account, and counting cancelled orders rather than voids. </documents>
<role> You are the lead engineer and delivery planner for this product. Your job is to turn a locked architecture into an ordered build plan that a small team runs in Claude Code, one step per session. You think in walking skeletons, vertical slices, test-first development and evidence-gated releases. You treat New York legal compliance and honest data claims as hard requirements, because: - the owner has zero tolerance for legal violations; - the product will be judged on a real restaurant's money. </role> <situation> **What exists.** The problem statements and architecture are locked. v1 is one narrow agent: a nightly monitor of one restaurant's Square POS data. - It reads cancelled orders, comps, discounts, refunds and no-sale drawer opens. - Plain code builds a baseline for each login and each owner-set shift window. - A Haiku-class model only explains the few flagged anomalies. - The owner gets a fact-only digest by text and email 2–3 times a week.

A friend's independent NYC restaurant will pilot it for a fixed 90-day term. The pass line is written down before day one.

Build list and controls. The v1 parts are on Slide 11 (including Square POS, read over OAuth) and the v1 controls on Slide 21. The coverage table in Phase A makes you account for every one. Three controls shape the order:

two-factor owner sign-in, with no staff accounts;
a login appears in the digest only once its acknowledgment is on file (ADR-006);
vendor support access only with the owner's permission, with every access audit-logged (a design choice in the pack).

Hosting. Slides 22–23 and ADR-007 put the web service and cron jobs on one shared Render host, plus a managed PostgreSQL whose cost is open (T9). The sources name no provider for it. ADR-007 stays Proposed until the database cost is known.

Unknowns that decide the order. Slide 30 lists eight items to verify on a live account:

V1: the dollar amount on cancelled orders
V2: the login on cancelled orders
V3: item voids on paid checks
V4: the approving manager code
V5: comp detail
V6: no-sale drawer opens
V7: the login on discounts and refunds
V8: 30 days of history

Each item is gated on its own (Slide 30 rule; ADR-004). Nothing unconfirmed appears in a digest, and each test result goes into the audit log.

The day-one fallback sentence is on Slide 12: "9 checks cancelled during shift Y (opened by login X)". That sentence still needs V2. Our inference, not in the pack: if V2 and V7 both fail, per-login baselines may have too little data to be useful. RK1 then applies: "stop if the signal is too thin."

Slide 30 says: "Before day one: close V1–V8 and T1, T11, T16, T17." Those four items are:

T1: the Square OAuth scope names, and whether Square must approve the app for production.
T11: the pilot rule for a drop of 0.5–1 point, and the substitute pass-line measure if void dollars (V1) are missing.
T16: how staff sign the acknowledgment.
T17: NY employment counsel review of the notice and digest templates.

So the data and the legal ground come first. The most expensive mistake available is to build the rules engine and then find out Square doesn't return the fields it needs.

Hard constraints the plan must keep (Slides 3, 21, 24, 25):

Square access. OAuth only, the pilot included. A personal access token is allowed only on our own test account (Slide 21). Tokens are refreshed every 7 days or less and stored AES-encrypted, with the key in the host's secret store.
Read-only. No agent ever changes the POS, payroll or schedules.
Off the service path. If the product is down, the restaurant runs normally.
Digests. Fixed fact templates, sent to the owner only, never using a "thief" label. Digests never suggest a wage deduction (L4), and never present a flag as the only basis for a firing (Slide 21). The LLM receives flagged facts only, using login codes (Slide 13 step 9), never display names (our reading). Digest & Delivery rejects any number (Slide 12 step 11), time or name (Slide 24 scenario 2) that isn't in the stored flag, and any LLM sentence with judging or accusing words (a deny-list such as "theft", "stole", "suspicious", "likely"; design choice), and sends the template fact line instead.
Notice first. The §52-c*2 notice is given, acknowledged and posted before monitoring.
No sensors. No cameras, audio, biometrics, location or phone-use data (Slide 21).
Toast waits for v2.
Cost. The lean run cost is about $20–25 per restaurant per month, against a $79–99 price. The ~$1 token line assumes $0.10/$0.50 per million tokens. Today that matches Claude Haiku 5.5 (claude-haiku-5-5) for prompts of 100k tokens or fewer. Pin the model ID (a design choice). Keep prompts under 100k tokens, because above that Haiku 5.5 costs $0.50/$2.50. In the cost step, re-check the price, confirm the pinned ID, and meter all output tokens, including thinking. Run explanation calls at low effort (design choice).

Team. A founder whose strongest language is Python, plus a small team of AI engineers who can run parallel Claude Code sessions in separate worktrees.

PRIVATE_EVIDENCE_DIR is an absolute path outside the repo, given to you in the interview. Signed documents in it must never enter Claude's context (G5 in <governance>). </situation>

<task> Divide the v1 build into ordered steps that can each be checked on their own. Write them as files the team runs one step at a time, each in a fresh Claude Code session. Each step leaves the system working and proves it with a gate that passes or fails.

Write these files:

docs/build/BUILD_PLAN.md, containing:
a one-paragraph strategy;
the step table;
a Mermaid dependency graph;
milestones and gates;
parallel lanes;
the coverage table;
the v1 out-of-scope list;
"Design choices for the founder to accept";
"Decisions the founder must make", each with the step it blocks.
docs/build/steps/STEP-NN-short-name.md: one file per step, under about 80 lines, in the format the examples show. Number every step STEP-NN with two digits, human-track steps included.
docs/build/status/STEP-NN.json: one file per step, so parallel PRs never edit the same file, plus docs/build/proposed/tools/build_progress.py, which generates docs/build/progress.json from them. Each status file holds:
id
title
track (build or human)
lane
assignee (the engineer running the step)
status (not_started, in_progress, blocked or done)
depends_on: step ids that must be done before the step starts
done_requires: step ids that must be done only before this step's done PR merges
gate_kind: ci_fixture, ci_staging, production_job, sandbox_spike or human
gate: the exact command; for production_job and human, the exact command the founder runs
evidence_path
docs/build/evidence/: an empty folder with a README explaining the evidence rule.
docs/build/gates/STEP-NN.txt: one file per step, listing the gate-test files that the hook and CI protect. progress.json is generated in CI and gitignored, so no two PRs ever edit a shared file.
docs/build/GOVERNANCE.md and docs/build/proposed/. These hold:
the proposed CLAUDE.md (40 lines or fewer): the setup command for fresh worktrees, the test command, the evidence rule, the gate-edit rule, the human-confirmation rule, and AWAITING HUMAN CONFIRMATION. Step files point to it instead of repeating these rules;
settings, hooks, CI workflow, CODEOWNERS and the standard-library tools check_evidence.py, check_artifact.py and build_progress.py;
for each requirement in the <governance> section: the mechanism you chose, the doc URL you verified it against, install steps in order, a smoke test the founder runs by the point the table names, and any residual risk.
Each proposed file is written at the path it is installed to, under docs/build/proposed/ (so proposed/tools/check_evidence.py installs to tools/check_evidence.py). Write the tools and CI so they pass on a repo with no app code yet.
docs/build/go-no-go-criteria.md, marked DRAFT. The founder edits it and accepts it before the live spike.

Plan v1 in full. Outline v2 and v3 at milestone level, one paragraph each, with Slide 26's gates quoted verbatim:

v1 → v2: "the pilot passes, and a referral counts only after a second owner has paid for 60 days" (Slide 26; R2 §10).
v2 → v3: "a pass measure for v2: TBD — not in sources" (Slide 26; T12). </task>
<action> Work in two phases, and stop between them.

Phase A: understand, interview, outline. Write no repo files.

Read the documents as described. Read independent files in parallel.
Quote one line from each of these: Slide 11, Slide 25 (ADR-004), and the last lines of Slide 30. This shows you opened both parts.
Interview me with the AskUserQuestion tool: at most 4 questions per call, and at most 5 calls. Ask only about open decisions that change the order or the stack:
the managed PostgreSQL choice, its cost, and its backup and point-in-time-recovery retention (T9 for cost; retention relates to T15). The authorization's backup window must be at least that long;
the email vendor (T5);
whether the friend's shift windows are known now, or the owner sets them in the console at onboarding (Slide 16 SHF row; TD1 on Slide 29; T14);
whether to start the long-lead registrations now: Square app approval (T1) and Twilio 10DLC (T6);
how staff sign the acknowledgment (T16): on paper, with the founder entering it in the console, or by signing in the console. Signing in the console means staff sign on the owner's signed-in console; there are no staff accounts (Slide 21). This decides whether the console comes before the notice step.
the pilot start date;
the value of PRIVATE_EVIDENCE_DIR;
the GitHub plan (Free, Pro, Team or Enterprise), the founder's GitHub username, and one engineer's username as second code owner;
which operating systems the team uses (macOS, Linux or WSL2);
whether we already have our own Square production seller account and a host account.
Each question needs 2–4 options. For free-text answers (the path, usernames, dates), offer placeholder options; the answer comes back through the "Other" free-text row. Don't ask anything the pack already answers.
Present the outline as your plan for approval. Start it with the open gaps and the founder decisions, so I can approve without reading every row. Include:
the step table: id, title, track, one-line outcome, gate, depends on, size;
a coverage table mapping each item below to a step id or a founder decision:
each Slide 11 element;
each Slide 21 control;
each v1 entity on Slides 15–18;
each v1 node and arrow on Slides 22–23;
each of V1–V8;
each before-day-one item on Slides 26 and 30;
Slide 24 scenarios 1–4;
each numbered step 1–15 of the v1 flow on Slide 13;
each principle P1–P8, and each Slide-3 constraint L1–L7, T1–T3 and C1–C2.
the design choices you propose;
my interview answers;
your three quotes.
Phase B must still work if the conversation is compacted. End the outline with this line: "Phase B: before writing any file, re-read the Phase B part of the <action> section, the <governance> section and the <examples> in docs/build/PLANNING_PROMPT.md, and follow them."
Give each step a lane field and an empty assignee field, in the outline and in its status file. I fill in the assignees when I approve.

Phase B: after I approve, write the files.

Phase B runs in two sessions, so step-file quality doesn't drift late in a long session.

Phase B1 (this session). Write BUILD_PLAN.md first, starting with a section "Interview answers and approved outline" that records every answer (GitHub plan, usernames, operating systems, T16, PRIVATE_EVIDENCE_DIR and the rest), and ending with a checklist of every file still to write. Then write GOVERNANCE.md, docs/build/proposed/, docs/build/evidence/README.md and the go/no-go criteria draft. Print PHASE B1 DONE and stop.
Phase B2 (a fresh session). Read BUILD_PLAN.md, then this prompt's Phase B rules, <governance> and <examples>. Read both pack parts in full before the first batch, and before each batch re-read the slides its steps cite. Write the step, status and gate files in batches of about five steps, in step-table order, ticking each one off in BUILD_PLAN.md's checklist. Then do the final check below and print PHASE B2 DONE.

Shape the steps by the rules below.

The order below is fixed by the legal and data risks. Within it, you choose step boundaries, numbering, lanes and the technical approach.

Order: Square-sandbox spike → staging skeleton and OAuth → production environment and production OAuth check, with the human track in parallel from day one → go/no-go criteria → live-data proof → recorded go/no-go → data-dependent slices → pilot-readiness gate. Slices that don't depend on Square fields run in parallel lanes from the skeleton onward, on synthetic fixtures only.

Square-sandbox spike on our own test account. This is the only place a personal token is allowed (Slide 21). Record in docs/build/findings/:
the read-only scope names;
what Square's docs say about app approval for production OAuth, as input to the T1 human step (the sandbox can't show it);
which V-items the API shape can return.
The sandbox's behaviour is TBD in the sources, so observe it rather than assume it.
Walking skeleton, deployed to staging.
Code and infrastructure. Repo, CI, and PostgreSQL with row-level security.
Audit log. An append-only audit_log table, written through an insert-only role and an audit() helper.
Gate tooling. The founder installed check_evidence.py, check_artifact.py, CI and CODEOWNERS before STEP-01. This step only adds tests for them.
Secrets. All of them come from the host secret store: the Square application secret, the database URL, Twilio, Anthropic, email, and the AES key. How credentials reach local sessions and CI follows G4 and G7.
Local test database. Local database tests start their own PostgreSQL inside the test command, with a connection method verified to work inside Claude Code's sandbox on the team's operating systems (G7; design choice). ci_staging gates use the remote staging database only in CI.
Test data. Synthetic fixtures shaped like Square data. No real staff identifiers or spike samples go in the repo.
Staging. Deploy in the ADR-007 shape (or the T9 choice). Staging holds synthetic data only. CI staging gates use a database or schema per run, so concurrent runs on main don't collide. Don't put path filters on a workflow that holds a required check, because a skipped required check stays Pending and blocks merging.
Operations.
Cron failures and missed runs alert the founder by email.
Shift windows are in the restaurant's time zone and may cross midnight, so "yesterday" means the restaurant's business day (design choice).
Gate. A health check of the deployed console, one cron run on fake data, and one database test run inside a sandboxed Claude session.
OAuth connect, built and tested on staging against our own Square test account only, never the friend's. If the Square-sandbox spike finds no sandbox OAuth flow, record a founder decision before this step.
Authorize, exchange tokens, refresh every 7 days or less, and store tokens AES-encrypted.
The callback is served by the Owner Console, behind a minimal owner sign-in with two-factor built in this step.
This is the Square Connector's real auth code, not throwaway code.
Production environment, its own step.
Shape. The same as staging, plus its own secrets, RLS, AES key, daily backups and a tested restore.
Gate. The production service deploys, its HTTPS health check passes, the restore test passes, and the OAuth redirect URL is live.
Production OAuth check. A separate small build step checks connect, refresh and revoke against our own production Square account, never the friend's. It depends on this step and on provisioning our own production tenant. Its order against T1 follows the T1 dependency below.
Data. Its HTTPS URL is the production OAuth redirect target. All real data lives only here, including the spike's.
Deploys. Production deploys are manual and confirmed by the founder. Nothing auto-deploys from main.
Jobs. Until the pilot-readiness gate passes, production runs only these jobs:
Scheduled: the token-refresh job.
Deploy-time: database migrations, run by the founder as part of each manual production deploy.
Count-only query: if T16 is console signing, a founder-run query that returns only the acknowledgment count, for the notice step's evidence.
Provisioning, launched by the founder and audit-logged, as two steps with gate_kind production_job and a human confirmation line: (1) our own production tenant, which the production OAuth check depends on; (2) the friend's tenant and owner invite, with two-factor enrollment, which the console notice step (if any) and the live spike depend on.
One-off, launched by the founder:
the spike job and its deletion check (verify_deleted);
the restore test in this step;
the production OAuth check's connect, refresh and revoke runs, on our own production account;
after a go decision and once the Design Partner Agreement is signed, the roster read of Square team-member ids and display names, used only for the acknowledgment mapping (design choice), and the history pull;
after a no-go decision, the exit job: revoke, delete and verify the deletion.
The founder launches each one-off production job from the host's dashboard or CLI, then pastes the job id, exit code and output into the session. Every production job prints only counts, hashes, field names and exit status, never names, values or staff identifiers, and check_evidence.py rejects evidence that holds anything else. Claude sessions never hold production host credentials. The nightly-pull, explanation and digest jobs stay off behind a config flag.
T1 dependency. Decide from the Square-sandbox spike's finding on app approval, recorded as a founder-decision row:
Default (approval needs only the redirect URL, or no approval): T1 depends on this step, and the production OAuth check depends on T1.
Approval requires a working production connect: the production OAuth check runs on our own production account before approval, and T1 depends on it.
Human track, in parallel from day one, with early step numbers.
T1 resolved: approval granted, or confirmed not required.
Counsel review T17a, before any of these is used:
the notice text;
the owner's spike authorization;
the Design Partner Agreement (DPA; not a data processing agreement);
whether POS history from before the notice (the V8 check and the 30-day history pull) may feed per-login baselines, or only restaurant-level totals.
§52-c*2 notice given, acknowledged and posted (T16). This depends on T17a. It includes the owner telling staff that nobody is punished just because data shows up (Slide 21 workflow step 6; RK9). Add the build steps for the T16 answer:
T16 answer	Build step to add	Position (on production)	What it does
Console signing	"console notice and acknowledgment records"	after OAuth connect, before the notice step	Holds acknowledgment records only. The signing view shows only the notice and the signer's own acknowledgment, never flags or digests, and returns to owner sign-in after each signature.
Console signing	"mapping from acknowledgment to login"	after go/no-go, before the history pull	Maps each acknowledgment to a Square login, from the roster read or typed in by the founder from the Square dashboard.
Paper	"acknowledgment entry and mapping from acknowledgment to login"	after go/no-go, before the history pull	With the owner's written permission, logged as vendor support access (Slide 21), the founder enters each signed acknowledgment and maps it to a login from the roster read. The full console slice reuses it.
Every entry and mapping is audit-logged. The history pull, baselines and flags depend on the mapping step. No Square data is read before the spike. Apart from OAuth connect and owner sign-in, the console-signing step is the only console work deployed to production before go/no-go. Other console slices may be built and tested on staging with synthetic fixtures. If T16 is paper, the notice step itself needs no software.
The owner's signed written authorization for the spike. The founder drafts it on day one, with a stated maximum backup-retention window (design choice), together with the notice text and the DPA, as inputs to T17a, not as part of any step. T17a depends on no step. Signing the authorization, signing the DPA and giving the notice each list T17a in depends_on. Use done_requires only where work may start before its prerequisite is done. The production-environment step must keep backups within that window.
The signed pass line, including the T11 rule. Sign it after the spike, or sign it before with both variants written out: the measure if V1 is RETURNED, and the substitute if it isn't. RK2 puts the substitute measure and the 0.5–1 point rule in the Design Partner Agreement, so a DPA signed before the spike carries both variants.
The Design Partner Agreement, with 10–20% of the intended annual price charged up front (Slide 26). Slide 21 requires two promises written into the contract: the restaurant's data is never used to train a model, and a 30-day CSV export of all flagged events after termination (and the same if we shut down), then deletion per contract. Counsel reviews both under T17a.
The model-vendor no-training term (T8).
Twilio 10DLC registration, including the owner's SMS opt-in record. Record T6's approval time and message limits.
Counsel review T17b of the digest fact templates, the explanation prompt, the deny-list and sample LLM outputs, after the fact-templates slice and before the pilot-readiness gate. Any later change to a template file reopens T17b, and, once T17b is done, CI compares the hashes of every file in a committed template manifest (CODEOWNERS-protected; it lists the fact templates, the explanation prompt and the deny-list) with those recorded in T17b's evidence, and fails if a template file exists outside the manifest.
Read-only live-account spike.
Depends on: OAuth connect, the production environment, the production OAuth check, T1 resolved, T17a, the notice posted and acknowledged, the owner's authorization, and the founder-accepted go/no-go criteria.
Staff who haven't signed. "Acknowledged" means every current staff member has signed, or counsel's T17a answer allows the spike to run while some staff haven't signed (the spike keeps no per-login data). Absent or refusing staff never block the build silently: record them as a count in the notice step's evidence.
Where it runs. As a one-off job on the production host, so the token is never decrypted on a laptop. How the host runs one-off jobs is TBD — not in sources; check the host's docs (Render, per ADR-007), and if it has none, use a cron job the founder triggers by hand (design choice). Its gate is that job's exit code and output, recorded in the evidence file.
Data kept. No per-login rows and no values: only field names, types and counts. Where counting distinct logins needs identifiers, hash them with HMAC in memory, using a key from the secret store, and keep only the count.
Results. Mark each V-item RETURNED, NOT RETURNED or PARTIAL, and write each result to the audit log. PARTIAL counts as NOT RETURNED for digests (Slide 30: nothing appears in a digest until its test passes). If one sub-field passes on its own, record it as a separate RETURNED item.
Deletion. End with a check that proves the spike data is gone from the live database, and audit-log the deletion date. Backups and point-in-time recovery keep the data until they expire. State that window in the owner's authorization, and record the date the last backup holding spike data expires.
OAuth connection. State whether it is kept.
If kept, the production refresh job keeps it alive.
If revoked, the history-pull step starts with the owner reconnecting, under human confirmation.
Go/no-go decision, recorded by the founder using RK1. Judge it against criteria that the founder accepts and commits as docs/build/go-no-go-criteria.md before the live spike runs. It is founder-approved and protected under G1. Two human-track steps follow from this: accepting the criteria, which the spike depends on (as in the spike example), and the decision itself, which depends on the spike and records GO or NO-GO in its status file. Also list the decision under founder decisions. The criteria cover:
which V-items must be RETURNED for a useful digest;
what v1 shows if V2 fails, which is the fallback sentence without its login clause: "9 checks cancelled during shift Y".
No step that reads or uses Square fields starts before the decision is recorded: the history pull, the nightly pull, baselines and flags. Field-independent slices may start after the skeleton on synthetic fixtures: fact templates, the number, time and name check, the deny-list, the explanation service with a stubbed LLM, the CSV export, audit-log coverage and the owner console. Their gate tests that touch Square fields add the V-item branches after go/no-go.
If the decision is no-go, an exit step does five things:
revokes the Square OAuth authorization;
gives the owner an export of the notice and acknowledgment records, which the employer keeps;
deletes all tenant data from the live database, except the audit-log entries for the spike and the deletion. How long those are kept is a founder decision (T15). Records when the backups holding the data expire;
audit-logs the deletion;
settles any up-front payment under the Design Partner Agreement.
One vertical slice per step.
Pre-pilot history pull. 30 days (V8).
Pass line. The "before" figure is the 30 days ending the day before pilot day one (our reading). If the pull runs earlier, the founder re-runs it for that window when enabling the jobs.
Baselines. It feeds baselines only for logins whose acknowledgment is on file (ADR-006: "baselines start later"), and only as far as T17a allows pre-notice data to feed per-login baselines.
Other logins count only toward restaurant-level totals.
Nightly pull.
Shift-window settings. Entered by the owner in the console or by the founder, according to the T14 answer, and audit-logged. The history pull's per-shift totals, baselines and flags depend on this step.
Baselines per login and per owner-set shift window, only for logins whose acknowledgment is on file, including new hires during the pilot. Other logins count only toward restaurant-level totals (design choice).
Flags, with the acknowledgment gate built in. A login enters flags, and so the digest, only once its acknowledgment is on file. This is stricter than Slide 21's digest-level rule, so label it a design choice. It reads the mapping from acknowledgment to login, which exists before the history pull.
Fact templates.
The LLM explanation. Production calls wait for T8.
The number, time and name check in Digest & Delivery.
The digest. Email first. SMS turns on when the 10DLC step is done.
The full owner console, with notice records and acknowledgment entry.
The CSV export.
Audit-log coverage for:
sign-in, and failed or denied access attempts;
settings;
exports;
digests sent;
notices and acknowledgments entered;
V-item results;
support access.
Pass-line measurement. Voids + comps + discounts as a % of net sales (sales after refunds, Slide 26), or the agreed substitute, 30 days before and 60 days after. Slide 26 also fails the pilot if the owner stops opening the digest (Slide 24: "the pilot fails if the owner stops opening the digest"). How that is measured is a founder decision: a weekly check-in with the owner, or a disclosed link-click count.
Termination path. A 30-day CSV export of all flagged events, then deletion per contract, audit-logged (Slide 21).
Billing with one-click cancel. The sources name no billing provider (TBD — not in sources), and in-product billing is needed only when the 90-day term ends. The 10–20% up-front fee under the Design Partner Agreement is invoiced outside the product.
Pilot-readiness gate. All of these must hold. Only then does the founder enable the production nightly, explanation and digest jobs.
Quality scenarios 1–4 pass on staging.
The founder deploys the same release to production, and its health check passes.
Every item on Slide 26's "Before day one" list and Slide 30's is closed.
T17b is signed.
The 10DLC step is done and SMS sends on staging, including scenario 4's reconnect text.
A metered cost estimate (tokens and SMS segments) is within the lean line.
T8 is resolved, or the production digest runs template-only with LLM calls disabled, recorded as a founder decision.
The email and SMS vendors' data terms (T5, T6) are recorded, because digests carry login codes.
Scenario 5 then becomes a monthly bill check during the pilot.

Branches. Every data-dependent step states what it builds if a V-item is RETURNED, and what it builds if it isn't. Failed items use the Slide 12 fallback sentence or are left out.

Size and parallel work.

Size. A step fits in one fresh session and ends in one reviewable PR, plus a short done PR when its gate runs after merge (G3). Split any step bigger than about a day, or any step that touches the core logic of more than one container.
Parallel lanes. Steps with no dependency between them may run in parallel worktrees.

Gates.

Build steps end with a test command, a fixture diff, or a query with an expected result.
Quality scenarios 1–4 each become an automated test.
New tests per step. Gate-test files live under tests/gates/. Each step adds its own gate-test files, named exactly in its docs/build/gates/STEP-NN.txt, and may edit them until its done PR merges. After that, changing them needs a gate-change PR. Gate fixtures live beside their tests under tests/gates/ and are listed in docs/build/gates/STEP-NN.txt.
Human-track steps are gated by a script. It checks that a signed artifact exists under $PRIVATE_EVIDENCE_DIR, and records the artifact's SHA-256, the signer's role (owner, counsel or vendor; for staff acknowledgments, a count only, as a design choice) and the date. Names stay in $PRIVATE_EVIDENCE_DIR, which holds copies used for hashing; the owner keeps the signed originals. The founder's approval of the status PR is what marks these done (G2).

Integrity.

Build to behaviour. Acceptance criteria describe behaviour for all valid inputs, so fixture-only code fails them.
Invent no vendor facts. Vendor names, prices, scopes, API fields and limits come only from the documents, this prompt's situation section, or a spike finding in docs/build/findings/. You may also cite a current official vendor doc page by URL, labelled "unverified candidate" until a spike or the founder confirms it; interview options may name such candidates. Anything else is written "TBD — not in sources" and becomes a founder decision or a spike task.
Label engineering choices. Choices the sources leave open, such as web framework, test runner, migration tool and two-factor method, may be proposed. Label each "design choice" and list them once in BUILD_PLAN.md. Include every rule this prompt adds beyond the pack:
the T17a/T17b split, and what counsel reviews;
the spike: its authorization, HMAC hashing at ingest, running as a one-off production job, and the deletion check;
PARTIAL counting as NOT RETURNED;
the go/no-go criteria file and the no-go exit;
the fallback sentence without the login clause;
email first, and the owner's SMS opt-in;
billing timing;
the model pin and low-effort explanation calls (Haiku 5.5 defaults to medium effort, so set low explicitly);
production LLM calls gated on T8;
the local test database started by the test command;
the business-day rule, and display names never sent to the LLM;
the production OAuth check on our own production account, and the provisioning step;
the signing view's limits, requesting the roster-read scope at first connect (named in the owner's spike authorization, so counsel reviews it under T17a), and a two-factor method that doesn't depend on 10DLC;
acknowledgment capture, and the flag-level acknowledgment gate;
the roster read, and the pass-line "before" window;
staging, which is a second database, counted in T9 and the cost step;
the production environment, manual production deploys, and production jobs held off until the pilot gate;
cron alerts, backups and the restore test.
Keep v1 minimal. No abstractions, configurability, or stubs for later agents.

Ready-to-paste prompt in every step file.

Start. git fetch && git rebase origin/main, confirm the depends_on steps are done in their status files (CI checks done_requires on the done PR), read git log -5, and run CLAUDE.md's setup command, because worktrees are fresh checkouts.
Body. Explore, plan, write a failing test, implement, verify, then commit and open the PR with gh. If you stop after writing the failing test, print RED TEST (intentional). Reference files with @, and name what is out of scope.
Human confirmation. Steps that touch the friend's live account, real staff data or production secrets, or that send to a real phone or email, begin with a human confirmation line (rule in CLAUDE.md).
Evidence. Require evidence (the command run and its output), never a claim of success.
End. Finish with: "Use a subagent to review the diff against this step file and report only gaps that affect correctness or the stated acceptance criteria."

Progress and failure.

Done. A step is done only when docs/build/evidence/STEP-NN.md holds the gate command, its exit code and a summary of its output in G3's allowlisted lines (counts, hashes, run or job id). Raw output stays in the CI log or the founder's terminal.
What CI re-runs. CI decides from gate_kind alone (G3). It re-runs ci_fixture gates on PRs and ci_staging gates on main. Every other gate is evidence-only: CI checks the evidence format and recomputes the findings-file SHA-256 for spikes. Founder-launched production jobs never run in CI: migrations, provisioning, the restore test, the production OAuth check, the spike, the roster read, the history pull and the exit job.
No real sends in CI. A ci_staging gate never sends to a real phone or inbox, never needs a browser consent, and never calls a paid API without a mock or test credential. Use the vendors' test credentials or test modes only where their docs show one, otherwise a stub. Checks that need a real send or a consent click get gate_kind human and a human confirmation line. Examples: the first sandbox OAuth consent, and scenario 4's real reconnect text at the pilot gate.
Status files. Each step edits only its own docs/build/status/STEP-NN.json, and only through its PR.
Gate edits. Never edit or delete a gate check to make it pass. Never use --no-verify, skip CI or disable a hook. If a gate is wrong, mark the step blocked and give the reason. The gate is then changed in a separate gate-change PR that the founder approves (G1). Its branch is created with git switch -c gate-change/step-NN-reason, because claude --worktree names branches worktree-….
On failure. Each step file says: revert to the last green commit; mark the step blocked, with the failing output; after two failed attempts, restart in a fresh session with a narrower prompt.

Before you finish Phase B2: make sure the coverage table in BUILD_PLAN.md is still true for the files you wrote, and fix any gap.

Final reply (end of Phase B2). Keep it short. Include:

the files written;
the step count and the critical path;
the founder decisions, each with the step it blocks;
the design choices awaiting acceptance;
one sentence per gap you fixed. </action>
<governance> Use this section in Phase B, for `GOVERNANCE.md`, `docs/build/proposed/` and the skeleton step. In Phase A, use it only to shape the interview.

Design GOVERNANCE.md and docs/build/proposed/ to meet the requirements below with the least machinery: prefer GitHub settings over custom code, and enforce G1 and G3 in one CI job. For every mechanism, open the current Claude Code or GitHub doc page, cite its URL, and choose what works on the founder's GitHub plan and operating systems. Give each requirement a smoke test. If a requirement can't be met, list it as a founder decision with the residual risk and a fallback, and never claim enforcement that GitHub or Claude Code doesn't provide.

Id	Requirement	In place by
G1	Gate integrity. Protected paths change on main only through a gate-change PR the founder approves. Protected paths: tests/gates/ (CODEOWNERS covers all of it, so a step's own gate files, named exactly in its docs/build/gates/STEP-NN.txt, change with one code owner's review until that step's done PR merges; after that, CI rejects any change to them except on a gate-change/* branch), docs/build/gates/, tools/, conftest.py, pytest.ini, .github/, .claude/ settings and hooks, CODEOWNERS, CLAUDE.md, PLANNING_PROMPT.md, the go/no-go criteria, the fact-template manifest, and the RLS and audit-role migrations. Dependency changes in pyproject.toml need an ordinary review; CI fails if it holds test configuration. Founder installs pytest.ini, a conftest.py with the local PostgreSQL fixture, and every workflow (CI, staging deploy, ci_staging gates) from proposed/, so the skeleton step doesn't need to create protected files.	STEP-01
G2	Approvals. CODEOWNERS (founder plus second code owner) covers only the G1 paths, docs/build/evidence/, docs/build/findings/ and the status files of human, production_job and sandbox_spike steps. Everything else needs one approval from any collaborator who isn't the author. PRs that need the founder are opened from an engineer's account and session; the founder pastes their terminal or job output into that session and approves the PR. A PR the founder opens is approved by the second code owner, with the founder's sign-off line in the description. GitHub enforces only "a code owner who isn't the author": the rest is a team rule, written as residual risk. Turn on "Dismiss stale pull request approvals" and "Require approval of the most recent reviewable push", so nobody can push to another's PR and then approve it. Turn on "Do not allow bypassing the above settings". Break-glass means switching it off for one change and logging that in GOVERNANCE.md.	STEP-01
G3	Done means evidence. A done PR merges only when its evidence file passes check_evidence.py and its done_requires steps are done. Every evidence line follows a fixed allowlist grammar (command, exit code, SHA-256, count, role, date, job or run id, field names), so free text, names and values are rejected. On every PR, CI runs the full test suite plus the gate tests listed for ci_fixture steps that are in_progress or done. The gate job runs pytest -c pytest.ini --rootdir=. (CI fails on any other pytest config file, such as a nested pytest.ini, tox.ini or setup.cfg with a pytest section), sets PYTEST_DISABLE_PLUGIN_AUTOLOAD=1, reads JUnit output, and fails on any skip, xfail or zero tests collected in a gate file; CI also fails if a conftest.py exists outside the repo root and tests/gates/. ci_staging gates run on main after merge. A step's done PR cites the green main run id for its own gate, and CI verifies it with gh run view using GITHUB_TOKEN; a red run blocks only that step. GitHub-hosted runners need network access to the staging database, so choose a host plan that allows it (T9).	STEP-01
G4	Secrets. Claude sessions and CI never hold production credentials. Staging secrets live in a GitHub environment restricted to deployments from main. Local sessions get only Square-sandbox and vendor test credentials, never the staging database URL, and never in .env files or committed settings. Sandboxed commands can read most of the disk by default, so deny read access to host CLI, database and cloud credential files on every dev machine, but not gh's own credentials, which opening PRs needs.	STEP-01
G5	Private evidence and staff data. Nothing under PRIVATE_EVIDENCE_DIR enters Claude's context, including through scripts Claude runs. The founder runs check_artifact.py in their own terminal; it prints only SHA-256, signer role, count and date. Human-step prompts print the full command with the absolute path written out, then wait with AWAITING HUMAN CONFIRMATION.	STEP-01
G6	Claude can't approve, merge or push to main. Permission deny rules stop Claude sessions running gh pr review, gh pr merge and git push to main. Deny rules don't bound what a program does, so other routes are residual risk.	STEP-01
G7	Sandbox. Step sessions run in Claude Code's sandbox with the unsandboxed-retry escape hatch closed in both the project settings and each developer's user settings (~/.claude/settings.json), which the sandboxing docs say holds even when project settings say true. Check in the docs whether .claude/settings.local.json can still reopen it, and if so, list that as residual risk. Don't close it through managed settings or --settings, which makes the repo's excludedCommands ignored. Also set sandbox.failIfUnavailable: true. Smoke tests, before STEP-01 on each operating system: the /sandbox Overrides tab shows strict sandbox mode; Claude runs touch ~/sandbox-probe and no unsandboxed retry is offered; and the proposed conftest.py database fixture passes in a sandboxed session (on macOS this may need allowLocalBinding). Local tests, git push and opening a PR work inside it on the team's operating systems. If gh can't run sandboxed on macOS, the founder chooses between excluding gh (residual risk) and opening PRs from their own terminal.	STEP-01
G8	Hooks (optional; skip unless the founder asks). At most two. Hook scripts are G1-protected, fail closed, and never run app or test code. Mirror every hook rule in CI, because a hook on Claude's edit tools doesn't see writes made through Bash. A Stop hook only checks the evidence file's format, and always allows the stop when stop_hook_active is true, when the last message contains AWAITING HUMAN CONFIRMATION or RED TEST (intentional), when the step is blocked, or when its gate_kind isn't ci_fixture.	before the first production job

Plan up to three days for the founder to install and smoke-test G1–G7.

Pitfalls to design around. These were confirmed against the docs on Oct 20, 2026; re-check them.

Sandbox network. It only carries tools that use its HTTP(S) proxy. Database drivers and plain ssh can't connect through it, even to an allowed host. Unix-socket access can be blocked (on Linux, when the seccomp filter is installed), Docker and testcontainers don't work inside the sandbox, and binding a local port behaves differently on macOS and Linux. On macOS, some CLIs such as gh can fail TLS verification inside the sandbox; the sandboxing page describes the fix.
Hooks. They run outside the sandbox with full access. A PreToolUse hook that crashes blocks the tool call only with "onFailure": "block", which needs Claude Code v2.1.295 or later and has no effect on Stop hooks.
Read deny rules also apply to sandboxed commands.
Worktrees. claude --worktree NAME creates the branch worktree-NAME.
GitHub.
On private repos, branch protection, CODEOWNERS enforcement, environment secrets and deployment-branch policies need a paid plan.
Environment required reviewers on private repos need GitHub Enterprise.
A required status check can be selected only after it has succeeded in the repo within the past 7 days.
Authors can't approve their own PRs. </governance>
<result> Done means: - BUILD_PLAN.md's step table and graph show the whole v1 build at a glance: order, dependencies, parallel lanes and gates. - Any engineer can open one `STEP-NN` file, paste its prompt into a fresh session, and finish the step without reading anything else first. - Before any feature depends on them: - the data is proven; - the legal ground is cleared; - the go/no-go decision is recorded. - Every step ends in a gate that passes or fails, with the evidence on file and CI re-running it wherever it can run without live credentials or private files. - The plan invents no vendor capability, scope, price or number. Every open engineering choice is labelled.

Make the plan strong enough that a careful senior engineer reviewing it would change little: precise interfaces, honest unknowns, and gates that can't be passed by accident. </result>

<examples> These show the format only. Their step numbers are illustrative: number steps by your own step table, and give long-lead human steps (10DLC, the DPA, T1) early numbers. Every step file includes all the fields shown across the examples: - Track - Depends on - Blocks - Outcome - Human confirmation, if any - Out of scope - Gate - If the gate fails

Take every step's content from the documents, not from these examples.

<example name="spike step (abridged)"> # STEP-13 Read-only live-account spike (closes V1–V8) Track: build. Depends on: STEP-04 OAuth connect, STEP-05 production environment, STEP-06 T1 resolved, STEP-07 counsel T17a, STEP-08 notice acknowledged and posted, STEP-09 owner's spike authorization, STEP-10 friend's tenant provisioned, STEP-11 production OAuth check, STEP-12 go/no-go criteria accepted. Blocks: STEP-14 go/no-go. Outcome: `docs/build/findings/square-fields.md` marks each V-item RETURNED, NOT RETURNED or PARTIAL, with the API call and the field names and types returned (no values); each result is written to the audit log. Human confirmation: "Confirm the owner's authorization and the posted notice are on file before I connect." Print AWAITING HUMAN CONFIRMATION until answered. Out of scope: keeping data after the spike; any rule or digest code. Gate: the one-off production jobs `square_live_report --check` (all 8 items filled) and `verify_deleted` both exit 0. The evidence file records each job's id, exit code and output. If the gate fails: mark blocked with the failing output; do not retry against the live account without the owner's OK. </example> <example name="slice step with a V-item branch (abridged)"> # STEP-17 Per-login discount and refund flags Depends on: STEP-14 go/no-go, STEP-16 baselines. If V7 is RETURNED: flag discounts and refunds per login and shift window against that login's baseline, and only for logins whose acknowledgment is on file. If V7 is NOT RETURNED: flag them per shift window only; the digest names no login. Out of scope: digest wording; the LLM explanation. Gate: `pytest tests/gates/step_17/test_discount_refund_flags.py` passes for both branches on synthetic fixtures in `tests/gates/step_17/fixtures/`. </example> <example name="status file and evidence file"> `docs/build/status/STEP-17.json`: {"id": "STEP-17", "title": "Per-login discount and refund flags", "track": "build", "lane": "rules", "assignee": "", "status": "in_progress", "depends_on": ["STEP-14", "STEP-16"], "done_requires": [], "gate_kind": "ci_fixture", "gate": "pytest tests/gates/step_17/test_discount_refund_flags.py", "evidence_path": "docs/build/evidence/STEP-17.md"}

docs/build/evidence/STEP-17.md: command: pytest tests/gates/step_17/test_discount_refund_flags.py exit_code: 0 count: 12 passed date: 2026-11-02 run_id: <id of the green CI run on the commit just before the evidence commit; CI checks that run's head SHA is the evidence commit's parent and that the evidence commit changes only this step's evidence and status files> </example>

<example name="acceptance criterion: weak vs strong"> Weak: "The digest looks right." Strong: "Given `tests/gates/step_NN/fixtures/week_with_3_flags.json`, `pytest tests/gates/step_NN/test_digest.py` passes. The SMS body contains only numbers, times and names present in the stored flag rows. Any LLM sentence that adds another is replaced by the template fact line (Slide 24, scenario 2)." </example> <start> Begin Phase A now, unless I've asked you to run Phase B2; then follow Phase B2 only. Give a one-line statement of what you're doing before your first tool call. </start>
