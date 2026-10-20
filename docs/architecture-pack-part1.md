# Restaurant Platform Architecture Pack — part 1 of 2 (Slides 1–15)

Source: Restaurant-Platform-Architecture-Pack.pptx (Claude Design, Oct 19, 2026). Each section is one slide's speaker notes, which hold the slide's full text. Arrows are written as "Arrow from X to Y".

## Slide 1 — Restaurant Platform Architecture Pack
01 Cover and decision summary

Full text of this artboard (arrows are written as "Arrow from X to Y"):

ENTERPRISE ARCHITECTURE PACK · 01 / 16 · OCTOBER 19, 2026
Restaurant Platform Architecture Pack
The target-state platform for the restaurant problems software can solve, and the v1 slice that ships first: a POS-data monitor on Square for one independent NYC restaurant.
THE DECISION

We will not build R1's 7-module platform. We will build one narrow agent first (R2 §10). It reads the restaurant's Square POS data through OAuth (Checked 2026-10-19). For each login and shift, it counts cancelled orders, comps, discounts, refunds and no-sale drawer opens. Then it texts or emails the owner a short ranked digest of time-stamped facts 2–3 times a week (R2 §2). Plain code finds the anomalies, and an AI model only explains them in plain English (R2 §2). It recommends and the owner decides. It never changes the POS, payroll or schedules (R2 §5). Price: under $100 a month, month-to-month (R2 §10). Run cost: about $20–25 a month per restaurant (R2 §3). The pilot passes only if voids + comps + discounts fall by at least 1 point of net sales (R2 §6).

v1 does
Reads Square orders, refunds and cash-drawer events every night (R2 §2)
Baselines each login and shift (R2 §10)
Texts and emails the owner only (R2 §2, §6)
Records each staff member's monitoring notice and signed acknowledgment (Checked 2026-10-19)
v1 does not
Use cameras, audio or biometrics (R2 §6, §10)
Connect to Toast. That is phase 2 (R2 §10)
Label anyone a thief or alert staff (R2 §6)
Change the POS, payroll or schedules (R2 §5)
FOR THE OWNER (10 MINUTES)
01 decision · 02 what each problem gets · 07 what the digest says · 11 what staff are told · 15 pass or fail
FOR THE DEVELOPER (BUILD FROM)
06 v1 containers · 07 flow · 09a–b data model · 10 integrations · 11 security · 14 ADRs · 16d verify list
2.8%
Median full-service profit as a share of sales, 2024 (R2 §1)
42%
Operators not profitable in 2025 (R2 §1)
about 22%
Drop in theft with POS-data monitoring, across 392 restaurants (R2 §1)
$79–99
Target monthly price for the lean product (R2 §3)
$50/mo
Toast integration portal fee per US location, so Toast waits (Checked 2026-10-19)
≥ 1 point
Pilot pass line: voids + comps + discounts as a % of net sales (R2 §6)
IN THIS PACK
01 Cover and decision
09a–b Domain data model
02 Problem → capability traceability
10 Integration view
03 Principles and constraints
11 Security, privacy, NY compliance
04 C4 L1 System context
12 Deployment and cost
05a–b C4 L2 Containers (target)
13 Quality attribute scenarios
06 C4 L2 v1 slice
14 Architecture decision records
07 Dynamic view: v1 flow
15 Roadmap and pilot pass line
08 Agent catalog
16a–d Risks, conflicts, open questions
Element-catalog appendices follow the diagrams that need them.
Words used here: POS the cash-register software · void cancelling an item after it was rung up · comp an item given free (R2 p.2) · OAuth Square’s “approve this app” connection · LLM the AI model that writes text (R2 §2) · SOP a written standard procedure (R1 p.20) · TBD not decided; the sources do not say
R1 Restaurant Problems: Deep Research Report (Oct 15, 2026) · R2 Build One Narrow Agent, Not the Platform (Oct 16, 2026), the decision baseline · Checked vendor docs and NY statutes, Oct 19, 2026
Where R1 and R2 disagree, this pack follows R2 and logs the conflict on artboards 16a and 16b. Numbers appear exactly as the source gives them.
v1 slice
Later phase
Out of scope / grey context
Verify on live account

## Slide 2 — Problem → capability: what each of the 15 problems gets
02 Problem to capability traceability

Full text of this artboard (arrows are written as "Arrow from X to Y"):

02 / 16 · TRACEABILITY
Problem → capability: what each of the 15 problems gets
One primary status per problem, in the owner's order. Indirect help and hard limits are noted beside it.
v1 · 3
v2 · 1
v3 · 6
process/policy only · 4
out of scope · 1
#
Problem
Primary status
Capability (agent, phase)
Why this status
Indirect help · limitation
Source
1
Consistent food
process/policy only
Written recipes and chef line checks
Checking each plate needs cameras. Camera plate-recognition startups failed on cost and false positives
Indirect: Agent 6 recipe quizzes (v3); Agent 4 variance shows drift (v3)
(R1 p.3–4; R2 §2)
2
Portioning (plate level)
out of scope (needs cameras or hardware)
None in the target state
Plate-level portion size needs cameras or scales. The best camera-only estimate has 18.8% mass error
Indirect only: Agent 4 inventory variance (v3)
(R2 §1, §2; R1 p.5)
3
Quality control
process/policy only
Manager opening and closing checks
No R2 agent covers it. Live temperature monitoring needs sensor hardware
Indirect: Agent 6 quizzes staff on storage procedures (v3)
(R1 p.6; R2 §2)
4
Employee theft
v1
Agent 1 Comp-and-void monitor: cancelled orders, comps, discounts, refunds
The one intervention with peer-reviewed payback; no hardware
Limit: drinks poured and never rung up leave no POS trace (R2 §2)
(R2 §1, §2, §10)
5
Favoritism / free extras
v1
Agent 1: comps and discounts ranked per login and shift
Comps and discounts are POS records. Comp detail through the API: verify on live account
Limit: drinks poured and never rung up leave no POS trace (R2 §2)
(R2 §2, §9; Checked 2026-10-19)
6
Cash theft
v1
Agent 1: refunds, no-sale drawer opens, cancelled-order counts
Square's Orders API does not return voided items, so v1 counts cancelled orders only
Limit: void $ amount and login on voided orders: verify on live account
(R2 §2; Checked 2026-10-19)
7
Time theft
v2
Agent 2 Clock checker: missed punches, early clock-ins, overtime drift
39% of payroll errors came from missed punches. Square Plus already blocks early clock-ins for $49 a month
Limit: no fingerprint clock may be required (Labor Law §201-a, Checked 2026-10-19)
(R2 §2; Checked 2026-10-19)
8
Phone use on shift
process/policy only
Written phone policy and manager coaching
Software cannot solve it without cameras. The only vendor found uses human remote auditors
None
(R2 §2)
9
Training
v3
Agent 6 SOP nudges: 2-minute SMS quizzes from the owner's procedures
Cheap, but incumbents fail on "no time": 62% of operators give 1–2 hours of training a week
Indirect: Agent 7 gets new hires in faster (v3)
(R2 §2)
10
Customer data
v3
Agent 3 Phone agent: takes calls, captures name and number with consent
Voice is the costliest line: about $106–179 a month for 1,200 minutes
Limit: delivery apps will not share their customer data
(R2 §2, §3)
11
Inventory counts
v3
Agent 4 Inventory variance: invoices, counts, recipes, item sales
Works only if someone keeps recipes and counts current. "Build later, if at all"
Indirect: catches portioning drift (problem 2), only indirectly
(R2 §2)
12
Busy times and staffing
v3
Agent 5 Forecast
Low priority: Toast IQ Team and Square Shifts already bundle forecasts
Indirect: Agent 2 flags overtime drift (v2)
(R2 §2)
13
Writing SOPs
process/policy only
The owner writes procedures
Agent 6 builds on the owner's own procedures. AI drafting of SOPs: TBD — not in sources
Indirect: Agent 6 delivers them once written (v3)
(R2 §2)
14
Retraining on changed SOPs
v3
Agent 6 SOP nudges for SOP rollout
R2 assigns SOP rollout to Agent 6; cheap to run over SMS
None
(R2 §2)
15
Hiring
v3
Agent 7 Hiring scheduler: fast text replies and interview booking only
36% of applicants drop out from slow replies. Humans evaluate candidates (NYC Local Law 144)
None
(R2 §2)
Phases: v1 = Agent 1 on Square. v2 = Agent 2 and the Toast connector. v3 = Agents 3–7, one at a time, only after the previous phase proves itself (R2 §6, §10). "Verify on live account" items are listed on artboard 16.
R1 = Oct 15 report · R2 = Oct 16 report · Checked = Oct 19, 2026

## Slide 3 — Eight principles every component must obey, and the rules we cannot break
03 Principles and constraints

Full text of this artboard (arrows are written as "Arrow from X to Y"):

03 / 16 · PRINCIPLES AND CONSTRAINTS
Eight principles every component must obey, and the rules we cannot break
Principles are our choices. Constraints come from law, vendors and money. Each one names what it forces in the design.
ARCHITECTURE PRINCIPLES
P1 · One narrow wedge first
Ship Agent 1 only. Add one agent at a time, each after the last one proves itself. (R2 §6, §10)
So: v1 has one agent, one POS and one delivery channel.
P2 · Rules first, model second
Plain code computes ratios and baselines per login and shift. The LLM only explains the few flagged anomalies. (R2 §2)
So: every flag can be reproduced without the model.
P3 · Recommend; the owner decides
Agents never change the POS, payroll or schedules. "Recommend; do not act." (R2 §5)
So: read-only POS access; no write path exists. Exact Square scopes: TBD — not in sources.
P4 · State facts, never labels
Digests give counts, times and logins, never "thief", and go to the owner only. (R2 §6)
So: fixed fact-only templates; the LLM cannot add accusations.
P5 · Stay off the service path
A failure during service can destroy trust permanently. AI that takes control of operations gets pulled. (R1 p.32; R2 §5)
So: nightly reads only. If we are down, the restaurant runs normally.
P6 · Push to the owner, not a dashboard
Median software products see only 37% of users return after week one (2017). Deliver by text and email, 2–3 times a week. (R2 §2)
So: no dashboard in v1; never a staff group chat (R2 §6).
P7 · Honest about limits
"Test comps on a live account before promising them." "Do not promise integrations that are not working." (R2 §2; R1 p.31)
So: unconfirmed fields carry "verify on live account" and are not shown until tested.
P8 · Legally clean by design
Staff notice before monitoring, no biometrics, no cameras or audio in v1, and no AI training on the restaurant's data. (R2 §6)
So: compliance records are first-class data, built in v1.
CONSTRAINTS (L = LEGAL · T = TECHNICAL · C = COMMERCIAL)
ID
Constraint
What it forces in the design
Source
L1
NY Civil Rights Law §52-c*2: notice at hire, signed acknowledgment, posted notice. AG penalties up to $500 / $1,000 / $3,000
Notice and acknowledgment on file before any monitoring starts
(Checked 2026-10-19)
L2
NY Labor Law §201-a: no one may be required to be fingerprinted to get or keep a job
No mandatory fingerprint clock
(Checked 2026-10-19)
L3
NYC requires signage for any biometric capture, with a private right of action
No biometrics in any phase
(R2 §6)
L4
NY Labor Law §193 forbids deducting losses from wages
The digest never suggests a deduction
(R2 §1)
L5
"We fired her for stealing" is defamation per se in New York if false
Facts only, owner only, no "thief" label
(R2 §6)
L6
No video in restrooms or changing rooms (§203-c); recording conversations without consent is a felony (§250.05)
No cameras or audio in v1
(R2 §6)
L7
Scoring candidates triggers NYC's hiring bias-audit law, Local Law 144
Agent 7 books interviews; humans evaluate candidates
(R2 §2)
T1
Square partner apps must use OAuth, never a seller's personal access token. OAuth tokens expire every 30 days
OAuth for the pilot too; refresh every 7 days or less; encrypt stored tokens
(Checked 2026-10-19)
T2
Square's Orders API does not return voided items; voided orders come back CANCELED without line items
Count cancelled orders only
(Checked 2026-10-19)
T3
Toast integrations need a $50/month portal per US location; Standard API access is read-only
Toast is phase 2. Partner path and terms: TBD — not in sources
(Checked 2026-10-19)
C1
Median full-service profit was 2.8% of sales in 2024. Owners leave over add-on fees, blocked cancellation and vanishing support
Under $100 a month ($79–99), month-to-month, one-click cancel, no hidden fees
(R2 §1, §3, §4, §6)
C2
Self-hosted n8n may be used "only for your own internal business purposes"
Write automations in code
(R2 §3)
Whether reading POS logs counts as electronic monitoring under §52-c*2 is not confirmed (R2 §9). We give the notice anyway; it costs one page (R2 §6).
R1 = Oct 15 report · R2 = Oct 16 report · Checked = Oct 19, 2026

## Slide 4 — System context, target state: the people and systems the platform talks to
04 C4 L1 System context (target)

Full text of this artboard (arrows are written as "Arrow from X to Y"):

04 / 16 · C4 LEVEL 1 · SYSTEM CONTEXT · TARGET STATE
System context, target state: the people and systems the platform talks to
Owner
[Person] · v1
Reads the digest; decides what, if anything, to do.
Restaurant Ops Platform
[Software system: multi-tenant SaaS] · v1 to v3
Reads POS and labor data, flags anomalies per login and shift, has a model explain them in plain English, and tells the owner. Recommends; never changes the POS, payroll or schedules.
Staff
[Person] · v1
Gets written notice at hire; signs the acknowledgment.
Square POS
[External: Square APIs] · v1
Orders, refunds, discounts and cash-drawer records.
Toast POS
[External: Toast API] · v2
$50/mo portal; standard access is read-only.
7shifts
[External: 7shifts API] · v2
Timecards and schedules (or Square Labor API).
Applicants & callers
[Person] · v3
Applicants by text; callers by phone.
LLM API
[External: Anthropic API] · v1
Haiku-class model explains flagged facts.
Twilio
[External: SMS API] · v1
Sends texts from a number with 10DLC.
Email service
[External: vendor TBD] · v1
Delivers digest emails.
Voice provider
[External: voice agent] · v3
Retell, Vapi or Bland; answers calls.
Arrow from Owner to Restaurant Ops Platform: A1 connects Square and sets digest preferences in · v1
Arrow from Restaurant Ops Platform to Owner: A2 texts and emails a ranked digest 2–3 times a week to · v1
Arrow from Restaurant Ops Platform to Square POS: A3 pulls orders, refunds and cash-drawer events nightly from · v1
Arrow from Restaurant Ops Platform to Toast POS: A4 pulls orders from · v2
Arrow from Restaurant Ops Platform to 7shifts: A5 reads timecards and schedules from · v2
Arrow from Restaurant Ops Platform to Applicants & callers: A6 texts applicants and answers calls for · v3
Arrow from Restaurant Ops Platform to LLM API: A7 sends flagged facts only, for a plain-English explanation, to · v1
Arrow from Restaurant Ops Platform to Twilio: A8 sends digest and staff texts through · v1
Arrow from Restaurant Ops Platform to Email service: A9 sends digest emails through · v1
Arrow from Voice provider to Restaurant Ops Platform: A10 hands caller name, number and booking to · v3
Arrow from Staff to Restaurant Ops Platform: A11 signs the monitoring-notice acknowledgment in · v1
Arrow from Restaurant Ops Platform to Staff: A12 sends 2-minute SOP quizzes to · v3
What this shows: Target state with the platform as one box. Colour shows when each relationship arrives. Arrows point the way the request goes. Element catalog: 11 boxes and 12 arrows, every one a row on artboard 04·A.
Legend
v1 slice
later phase (v2, v3)
the platform, all phases
v1 call
later call

## Slide 5 — System context catalog: every box and arrow on artboard 04
04·A Context element catalog

Full text of this artboard (arrows are written as "Arrow from X to Y"):

04·A / 16 · APPENDIX · ELEMENT CATALOG FOR ARTBOARD 04
System context catalog: every box and arrow on artboard 04
BOXES (11)
ID
Name
Type
Technology
Phase
Source
OWN
Owner
Person
Phone (SMS), email, web browser
v1
(R2 §2, §6)
PLT
Restaurant Ops Platform
Software system: multi-tenant SaaS
Python services on shared hosting (design choice)
v1 to v3
(R2 §2, §5, §10)
STF
Staff
Person
Capture method TBD — not in sources
v1
(Checked 2026-10-19)
SQ
Square POS
External: Square APIs
Square APIs via OAuth; its MCP server (beta) not used
v1
(R2 §2; Checked 2026-10-19)
TST
Toast POS
External: Toast API
Toast API; partner path TBD — not in sources
v2
(Checked 2026-10-19; R2 §2–3)
SHF
7shifts
External: 7shifts API
7shifts API; admin-created token
v2
(R2 §2)
APP
Applicants & callers
Person
SMS; phone
v3
(R2 §2)
LLM
LLM API
External: Anthropic API
Anthropic API, Haiku-class model (lean design)
v1
(R2 §3)
TWL
Twilio
External: SMS API
SMS API; number + 10DLC campaign fee
v1
(R2 §3)
EML
Email service
External: vendor TBD
TBD — not in sources
v1
(R2 §2)
VOX
Voice provider
External: voice agent
Retell, Vapi or Bland
v3
(R2 §2)
ARROWS (12) · FROM → TO, VERB PHRASE, DATA, PROTOCOL
ID
From
To
Verb phrase
Data
Protocol
Phase
Source
A1
Owner
Restaurant Ops Platform
connects Square and sets digest preferences in
OAuth consent on Square's screen; phone, email, preferences
HTTPS (browser)
v1
(Checked 2026-10-19; R2 §6)
A2
Restaurant Ops Platform
Owner
texts and emails a ranked digest 2–3 times a week to
Ranked facts per login and shift, with times
SMS and email
v1
(R2 §2, §6)
A3
Restaurant Ops Platform
Square POS
pulls orders, refunds and cash-drawer events nightly from
Orders (CANCELED counted only), refunds, discounts; comps and drawer events: verify on live account
JSON over HTTPS, OAuth, read-only scopes TBD
v1
(R2 §2; Checked 2026-10-19)
A4
Restaurant Ops Platform
Toast POS
pulls orders from
Orders and checks
HTTPS; access path TBD — not in sources
v2
(Checked 2026-10-19)
A5
Restaurant Ops Platform
7shifts
reads timecards and schedules from
Punches, shifts, schedules
HTTPS; admin token (multi-restaurant use unverified)
v2
(R2 §2)
A6
Restaurant Ops Platform
Applicants & callers
texts applicants and answers calls for
Interview slots; reservations
SMS; voice
v3
(R2 §2)
A7
Restaurant Ops Platform
LLM API
sends flagged facts only, for a plain-English explanation, to
Flagged facts only; never full history
HTTPS API
v1
(R2 §2–3)
A8
Restaurant Ops Platform
Twilio
sends digest and staff texts through
Message text, phone numbers
HTTPS API
v1
(R2 §3)
A9
Restaurant Ops Platform
Email service
sends digest emails through
Digest text, owner email
API TBD — not in sources
v1
(R2 §2)
A10
Voice provider
Restaurant Ops Platform
hands caller name, number and booking to
Name and number captured with consent
Webhook; format TBD — not in sources
v3
(R2 §2)
A11
Staff
Restaurant Ops Platform
signs the monitoring-notice acknowledgment in
Signed acknowledgment and date
Capture method TBD — not in sources
v1
(Checked 2026-10-19)
A12
Restaurant Ops Platform
Staff
sends 2-minute SOP quizzes to
Quiz questions and answers
SMS
v3
(R2 §2)
Every box and arrow on artboard 04 is one row here, and every row is drawn there. Technology marked “design choice” is settled in the ADRs on artboard 14. “Verify” = verify on live account (artboard 16).

## Slide 6 — Containers, target state, part 1: how POS and labor data get in
05a C4 L2 Containers (target) part 1

Full text of this artboard (arrows are written as "Arrow from X to Y"):

05a / 16 · C4 LEVEL 2 · CONTAINERS · TARGET STATE · PART 1 OF 2
Containers, target state, part 1: how POS and labor data get in
Restaurant Ops Platform [software system boundary]
Owner
[Person] · v1
Connects Square; keeps staff notices.
Staff
[Person] · v1
Signs the monitoring acknowledgment.
Owner Console
[Container: Python web app] · v1
Square OAuth connect, staff notice and acknowledgment records, settings, 30-day CSV export. Owner-only sign-in.
Square POS
[External: Square APIs] · v1
Orders, refunds, discounts, cash-drawer records.
Square Connector
[Container: Python job] · v1
The only code that calls Square. Read-only.
Toast POS
[External: Toast API] · v2
Standard API access is read-only.
Toast Connector
[Container: Python job] · v2
Same job for Toast restaurants.
7shifts
[External: 7shifts API] · v2
Timecards and schedules.
Labor Connector
[Container: Python job] · v2
Feeds Agent 2, the clock checker.
Platform Database
[Container: PostgreSQL] · v1
Tenant-scoped tables: POS events, baselines, flags, digests, staff notices and acknowledgments, an append-only audit log, and AES-encrypted OAuth tokens. Shared with 05b.
Arrow from Owner to Owner Console: B1 connects Square (OAuth consent), records staff notices, exports CSV in · v1
Arrow from Staff to Owner Console: B2 reads the monitoring notice and signs the acknowledgment in · v1
Arrow from Owner Console to Square Connector: B3 hands the OAuth code to · v1
Arrow from Square Connector to Square POS: B4 exchanges the code and refreshes tokens (every 7 days or less) with · v1
Arrow from Square Connector to Square POS: B5 pulls yesterday's orders, refunds and cash-drawer events from · v1
Arrow from Owner Console to Platform Database: B6 writes settings, notice records and encrypted tokens to · v1
Arrow from Square Connector to Platform Database: B7 reads its token from and writes normalized POS events to · v1
Arrow from Toast Connector to Toast POS: B8 pulls orders from · v2
Arrow from Toast Connector to Platform Database: B9 writes normalized POS events to · v2
Arrow from Labor Connector to 7shifts: B10 reads timecards and schedules from · v2
Arrow from Labor Connector to Platform Database: B11 writes shifts and timecards to · v2
What this shows: Split in two because the full container view has 22 boxes, over the 15-box limit. Part 2 (05b) covers rules, explanation and delivery. Element catalog: 10 boxes and 11 arrows, every one a row on artboard 05a·A.
Legend
v1 slice
later phase (v2, v3)
v1 call
later call

## Slide 7 — Containers part 1 catalog: every box and arrow on artboard 05a
05a·A Containers part 1 catalog

Full text of this artboard (arrows are written as "Arrow from X to Y"):

05a·A / 16 · APPENDIX · ELEMENT CATALOG FOR ARTBOARD 05a
Containers part 1 catalog: every box and arrow on artboard 05a
BOXES (10)
ID
Name
Type
Technology
Phase
Source
OWN
Owner
Person
Web browser
v1
(R2 §6; Checked 2026-10-19)
STF
Staff
Person
Capture method TBD — not in sources
v1
(Checked 2026-10-19)
CON
Owner Console
Container: Python web app
Python web app; owner-only sign-in (design choice)
v1
(Checked 2026-10-19; R2 §6)
SQ
Square POS
External: Square APIs
Square APIs via OAuth
v1
(R2 §2; Checked 2026-10-19)
SQC
Square Connector
Container: Python job
Scheduled Python job, nightly (design choice)
v1
(R2 §2; Checked 2026-10-19)
TST
Toast POS
External: Toast API
Toast API; $50/mo portal; partner path TBD
v2
(Checked 2026-10-19)
TSC
Toast Connector
Container: Python job
Scheduled Python job (design choice)
v2
(R2 §10; Checked 2026-10-19)
SHF
7shifts
External: 7shifts API
7shifts API; admin-created token
v2
(R2 §2)
LBC
Labor Connector
Container: Python job
Scheduled Python job; 7shifts or Square Labor API
v2
(R2 §2)
DB
Platform Database
Container: PostgreSQL
PostgreSQL, row-level tenant isolation (design choice)
v1
(Checked 2026-10-19; R2 §6)
ARROWS (11) · FROM → TO, VERB PHRASE, DATA, PROTOCOL
ID
From
To
Verb phrase
Data
Protocol
Phase
Source
B1
Owner
Owner Console
connects Square (OAuth consent), records staff notices, exports CSV in
Consent, notice records, export requests
HTTPS (browser)
v1
(Checked 2026-10-19; R2 §6)
B2
Staff
Owner Console
reads the monitoring notice and signs the acknowledgment in
Signed acknowledgment, date
HTTPS; capture method TBD
v1
(Checked 2026-10-19)
B3
Owner Console
Square Connector
hands the OAuth code to
One-time authorization code
Internal HTTPS call
v1
(Checked 2026-10-19)
B4
Square Connector
Square POS
exchanges the code and refreshes tokens (every 7 days or less) with
Access and refresh tokens (expire every 30 days)
OAuth over HTTPS
v1
(Checked 2026-10-19)
B5
Square Connector
Square POS
pulls yesterday's orders, refunds and cash-drawer events from
Orders (CANCELED counted only), refunds, discounts; comps, drawer events: verify on live account
JSON over HTTPS; read-only scopes TBD
v1
(R2 §2; Checked 2026-10-19)
B6
Owner Console
Platform Database
writes settings, notice records and encrypted tokens to
Settings, notices, acknowledgments, AES-encrypted tokens
SQL over TLS
v1
(Checked 2026-10-19; R2 §6)
B7
Square Connector
Platform Database
reads its token from and writes normalized POS events to
Encrypted token in; orders, refunds, discounts, events out
SQL over TLS
v1
(R2 §2)
B8
Toast Connector
Toast POS
pulls orders from
Orders and checks
HTTPS; access path TBD
v2
(Checked 2026-10-19)
B9
Toast Connector
Platform Database
writes normalized POS events to
Same event schema as Square
SQL over TLS
v2
(R2 §10)
B10
Labor Connector
7shifts
reads timecards and schedules from
Punches, shifts, schedules
HTTPS; admin token, multi-restaurant use unverified
v2
(R2 §2)
B11
Labor Connector
Platform Database
writes shifts and timecards to
Shifts, punches
SQL over TLS
v2
(R2 §2)
Every box and arrow on artboard 05a is one row here, and every row is drawn there. “Design choice” items are settled in the ADRs on artboard 14. “Verify” = verify on live account (artboard 16).

## Slide 8 — Containers, target state, part 2: rules, explanation and delivery
05b C4 L2 Containers (target) part 2

Full text of this artboard (arrows are written as "Arrow from X to Y"):

05b / 16 · C4 LEVEL 2 · CONTAINERS · TARGET STATE · PART 2 OF 2
Containers, target state, part 2: rules, explanation and delivery
Restaurant Ops Platform [software system boundary] · the database is the same box as on 05a
Owner
[Person] · v1
Gets the digest by text and email; decides.
Staff
[Person] · v1
Gets SOP quizzes from v3.
Applicants & callers
[Person] · v3
Applicants by text; guests calling in.
Email service
[External: vendor TBD] · v1
Delivers digest emails.
Twilio
[External: SMS API] · v1
Texts from a 10DLC number; inbound replies come back by webhook (v3).
Voice provider
[External: voice agent] · v3
Retell, Vapi or Bland.
LLM API
[External: Anthropic API] · v1
Haiku-class model; sees flagged facts only.
Digest & Delivery Service
[Container: Python job] · v1
Builds the fact-only digest 2–3 times a week; owner only.
Conversation Gateway
[Container: Python web service] · v3
Agents 3, 6, 7: SOP quizzes, hiring replies and booking, call capture. Never scores candidates.
Explanation Service
[Container: Python job] · v1
Turns top flags into plain English.
Rules & Baselines
[Container: Python job] · v1
Ratios, baselines and ranks per login and shift.
Platform Database
[Container: PostgreSQL] · v1
Same database as 05a: events, baselines, flags, explanations, digests, audit log.
Arrow from Email service to Owner: C1 delivers digest emails to · v1
Arrow from Twilio to Owner: C2 delivers digest texts to · v1
Arrow from Twilio to Staff: C3 delivers SOP quizzes to · v3
Arrow from Twilio to Applicants & callers: C4 texts interview replies and slots to · v3
Arrow from Applicants & callers to Voice provider: C5 call the restaurant line answered by · v3
Arrow from Digest & Delivery Service to Email service: C6 sends digest emails through · v1
Arrow from Digest & Delivery Service to Twilio: C7 sends digest texts through · v1
Arrow from Conversation Gateway to Twilio: C8 sends quizzes and hiring replies through · v3
Arrow from Twilio to Conversation Gateway: C9 forwards staff and applicant replies to · v3
Arrow from Voice provider to Conversation Gateway: C10 posts consented caller name, number and booking to · v3
Arrow from Explanation Service to LLM API: C11 sends flagged facts only to · v1
Arrow from Digest & Delivery Service to Platform Database: C12 reads explained flags; logs every digest sent to · v1
Arrow from Conversation Gateway to Platform Database: C13 stores replies, bookings and consent records in · v3
Arrow from Explanation Service to Platform Database: C14 reads top flags; writes explanations to · v1
Arrow from Rules & Baselines to Platform Database: C15 reads POS events; writes baselines and ranked flags to · v1
What this shows: Part 2 of 2. Insight out, plus the v3 conversation agents. Everything inside the boundary reads from and writes to one database. Element catalog: 12 boxes and 15 arrows, every one a row on artboard 05b·A.
Legend
v1 slice
later phase (v2, v3)
v1 call
later call

## Slide 9 — Containers part 2 catalog: every box and arrow on artboard 05b
05b·A Containers part 2 catalog

Full text of this artboard (arrows are written as "Arrow from X to Y"):

05b·A / 16 · APPENDIX · ELEMENT CATALOG FOR ARTBOARD 05b
Containers part 2 catalog: every box and arrow on artboard 05b
BOXES (12)
ID
Name
Type
Technology
Phase
Source
OWN
Owner
Person
Phone (SMS), email
v1
(R2 §2, §6)
STF
Staff
Person
Phone (SMS)
v1
(R2 §2)
APP
Applicants & callers
Person
SMS; phone
v3
(R2 §2)
EML
Email service
External: vendor TBD
TBD — not in sources
v1
(R2 §2)
TWL
Twilio
External: SMS API
SMS API; number + 10DLC campaign
v1
(R2 §3)
VOX
Voice provider
External: voice agent
Retell, Vapi or Bland
v3
(R2 §2)
LLM
LLM API
External: Anthropic API
Anthropic API, Haiku-class model
v1
(R2 §3)
DIG
Digest & Delivery Service
Container: Python job
Scheduled Python job (design choice)
v1
(R2 §2, §6)
GTW
Conversation Gateway
Container: Python web service
Python web service for SMS and voice webhooks (design choice)
v3
(R2 §2)
EXP
Explanation Service
Container: Python job
Python job calling the LLM API (design choice)
v1
(R2 §2)
RUL
Rules & Baselines
Container: Python job
Scheduled Python job; plain code, no model (design choice)
v1
(R2 §2, §10)
DB
Platform Database
Container: PostgreSQL
PostgreSQL, row-level tenant isolation (design choice)
v1
(Checked 2026-10-19)
ARROWS (15) · FROM → TO, VERB PHRASE, DATA, PROTOCOL
ID
From
To
Verb phrase
Data
Protocol
Phase
Source
C1
Email service
Owner
delivers digest emails to
Digest email
Email
v1
(R2 §2)
C2
Twilio
Owner
delivers digest texts to
Digest text
SMS
v1
(R2 §2, §3)
C3
Twilio
Staff
delivers SOP quizzes to
Quiz questions
SMS
v3
(R2 §2)
C4
Twilio
Applicants & callers
texts interview replies and slots to
Replies, interview slots
SMS
v3
(R2 §2)
C5
Applicants & callers
Voice provider
call the restaurant line answered by
Voice call
Phone
v3
(R2 §2)
C6
Digest & Delivery Service
Email service
sends digest emails through
Digest text, owner email
API TBD — not in sources
v1
(R2 §2)
C7
Digest & Delivery Service
Twilio
sends digest texts through
Digest text, owner number
HTTPS API
v1
(R2 §3)
C8
Conversation Gateway
Twilio
sends quizzes and hiring replies through
Quiz and reply text
HTTPS API
v3
(R2 §2)
C9
Twilio
Conversation Gateway
forwards staff and applicant replies to
Inbound SMS
Webhook (HTTPS)
v3
(R2 §2)
C10
Voice provider
Conversation Gateway
posts consented caller name, number and booking to
Name, number, booking, consent flag
Webhook; format TBD — not in sources
v3
(R2 §2)
C11
Explanation Service
LLM API
sends flagged facts only to
Top flags as facts; no full history
HTTPS API
v1
(R2 §2–3)
C12
Digest & Delivery Service
Platform Database
reads explained flags; logs every digest sent to
Explained flags; digest log
SQL over TLS
v1
(R2 §2, §6)
C13
Conversation Gateway
Platform Database
stores replies, bookings and consent records in
Quiz results, bookings, consent
SQL over TLS
v3
(R2 §2)
C14
Explanation Service
Platform Database
reads top flags; writes explanations to
Flags in; explanation text out
SQL over TLS
v1
(R2 §2)
C15
Rules & Baselines
Platform Database
reads POS events; writes baselines and ranked flags to
Events in; baselines, ranked flags out
SQL over TLS
v1
(R2 §2, §10)
Every box and arrow on artboard 05b is one row here, and every row is drawn there. “Design choice” items are settled in the ADRs on artboard 14.

## Slide 10 — The v1 slice: what ships first, in the accent colour
06 C4 L2 v1 slice

Full text of this artboard (arrows are written as "Arrow from X to Y"):

06 / 16 · C4 LEVEL 2 · CONTAINERS · THE V1 SLICE
The v1 slice: what ships first, in the accent colour
Later connectors
[Containers] · v2
Toast Connector and Labor Connector (05a).
Staff
[Person] · v1
Signs the acknowledgment.
Owner
[Person] · v1
Connects Square, gets the digest, decides.
Conversation agents
[Container + externals] · v3
Gateway, voice provider, applicants (05b).
Later external systems
[External] · v2
Toast POS and 7shifts (05a).
Owner Console
[Container: Python web app] · v1
OAuth connect, notice records, settings, CSV export.
Email service
[External: TBD] · v1
Delivers digest emails.
Twilio
[External: SMS] · v1
Sends digest texts.
LLM API
[External: Anthropic API] · v1
Haiku-class model.
Square POS
[External: Square] · v1
POS records via OAuth.
Square Connector
[Container: Python job] · v1
Only code that calls Square. Read-only.
Digest & Delivery Service
[Container: Python job] · v1
Fact-only digest, 2–3 times a week, owner only.
Explanation Service
[Container: Python job] · v1
Plain-English wording for top flags.
Rules & Baselines
[Container: Python job] · v1
Ratios, baselines and ranks per login and shift.
Platform Database
[Container: PostgreSQL] · v1
Tenant-scoped events, baselines, flags, digests, notices, audit log, encrypted tokens.
Arrow from Staff to Owner Console: V1 signs the monitoring-notice acknowledgment in (v1)
Arrow from Owner to Owner Console: V2 connects Square and keeps notice records in (v1)
Arrow from Owner Console to Square Connector: V3 hands the OAuth code to (v1)
Arrow from Square Connector to Square POS: V4 exchanges the code and refreshes tokens every 7 days or less with (v1)
Arrow from Square Connector to Square POS: V5 pulls orders, refunds and cash-drawer events from (v1)
Arrow from Owner Console to Platform Database: V6 writes settings, notices and encrypted tokens to (v1)
Arrow from Square Connector to Platform Database: V7 reads its token; writes POS events to (v1)
Arrow from Rules & Baselines to Platform Database: V8 reads events; writes baselines and ranked flags to (v1)
Arrow from Explanation Service to LLM API: V9 sends flagged facts only to (v1)
Arrow from Explanation Service to Platform Database: V10 reads top flags; writes explanations to (v1)
Arrow from Digest & Delivery Service to Platform Database: V11 reads explained flags; logs each digest to (v1)
Arrow from Digest & Delivery Service to Email service: V12 sends digest emails through (v1)
Arrow from Digest & Delivery Service to Twilio: V13 sends digest texts through (v1)
Arrow from Email service to Owner: V14 delivers digest emails to (v1)
Arrow from Twilio to Owner: V15 delivers digest texts to (v1)
What this shows: Only v1 is in the accent colour. The three grey boxes stand in for every later container and system (full detail on 05a and 05b). v1 reads Square through OAuth and creates only its own records. Every arrow here is v1. Element catalog: 15 boxes and 15 arrows, every one a row on artboard 06·A.
Legend
v1 slice
grey context, not in v1
v1 call

## Slide 11 — v1 slice catalog: the build list for the first release
06·A v1 slice catalog

Full text of this artboard (arrows are written as "Arrow from X to Y"):

06·A / 16 · APPENDIX · ELEMENT CATALOG FOR ARTBOARD 06 · THE V1 BUILD LIST
v1 slice catalog: the build list for the first release
BOXES (15)
ID
Name
Type
Technology
Phase
Source
G1
Later connectors
Containers
Grey context; see 05a·A
context
(R2 §2, §10)
STF
Staff
Person
Capture method TBD — not in sources
v1
(Checked 2026-10-19)
OWN
Owner
Person
Web browser, phone (SMS), email
v1
(R2 §2, §6)
G3
Conversation agents
Container + externals
Grey context; see 05b·A
context
(R2 §2)
G2
Later external systems
External
Grey context; see 05a·A
context
(R2 §2; Checked 2026-10-19)
CON
Owner Console
Container: Python web app
Python web app; owner-only sign-in (design choice)
v1
(Checked 2026-10-19; R2 §6)
EML
Email service
External: TBD
Vendor TBD — not in sources
v1
(R2 §2)
TWL
Twilio
External: SMS
SMS API; number + 10DLC campaign
v1
(R2 §3)
LLM
LLM API
External: Anthropic API
Anthropic API, Haiku-class model
v1
(R2 §3)
SQ
Square POS
External: Square
Square APIs via OAuth
v1
(R2 §2; Checked 2026-10-19)
SQC
Square Connector
Container: Python job
Scheduled Python job, nightly (design choice)
v1
(R2 §2; Checked 2026-10-19)
DIG
Digest & Delivery Service
Container: Python job
Scheduled Python job (design choice)
v1
(R2 §2, §6)
EXP
Explanation Service
Container: Python job
Python job calling the LLM API (design choice)
v1
(R2 §2)
RUL
Rules & Baselines
Container: Python job
Scheduled Python job; plain code, no model (design choice)
v1
(R2 §2, §10)
DB
Platform Database
Container: PostgreSQL
PostgreSQL, row-level tenant isolation (design choice)
v1
(Checked 2026-10-19; R2 §6)
ARROWS (15) · FROM → TO, VERB PHRASE, DATA, PROTOCOL
ID
From
To
Verb phrase
Data
Protocol
Phase
Source
V1
Staff
Owner Console
signs the monitoring-notice acknowledgment in
Signed acknowledgment, date
HTTPS; capture method TBD
v1
(Checked 2026-10-19)
V2
Owner
Owner Console
connects Square and keeps notice records in
Consent, notice records, export requests
HTTPS (browser)
v1
(Checked 2026-10-19; R2 §6)
V3
Owner Console
Square Connector
hands the OAuth code to
One-time authorization code
Internal HTTPS call
v1
(Checked 2026-10-19)
V4
Square Connector
Square POS
exchanges the code and refreshes tokens every 7 days or less with
Access and refresh tokens (30-day expiry)
OAuth over HTTPS
v1
(Checked 2026-10-19)
V5
Square Connector
Square POS
pulls orders, refunds and cash-drawer events from
Orders (CANCELED counted only), refunds, discounts; comps, drawer events: verify on live account
JSON over HTTPS; read-only scopes TBD
v1
(R2 §2; Checked 2026-10-19)
V6
Owner Console
Platform Database
writes settings, notices and encrypted tokens to
Settings, notices, AES-encrypted tokens
SQL over TLS
v1
(Checked 2026-10-19; R2 §6)
V7
Square Connector
Platform Database
reads its token; writes POS events to
Token in; normalized events out
SQL over TLS
v1
(R2 §2)
V8
Rules & Baselines
Platform Database
reads events; writes baselines and ranked flags to
Events in; baselines, ranked flags out
SQL over TLS
v1
(R2 §2, §10)
V9
Explanation Service
LLM API
sends flagged facts only to
Top flags as facts; no full history
HTTPS API
v1
(R2 §2–3)
V10
Explanation Service
Platform Database
reads top flags; writes explanations to
Flags in; explanation text out
SQL over TLS
v1
(R2 §2)
V11
Digest & Delivery Service
Platform Database
reads explained flags; logs each digest to
Explained flags; digest log
SQL over TLS
v1
(R2 §2, §6)
V12
Digest & Delivery Service
Email service
sends digest emails through
Digest text, owner email
API TBD — not in sources
v1
(R2 §2)
V13
Digest & Delivery Service
Twilio
sends digest texts through
Digest text, owner number
HTTPS API
v1
(R2 §3)
V14
Email service
Owner
delivers digest emails to
Digest email
Email
v1
(R2 §2)
V15
Twilio
Owner
delivers digest texts to
Digest text
SMS
v1
(R2 §2, §3)
Every box and arrow on artboard 06 is one row here. Same relationships as 05a and 05b: V1 = B2, V2 = B1, V3 = B3, V4 = B4, V5 = B5, V6 = B6, V7 = B7, V8 = C15, V9 = C11, V10 = C14, V11 = C12, V12 = C6, V13 = C7, V14 = C1, V15 = C2.

## Slide 12 — How v1 works: nightly POS pull, rules, baselines, ranking, explanation, digest
07 Dynamic view: v1 flow

Full text of this artboard (arrows are written as "Arrow from X to Y"):

07 / 16 · DYNAMIC VIEW · THE V1 FLOW, STEP BY STEP
How v1 works: nightly POS pull, rules, baselines, ranking, explanation, digest
Rules & Baselines [Container: Python job] · v1
Square POS
[External: Square APIs] · v1
Source of the night’s records.
Square Connector
[Container: Python job] · v1
Runs nightly; the only code that calls Square.
Ratio rules
[Component: Python] · v1
Counts and ratios per login and shift.
Baseline builder
[Component: Python] · v1
Each login’s own normal, per shift window.
Anomaly ranker
[Component: Python] · v1
Ranks the few biggest departures.
Platform Database
[Container: PostgreSQL] · v1
Events, baselines, ranked flags, explanations and the digest log, all tenant-scoped.
LLM API
[External: Anthropic API] · v1
Haiku-class model; gets facts, never full history.
Explanation Service
[Container: Python job] · v1
Asks for plain English for each top flag.
Digest & Delivery
[Container: Python job] · v1
Checks every number, then sends.
Twilio
[External: SMS API] · v1
Delivers the digest text.
Email service
[External: vendor TBD] · v1
Delivers the digest email.
Owner
[Person] · v1
Reads; decides what to do.
Arrow from Square Connector to Square POS: 1 refreshes the OAuth token if due, then pulls yesterday's orders, refunds and cash-drawer events from (v1)
Arrow from Square Connector to Platform Database: 2 writes events tagged with login and shift to (v1)
Arrow from Ratio rules to Platform Database: 3 reads the day's events from (v1)
Arrow from Ratio rules to Baseline builder: 4 hands ratios per login and shift to (v1)
Arrow from Baseline builder to Platform Database: 5 reads and updates each login's baseline in (v1)
Arrow from Baseline builder to Anomaly ranker: 6 hands departures from baseline to (v1)
Arrow from Anomaly ranker to Platform Database: 7 writes ranked flags with time-stamped evidence to (v1)
Arrow from Explanation Service to Platform Database: 8 reads the top flags, 2–3 times a week, from (v1)
Arrow from Explanation Service to LLM API: 9 sends only the facts of each top flag to (v1)
Arrow from Explanation Service to Digest & Delivery: 10 hands plain-English explanations to (v1)
Arrow from Digest & Delivery to Platform Database: 11 checks every number against the stored flag, then logs the digest in (v1)
Arrow from Digest & Delivery to Twilio: 12 sends the digest text through (v1)
Arrow from Digest & Delivery to Email service: 13 sends the digest email through (v1)
Arrow from Twilio to Owner: 14 delivers the text to (v1)
Arrow from Email service to Owner: 15 delivers email to (v1)
NIGHTLY · STEPS 1–7
2–3 TIMES A WEEK · STEPS 8–15 (R2 §2)
What the owner reads. Facts only, to the owner only (R2 §6). Target: “Login X voided $412 across 9 checks between 10:40 and 11:55 pm, approved by code Y.” On Square, the dollar amount, the login on voided orders and the approving code are verify on live account, so v1 starts with: “9 checks cancelled during shift Y (opened by login X).” (Checked 2026-10-19)
What this shows: Steps 1–7 are plain code and can be re-run without the model. Only step 9 uses the LLM. Step 11 rejects any number that is not in the stored flag (design choice, enforcing the facts-only rule in R2 §6). Every arrow here is v1. Element catalog: 12 boxes and 15 arrows, every one a row on artboard 07·A.
Legend
v1 slice
v1 call
verify on live account

## Slide 13 — v1 flow catalog: every box and numbered step on artboard 07
07·A v1 flow catalog

Full text of this artboard (arrows are written as "Arrow from X to Y"):

07·A / 16 · APPENDIX · ELEMENT CATALOG FOR ARTBOARD 07
v1 flow catalog: every box and numbered step on artboard 07
BOXES (12)
ID
Name
Type
Technology
Phase
Source
SQ
Square POS
External: Square APIs
Square APIs via OAuth
v1
(R2 §2; Checked 2026-10-19)
SQC
Square Connector
Container: Python job
Scheduled Python job (design choice)
v1
(R2 §2; Checked 2026-10-19)
RAT
Ratio rules
Component: Python
Plain code inside Rules & Baselines (design choice)
v1
(R2 §2)
BAS
Baseline builder
Component: Python
Plain code inside Rules & Baselines (design choice)
v1
(R2 §10)
RNK
Anomaly ranker
Component: Python
Plain code inside Rules & Baselines (design choice)
v1
(R2 §2, §10)
DB
Platform Database
Container: PostgreSQL
PostgreSQL, row-level tenant isolation (design choice)
v1
(Checked 2026-10-19)
LLM
LLM API
External: Anthropic API
Anthropic API, Haiku-class model
v1
(R2 §2–3)
EXP
Explanation Service
Container: Python job
Python job calling the LLM API (design choice)
v1
(R2 §2)
DIG
Digest & Delivery
Container: Python job
Scheduled Python job (design choice)
v1
(R2 §2, §6)
TWL
Twilio
External: SMS API
SMS API; number + 10DLC campaign
v1
(R2 §3)
EML
Email service
External: vendor TBD
TBD — not in sources
v1
(R2 §2)
OWN
Owner
Person
Phone (SMS), email
v1
(R2 §2, §6)
ARROWS (15) · FROM → TO, VERB PHRASE, DATA, PROTOCOL
ID
From
To
Verb phrase
Data
Protocol
Phase
Source
1
Square Connector
Square POS
refreshes the OAuth token if due, then pulls yesterday's orders, refunds and cash-drawer events from
Token refresh; orders (CANCELED counted only), refunds, discounts; comps, drawer events: verify on live account
OAuth + JSON over HTTPS
v1
(R2 §2; Checked 2026-10-19)
2
Square Connector
Platform Database
writes events tagged with login and shift to
Normalized events: login, shift, time, type, amount
SQL over TLS
v1
(R2 §10)
3
Ratio rules
Platform Database
reads the day's events from
Yesterday's events
SQL over TLS
v1
(R2 §2)
4
Ratio rules
Baseline builder
hands ratios per login and shift to
Cancelled-order, comp, discount, refund and no-sale counts; shares of net sales
In-process call
v1
(R2 §2, §6)
5
Baseline builder
Platform Database
reads and updates each login's baseline in
Baseline per login and shift window
SQL over TLS
v1
(R2 §10)
6
Baseline builder
Anomaly ranker
hands departures from baseline to
Departure from each login’s own baseline
In-process call
v1
(R2 §10)
7
Anomaly ranker
Platform Database
writes ranked flags with time-stamped evidence to
Ranked flags; check IDs and times as evidence
SQL over TLS
v1
(R2 §2)
8
Explanation Service
Platform Database
reads the top flags, 2–3 times a week, from
Top-ranked flags
SQL over TLS
v1
(R2 §2)
9
Explanation Service
LLM API
sends only the facts of each top flag to
Facts of each flag; login codes, no full history
HTTPS API
v1
(R2 §2–3)
10
Explanation Service
Digest & Delivery
hands plain-English explanations to
Explanation text per flag
Database row (design choice)
v1
(R2 §2)
11
Digest & Delivery
Platform Database
checks every number against the stored flag, then logs the digest in
Digest text; numbers re-checked against flags
SQL over TLS
v1
(R2 §6)
12
Digest & Delivery
Twilio
sends the digest text through
Digest text, owner number
HTTPS API
v1
(R2 §2–3)
13
Digest & Delivery
Email service
sends the digest email through
Digest email, owner address
API TBD — not in sources
v1
(R2 §2)
14
Twilio
Owner
delivers the text to
SMS
SMS
v1
(R2 §2)
15
Email service
Owner
delivers email to
Email
Email
v1
(R2 §2)
Every box and step on artboard 07 is one row here, and every row is drawn there. Step IDs are the numbers on the arrows. Steps 1–7 run nightly; steps 8–15 run 2–3 times a week.

## Slide 14 — Seven agents, one at a time: each recommends, the owner decides
08 Agent catalog

Full text of this artboard (arrows are written as "Arrow from X to Y"):

08 / 16 · AGENT CATALOG · THE 7 AGENTS IN R2 §2
Seven agents, one at a time: each recommends, the owner decides
No agent writes to the POS, payroll or schedules (R2 §5). Each is added only after the previous one proves itself (R2 §6, §10).
v1 · Agent 1
v2 · Agent 2
v3 · Agents 3–7
Agent
Problems
Input data
Output
Trigger
Phase
Recommends; owner decides · never does
Known gaps · cost
Source
1 · Comp-and-void monitor
4, 5, 6
Square orders (CANCELED counted only), comps, discounts, refunds, no-sale drawer opens, login, approving code. Comps, no-sale opens, login on voided orders and codes: verify on live account
Ranked digest per login and shift, with time-stamped evidence, by text and email
Nightly pull; digest 2–3 times a week
v1
Owner decides whether to talk to anyone. Never labels anyone a thief, alerts staff or changes the POS.
Square does not return voided items; it cannot show badge vs code. Lean run cost ~$20–25 a month.
(R2 §2, §3, §4, §6, §10; Checked 2026-10-19)
2 · Clock checker
7 (12 indirect)
Timecards and schedules from Square's Labor API or 7shifts
Missed punches, early clock-ins, overtime drift
TBD — not in sources
v2
Manager fixes timecards. Never edits payroll or timecards; no fingerprint clock (Labor Law §201-a).
Square Plus already blocks early clock-ins for $49 a month: a feature, not a product. 39% of payroll errors came from missed punches.
(R2 §2; Checked 2026-10-19)
3 · Phone and customer-data agent
10
Calls to the restaurant line, answered on Retell, Vapi or Bland
Reservations; caller name and number captured with consent
Each call
v3
Staff confirm bookings. Never the only way a guest can order; no recording without consent (Penal Law §250.05).
About $106–179 a month for 1,200 minutes. Competes with Yelp Host at $149 and Slang.ai at $399+ (vendor claim). Delivery apps will not share data.
(R2 §2, §4, §6)
4 · Inventory variance
11 (2 indirect)
Invoices, counts, recipes, item sales
Variance by item
TBD — not in sources
v3
Owner or chef investigates. Never adjusts stock or places orders.
Works only if someone keeps recipes and counts current. "Build later, if at all."
(R2 §2)
5 · Forecast
12
POS sales history
Busy-time forecast as staffing guidance
TBD — not in sources
v3
Guidance, not mandates; one-click override (R1 p.32). Never edits the schedule.
Low priority: Toast IQ Team and Square Shifts bundle forecasts; Lineup.ai $79 a location (vendor page). Sling calls 30–40% error "normal".
(R2 §2, §4; R1 p.32)
6 · SOP nudges
9, 14 (13 indirect)
The owner's own procedures
Two-minute SMS quizzes and a completion record
TBD — not in sources
v3
Owner writes and approves each procedure and quiz. Never used to discipline staff.
Incumbents fail on "no time": 62% of operators give 1–2 hours of training a week (vendor survey).
(R2 §2)
7 · Hiring scheduler
15
Applicant text messages
Fast replies and interview bookings
Each applicant message; reply within minutes
v3
Humans evaluate every candidate. Never scores or ranks anyone (NYC Local Law 144).
36% of applicants drop out from slow replies. Chipotle's agent cut time-to-hire from 12 days to 4.
(R2 §2)
WHAT EVERY AGENT REUSES
• Connectors that read the POS or labor tool, read-only (05a)
• Rules first, model second: code finds it, the model only explains it (R2 §2)
• One delivery path: text and email to the owner, never a dashboard or a staff chat (R2 §2, §6)
• Tenant isolation, owner-only access and the audit log (09b, 11)
WHERE R1'S 7 MODULES WENT (R1 pp.26–28)
• Loss Prevention → Agent 1 · Inventory and Food Cost → Agent 4 · Customer Data and CRM → Agent 3
• Staff Management → Agents 2 and 5, without biometric clock-in or phone-use logging (02, 03)
• Operations Core and Training → Agent 6 for SOPs; recipe and checklist apps not built
• Reporting Dashboard → replaced by the text and email digest (R2 §2)
"Trigger: TBD" means the sources give no cadence; artboard 15 sets each one when that agent is scheduled. Problem numbers follow the owner's list on artboard 02.
R1 = Oct 15 report · R2 = Oct 16 report · Checked = Oct 19, 2026

## Slide 15 — Data model, part 1: the tenant and the POS facts v1 reads
09a Domain data model part 1

Full text of this artboard (arrows are written as "Arrow from X to Y"):

09a / 16 · DOMAIN DATA MODEL · PART 1 OF 2 · TENANT AND POS FACTS
Data model, part 1: the tenant and the POS facts v1 reads
OAuth connection
[Entity] · v1
merchant_id, token (AES), expires_at, refreshed_at
Tenant
[Entity] · v1
tenant_id, restaurant name, plan, status
Shift
[Entity] · v1
shift_id, location, window start and end
Location
[Entity] · v1
location_id, square_location_id, time zone
Employee login
[Entity] · v1
login_id, square team member, display name
Manager approval code
[Entity] · v1 · verify on live account
code reference, holder login
Timecard
[Entity] · v2
clock in, clock out, login, shift
No-sale event
[Entity] · v1 · verify on live account
opened_at, login, location
Check
[Entity] · v1
order_id, opened by login, times, net total
Cancelled order
[Entity] · v1 · verify on live account
order_id, cancelled_at; counted only
Comp
[Entity] · v1 · verify on live account
line item at $0.00, reason
Line item
[Entity] · v1
item, quantity, price, check
Discount
[Entity] · v1
name, amount, applied to
Refund
[Entity] · v1
refund_id, amount, reason, time
Arrow from Tenant to OAuth connection: R1 holds 1 Square OAuth connection · v1
Arrow from Tenant to Location: R2 operates 1..* locations · v1
Arrow from Location to Shift: R3 defines 1..* shift windows · v1
Arrow from Location to Employee login: R4 is used by 1..* logins · v1
Arrow from Employee login to Manager approval code: R5 may hold 0..1 approval code · v1
Arrow from Shift to Timecard: R6 contains 0..* timecards · v2
Arrow from Location to No-sale event: R7 records 0..* no-sale drawer opens · v1
Arrow from Employee login to Check: R8 opens 0..* checks · v1
Arrow from Check to Cancelled order: R9 counts as 0..1 cancelled order · v1
Arrow from Check to Line item: R10 has 1..* line items · v1
Arrow from Line item to Discount: R11 may carry 0..* discounts · v1
Arrow from Line item to Comp: R12 may be comped at $0.00 · v1
Arrow from Line item to Refund: R13 may be refunded by 0..* · v1
What this shows: Split in two because the full model has more than 15 entities. Square calls a check an order. Dashed boxes hold records or fields the Square API may not return: verify on live account before the digest shows them. Element catalog: 14 boxes and 13 arrows, every one a row on artboard 09a·A.
Legend
v1 slice
later phase (v2, v3)
v1 call
later call
verify on live account

