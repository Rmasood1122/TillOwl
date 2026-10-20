# Restaurant Platform Architecture Pack — part 2 of 2 (Slides 16–30)

## Slide 16 — Data model part 1 catalog: every entity and relationship on artboard 09a
09a·A Data model part 1 catalog

Full text of this artboard (arrows are written as "Arrow from X to Y"):

09a·A / 16 · APPENDIX · ELEMENT CATALOG FOR ARTBOARD 09a
Data model part 1 catalog: every entity and relationship on artboard 09a
BOXES (14)
ID
Name
Type
Technology
Phase
Source
OAU
OAuth connection
Entity
PostgreSQL table; token encrypted with AES
v1
(Checked 2026-10-19)
TEN
Tenant
Entity
PostgreSQL table; every row everywhere carries tenant_id
v1
(R2 §2, §10)
SHF
Shift
Entity
PostgreSQL table; v1 windows set by owner, v2 from timecards (design choice)
v1
(R2 §10)
LOC
Location
Entity
PostgreSQL table
v1
(R2 §2)
EMP
Employee login
Entity
PostgreSQL table
v1
(R2 §2)
MAC
Manager approval code
Entity
PostgreSQL table; badge vs code unknown
v1
(R2 §4; verify on live account)
TMC
Timecard
Entity
PostgreSQL table; from Square Labor API or 7shifts
v2
(R2 §2)
NSE
No-sale event
Entity
PostgreSQL table; API availability unconfirmed
v1
(R2 §2; verify on live account)
CHK
Check
Entity
PostgreSQL table; Square order
v1
(R2 §2)
CXL
Cancelled order
Entity
PostgreSQL table; $ and login fields unconfirmed
v1
(Checked 2026-10-19; verify on live account)
CMP
Comp
Entity
PostgreSQL table; API exposure unconfirmed
v1
(Checked 2026-10-19; R2 §9; verify)
LIN
Line item
Entity
PostgreSQL table
v1
(R2 §2)
DSC
Discount
Entity
PostgreSQL table
v1
(R2 §2, §10)
REF
Refund
Entity
PostgreSQL table
v1
(R2 §2, §10)
ARROWS (13) · FROM → TO, VERB PHRASE, DATA, PROTOCOL
ID
From
To
Verb phrase
Data
Protocol
Phase
Source
R1
Tenant
OAuth connection
holds 1 Square OAuth connection
FK oauth_connection.tenant_id
Foreign key
v1
(Checked 2026-10-19)
R2
Tenant
Location
operates 1..* locations
FK location.tenant_id
Foreign key
v1
(R2 §2)
R3
Location
Shift
defines 1..* shift windows
FK shift.location_id
Foreign key
v1
(R2 §10)
R4
Location
Employee login
is used by 1..* logins
FK login.location_id
Foreign key
v1
(R2 §2)
R5
Employee login
Manager approval code
may hold 0..1 approval code
FK approval_code.login_id
Foreign key; verify on live account
v1
(R2 §4)
R6
Shift
Timecard
contains 0..* timecards
FK timecard.shift_id
Foreign key
v2
(R2 §2)
R7
Location
No-sale event
records 0..* no-sale drawer opens
FK no_sale.location_id
Foreign key; verify on live account
v1
(R2 §2)
R8
Employee login
Check
opens 0..* checks
FK check.opened_by_login
Foreign key
v1
(R2 §2)
R9
Check
Cancelled order
counts as 0..1 cancelled order
FK cancelled_order.order_id; state CANCELED
Foreign key
v1
(Checked 2026-10-19)
R10
Check
Line item
has 1..* line items
FK line_item.check_id
Foreign key
v1
(R2 §2)
R11
Line item
Discount
may carry 0..* discounts
FK discount.line_item_id
Foreign key
v1
(R2 §2)
R12
Line item
Comp
may be comped at $0.00
FK comp.line_item_id
Foreign key; verify on live account
v1
(Checked 2026-10-19)
R13
Line item
Refund
may be refunded by 0..*
FK refund.check_id
Foreign key
v1
(R2 §2)
Every entity and relationship on artboard 09a is one row here. Technology column lists the key fields. Every table also carries tenant_id. Cardinality is written into each verb phrase.

## Slide 17 — Data model, part 2: baselines, flags, digests and compliance records
09b Domain data model part 2

Full text of this artboard (arrows are written as "Arrow from X to Y"):

09b / 16 · DOMAIN DATA MODEL · PART 2 OF 2 · RECORDS THE PLATFORM CREATES
Data model, part 2: baselines, flags, digests and compliance records
Owner user
[Entity] · v1
user_id, email, phone; the only sign-in
Tenant
[Entity] · v1
Same as 09a; isolation key
Staff notice
[Entity] · v1
version, text, posted_at, given at hire
Audit log entry
[Entity] · v1
actor, action, target, time; append-only
Shift
[Entity] · v1
Same as 09a
Notice acknowledgment
[Entity] · v1
notice version, login, signed_at, method
Employee login
[Entity] · v1
Same as 09a
CSV export
[Entity] · v1
all flagged events; kept 30 days after end
Flag
[Entity] · v1
login, shift, metric, value, baseline, evidence
Baseline
[Entity] · v1
login, shift window, metric, normal range
Digest
[Entity] · v1
sent_at, channel, flag ids, text
Arrow from Tenant to Owner user: Q1 has 1 owner login (v1)
Arrow from Tenant to Staff notice: Q2 publishes 1..* notice versions (v1)
Arrow from Staff notice to Notice acknowledgment: Q3 is acknowledged in 0..* records (v1)
Arrow from Employee login to Notice acknowledgment: Q4 signs 1 per notice version (v1)
Arrow from Owner user to Audit log entry: Q5 has every sign-in, change and export written to (v1)
Arrow from Tenant to Shift: Q6 defines 1..* shift windows (v1)
Arrow from Shift to Flag: Q7 scopes 0..* flags (v1)
Arrow from Employee login to Baseline: Q8 has 1 baseline per shift window (v1)
Arrow from Baseline to Flag: Q9 sets the normal range that raises 0..* flags (v1)
Arrow from CSV export to Flag: Q10 copies every flag to CSV (v1)
Arrow from CSV export to Audit log entry: Q11 is logged in (v1)
Arrow from Digest to Flag: Q12 lists 1..* explained flags (v1)
Data rules that shape these tables
• v1 stores POS data and the records it creates; no camera, audio or biometric data (R2 §6)
• After termination or shutdown: CSV of all flagged events for 30 days, then deletion per contract (R2 §6)
• The restaurant’s data is never used for AI training (R2 §6)
• Retention periods beyond that: TBD — not in sources
What this shows: Part 2 of 2: the records v1 creates itself. Tenant, Shift and Employee login are the same entities as on 09a. Every table carries tenant_id, and the owner sees only their own tenant. Every arrow here is v1. Element catalog: 11 boxes and 12 arrows, every one a row on artboard 09b·A.
Legend
v1 slice
v1 call

## Slide 18 — Data model part 2 catalog: every entity and relationship on artboard 09b
09b·A Data model part 2 catalog

Full text of this artboard (arrows are written as "Arrow from X to Y"):

09b·A / 16 · APPENDIX · ELEMENT CATALOG FOR ARTBOARD 09b
Data model part 2 catalog: every entity and relationship on artboard 09b
BOXES (11)
ID
Name
Type
Technology
Phase
Source
OWU
Owner user
Entity
PostgreSQL table; owner-only access
v1
(R2 §6)
TEN
Tenant
Entity
PostgreSQL table
v1
(R2 §2, §10)
NOT
Staff notice
Entity
PostgreSQL table; §52-c*2 notice
v1
(Checked 2026-10-19)
AUD
Audit log entry
Entity
PostgreSQL table, append-only (design choice)
v1
(design choice)
SHF
Shift
Entity
PostgreSQL table
v1
(R2 §10)
ACK
Notice acknowledgment
Entity
PostgreSQL table; capture method TBD
v1
(Checked 2026-10-19)
EMP
Employee login
Entity
PostgreSQL table
v1
(R2 §2)
EXJ
CSV export
Entity
PostgreSQL table + file (design choice)
v1
(R2 §6)
FLG
Flag
Entity
PostgreSQL table
v1
(R2 §2, §6)
BAS
Baseline
Entity
PostgreSQL table
v1
(R2 §10)
DIG
Digest
Entity
PostgreSQL table
v1
(R2 §2, §6)
ARROWS (12) · FROM → TO, VERB PHRASE, DATA, PROTOCOL
ID
From
To
Verb phrase
Data
Protocol
Phase
Source
Q1
Tenant
Owner user
has 1 owner login
FK owner_user.tenant_id
Foreign key
v1
(R2 §6)
Q2
Tenant
Staff notice
publishes 1..* notice versions
FK staff_notice.tenant_id
Foreign key
v1
(Checked 2026-10-19)
Q3
Staff notice
Notice acknowledgment
is acknowledged in 0..* records
FK acknowledgment.notice_version
Foreign key
v1
(Checked 2026-10-19)
Q4
Employee login
Notice acknowledgment
signs 1 per notice version
FK acknowledgment.login_id
Foreign key
v1
(Checked 2026-10-19)
Q5
Owner user
Audit log entry
has every sign-in, change and export written to
FK audit.actor_id
Foreign key; insert-only
v1
(design choice)
Q6
Tenant
Shift
defines 1..* shift windows
FK shift.tenant_id
Foreign key
v1
(R2 §10)
Q7
Shift
Flag
scopes 0..* flags
FK flag.shift_id
Foreign key
v1
(R2 §2)
Q8
Employee login
Baseline
has 1 baseline per shift window
FK baseline.login_id
Foreign key
v1
(R2 §10)
Q9
Baseline
Flag
sets the normal range that raises 0..* flags
FK flag.baseline_id
Foreign key
v1
(R2 §2, §10)
Q10
CSV export
Flag
copies every flag to CSV
Export rows from flag
Batch query
v1
(R2 §6)
Q11
CSV export
Audit log entry
is logged in
FK audit.target_id
Foreign key
v1
(design choice)
Q12
Digest
Flag
lists 1..* explained flags
Join table digest_flag
Foreign key
v1
(R2 §2)
Every entity and relationship on artboard 09b is one row here. Technology column lists the key fields. The CSV export and its 30-day window come from the data-export clause in R2 §6.

## Slide 19 — Integrations: Square in v1, Toast in phase 2, then 7shifts and voice
10 Integration view

Full text of this artboard (arrows are written as "Arrow from X to Y"):

10 / 16 · INTEGRATION VIEW · EVERY OUTSIDE SYSTEM, HOW WE AUTHENTICATE, WHAT WE GET
Integrations: Square in v1, Toast in phase 2, then 7shifts and voice
Square Connector
[Container: Python job] · v1
Only code that calls Square.
Square POS
[External: Square APIs] · v1
Orders, refunds, discounts, labor.
Toast Connector
[Container: Python job] · v2
Phase 2 only.
Toast POS
[External: Toast API] · v2
Read-only standard access.
Labor Connector
[Container: Python job] · v2
Feeds Agent 2.
7shifts
[External: 7shifts API] · v2
Schedules and timecards.
Digest & Delivery
[Container: Python job] · v1
Sends the owner digest by text and by email.
Twilio
[External: SMS API] · v1
Texts the owner.
Email service
[External: vendor TBD] · v1
Emails the owner.
Explanation Service
[Container: Python job] · v1
Explains top flags.
LLM API
[External: Anthropic API] · v1
Haiku-class model.
Conversation Gateway
[Container: Python service] · v3
Receives call results.
Voice provider
[External: voice agent] · v3
Retell, Vapi or Bland.
Arrow from Square Connector to Square POS: I1 OAuth; refresh every 7 days or less; tokens AES-encrypted · v1
Arrow from Toast Connector to Toast POS: I2 paid portal, $50/month per US location; path TBD · v2
Arrow from Labor Connector to 7shifts: I3 admin-created token, no approval needed · v2
Arrow from Digest & Delivery to Twilio: I4 API credentials TBD; 10DLC-registered number · v1
Arrow from Digest & Delivery to Email service: I5 vendor and auth TBD — not in sources · v1
Arrow from Explanation Service to LLM API: I6 API key; flagged facts only · v1
Arrow from Voice provider to Conversation Gateway: I7 webhook into the gateway; auth TBD · v3
PLATFORM CONTAINER
AUTH METHOD (ON THE ARROW)
EXTERNAL SYSTEM
DATA AVAILABLE
KNOWN GAPS · TBD · VERIFY
Square POS, data available: Orders, including state CANCELED (counted only); refunds; discounts. Labor API for timecards in v2. Square hosts an MCP server in beta; v1 does not use it. (R2 §2; Checked 2026-10-19)
Square POS, known gaps: Voided items are not returned. verify on live account: comps, no-sale opens, $ and login on voided orders, approving code. Square cannot show badge vs code. (Checked 2026-10-19; R2 §4)
Toast POS, data available: Orders and checks for the restaurant’s own locations; Standard API access is read-only. (Checked 2026-10-19)
Toast POS, known gaps: Partner path and terms: TBD — not in sources. Self-serve API price unpublished (R2 §2). Order webhooks: R2 says none; Toast docs list webhook subscriptions — verify.
7shifts, data available: Timecards and schedules for Agent 2, the clock checker (R2 §2). Square’s Labor API is the alternative source.
7shifts, known gaps: Whether a vendor may use one admin token across many restaurants: unverified. 7shifts repriced twice in Sep–Oct 2026 (R2 §4).
Twilio, data available: Outbound SMS to the owner; inbound staff and applicant replies in v3. About $15 a month in the lean design: 1,000 segments + number + 10DLC campaign fee (R2 §3).
Twilio, known gaps: Credential type, 10DLC approval time and message limits: TBD — not in sources.
Email service, data available: Outbound digest email to the owner (R2 §2).
Email service, known gaps: Vendor, authentication and data terms: TBD — not in sources.
LLM API, data available: Only the facts of flagged anomalies. About $1 a month of tokens in the lean design: 8.1M in + 0.56M out at $0.10/$0.50 per million (R2 §3).
LLM API, known gaps: A vendor term that keeps restaurant data out of model training, as R2 §6 requires: TBD — not in sources.
Voice provider, data available: Caller name and number captured with consent; reservations. About $106–179 a month for 1,200 minutes (R2 §2).
Voice provider, known gaps: Mishears accents and menu names (competitor claim) (R2 §4). Recording calls without consent is a felony (R2 §6).
What this shows: Every integration is read-only toward the restaurant’s systems. Clover is not planned: it may need app approval and a 30% revenue share (R2 §2). Toast stays phase 2 until its access path is known. Element catalog: 13 boxes and 7 arrows, every one a row on artboard 10·A.
Legend
v1 slice
later phase (v2, v3)
v1 call
later call
verify on live account

## Slide 20 — Integration catalog: every box and arrow on artboard 10
10·A Integration catalog

Full text of this artboard (arrows are written as "Arrow from X to Y"):

10·A / 16 · APPENDIX · ELEMENT CATALOG FOR ARTBOARD 10
Integration catalog: every box and arrow on artboard 10
BOXES (13)
ID
Name
Type
Technology
Phase
Source
SQC
Square Connector
Container: Python job
Scheduled Python job (design choice)
v1
(R2 §2; Checked 2026-10-19)
SQ
Square POS
External: Square APIs
Square APIs via OAuth
v1
(R2 §2; Checked 2026-10-19)
TSC
Toast Connector
Container: Python job
Scheduled Python job (design choice)
v2
(R2 §10)
TST
Toast POS
External: Toast API
Toast API; $50/mo portal
v2
(Checked 2026-10-19)
LBC
Labor Connector
Container: Python job
Scheduled Python job (design choice)
v2
(R2 §2)
SHF
7shifts
External: 7shifts API
7shifts API; admin-created token
v2
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
EXP
Explanation Service
Container: Python job
Python job calling the LLM API (design choice)
v1
(R2 §2)
LLM
LLM API
External: Anthropic API
Anthropic API, Haiku-class model
v1
(R2 §3)
GTW
Conversation Gateway
Container: Python service
Python web service for webhooks (design choice)
v3
(R2 §2)
VOX
Voice provider
External: voice agent
Retell, Vapi or Bland
v3
(R2 §2)
ARROWS (7) · FROM → TO, VERB PHRASE, DATA, PROTOCOL
ID
From
To
Verb phrase
Data
Protocol
Phase
Source
I1
Square Connector
Square POS
OAuth; refresh every 7 days or less; tokens AES-encrypted
Orders (CANCELED counted only), refunds, discounts
OAuth + JSON over HTTPS; read-only scopes TBD
v1
(Checked 2026-10-19)
I2
Toast Connector
Toast POS
paid portal, $50/month per US location; path TBD
Orders and checks
HTTPS; access path TBD — not in sources
v2
(Checked 2026-10-19)
I3
Labor Connector
7shifts
admin-created token, no approval needed
Timecards, schedules
HTTPS; admin token
v2
(R2 §2)
I4
Digest & Delivery
Twilio
API credentials TBD; 10DLC-registered number
Digest text, owner number
HTTPS API; credential type TBD
v1
(R2 §3)
I5
Digest & Delivery
Email service
vendor and auth TBD — not in sources
Digest email, owner address
API TBD — not in sources
v1
(R2 §2)
I6
Explanation Service
LLM API
API key; flagged facts only
Facts of top flags; no full history
HTTPS API
v1
(R2 §2–3)
I7
Voice provider
Conversation Gateway
webhook into the gateway; auth TBD
Caller name, number, booking, consent flag
Webhook; format and auth TBD
v3
(R2 §2)
Every box and arrow on artboard 10 is one row here, and every row is drawn there. The data-available and known-gap columns on artboard 10 are text, not diagram elements.

## Slide 21 — Security and NY compliance: what v1 builds in before it reads one check
11 Security, privacy and NY compliance

Full text of this artboard (arrows are written as "Arrow from X to Y"):

11 / 16 · SECURITY, PRIVACY AND NEW YORK COMPLIANCE
Security and NY compliance: what v1 builds in before it reads one check
Legal compliance is a hard constraint. Where a law's reach is unclear, v1 takes the cautious path and says so.
Control
What we build
Why · the rule behind it
Phase
Source
Tenant isolation
Every table carries tenant_id; database row-level security; every query scoped to one tenant; automated tests try to read across tenants.
One owner's sales and staff data must never reach another owner.
v1
(design choice)
Encrypted OAuth tokens
AES-encrypted at rest; key held in the host's secret store, never in code or the database; refreshed every 7 days or less.
Partner apps must use OAuth, never a seller's personal access token. Personal tokens only on our own test account.
v1
(Checked 2026-10-19)
Owner-only access
One owner sign-in per restaurant with two-factor (design choice); no staff accounts; the digest goes to the owner only.
"Never send alerts to a staff group chat."
v1
(R2 §6)
Audit log
Append-only record of every sign-in, setting change, export, digest sent and notice recorded.
Shows who saw what, and when, if a decision is challenged.
v1
(design choice)
Staff notice and acknowledgment
The workflow on the right. A login enters the digest only after its acknowledgment is on file (design choice).
NY Civil Rights Law §52-c*2: notice at hire, acknowledgment, posted notice. AG penalties up to $500, $1,000, then $3,000 per offense.
v1
(Checked 2026-10-19)
v1 reads POS data only
No cameras, audio, biometrics, location or phone-use data in v1.
No one may be required to be fingerprinted (Labor Law §201-a); NYC biometric signage; no video in restrooms (§203-c); recording without consent is a felony (§250.05).
v1
(R2 §6; Checked 2026-10-19)
Fact-based wording
Fixed templates: counts, times, logins, codes. Never "thief", never a wage deduction, never the only basis for a firing.
A false theft accusation is defamation per se in NY; Labor Law §193 forbids deducting losses from wages.
v1
(R2 §1, §6)
Least data to vendors
The LLM gets only the facts of flagged anomalies; SMS and email carry only the digest.
Rules first, model second keeps raw history in-house.
v1
(R2 §2)
Exit rights
30-day CSV export of all flagged events after termination, and the same if we shut down; deletion per contract.
The standard SaaS contract (Common Paper CSA v2.1) gives deletion within 60 days but no export right.
v1
(R2 §6)
No AI training
The restaurant's data is never used to train a model. Matching vendor terms: TBD — not in sources.
Written into the contract as a promise to the owner.
v1
(R2 §6)
Month-to-month, one-click cancel
Monthly billing; cancel in one click; no hidden per-feature fees.
GOL §5-903 does not apply to renewal periods of one month or less; GBL §527-a covers personal purchases only.
v1
(R2 §6)
Hiring agent limits
Agent 7 replies and books interviews only; it never scores candidates.
Scoring triggers NYC's hiring bias-audit law, Local Law 144.
v3
(R2 §2)
§52-c*2 NOTICE WORKFLOW · V1
1
Owner records the notice text, with a version number, in the console.
2
Each employee gets the written notice at hire. Current staff get it before monitoring starts (design choice).
3
Each employee acknowledges it; the platform stores who, which version, when and how. Capture method: TBD — not in sources.
4
Owner posts the notice where staff can see it and records the date.
5
A login appears in the digest only once its acknowledgment is on file.
6
Owner tells staff that nobody is punished just for data showing up, the only documented staff-adoption tactic in food service (R2 §6).
Notice at hire, acknowledgment and posted notice (Checked 2026-10-19)
NOT CONFIRMED
Whether reading POS logs counts as monitoring under §52-c*2 (R2 §9). We give the notice anyway; it costs one page (R2 §6).
Have NY employment counsel review the notice and digest templates before the pilot: TBD — not in sources.
WHO SEES WHAT IN V1 (design choice)
Owner: digests, flags with evidence, notice records, CSV export.
Staff: the notice and their own acknowledgment; no flags.
Us (vendor): support access only when the owner allows it, and every access is in the audit log.
This page states rules from the sources; it is not legal advice. "Design choice" items are decided in the ADRs on artboard 14.
R1 = Oct 15 report · R2 = Oct 16 report · Checked = Oct 19, 2026

## Slide 22 — Deployment: v1 on one shared host, and what each restaurant costs to run
12 Deployment and cost per restaurant

Full text of this artboard (arrows are written as "Arrow from X to Y"):

12 / 16 · DEPLOYMENT VIEW AND COST PER RESTAURANT
Deployment: v1 on one shared host, and what each restaurant costs to run
Render, shared hosting [Deployment node] · lean design, ~$5 a month (R2 §3) · later agents deploy here as more jobs
Owner devices
[Device] · v1
Signs in; gets texts and email.
Square POS
[External: Square APIs] · v1
Read over OAuth.
Later integrations
[External] · v2, v3
Toast, 7shifts, voice provider.
LLM API
[External: Anthropic API] · v1
Haiku-class model.
Twilio
[External: SMS API] · v1
Texts the owner.
Email service
[External: vendor TBD] · v1
Emails the owner.
Owner Console
[Web service on Render] · v1
Owner-only sign-in.
Square Connector
[Cron job on Render] · v1
Nightly; key from host secrets.
Rules & Baselines
[Cron job on Render] · v1
Nightly; plain code.
Explanation Service
[Cron job on Render] · v1
2–3 times a week.
Digest & Delivery
[Cron job on Render] · v1
2–3 times a week; sends by text and by email.
PostgreSQL
[Managed database; cost TBD — not in sources] · v1
Tenant-scoped tables; OAuth tokens AES-encrypted with a key held in the host’s secret store.
Arrow from Owner devices to Owner Console: D1 signs in over HTTPS to (v1)
Arrow from Square Connector to Square POS: D2 pulls nightly over OAuth from (v1)
Arrow from Explanation Service to LLM API: D3 sends flagged facts to (v1)
Arrow from Digest & Delivery to Twilio: D4 sends SMS through (v1)
Arrow from Digest & Delivery to Email service: D5 sends email through (v1)
Arrow from Owner Console to PostgreSQL: D6 writes settings, notices, tokens to (v1)
Arrow from Square Connector to PostgreSQL: D7 writes events to (v1)
Arrow from Rules & Baselines to PostgreSQL: D8 reads events; writes flags to (v1)
Arrow from Explanation Service to PostgreSQL: D9 reads flags; writes text to (v1)
Arrow from Digest & Delivery to PostgreSQL: D10 reads flags; logs each digest to (v1)
COST PER RESTAURANT PER MONTH · OCTOBER 2026 LIST PRICES · EXCLUDES YOUR TIME, SUPPORT, SALES AND ANY CAMERA (R2 §3)
Design
Monthly
Arithmetic (as R2 gives it)
Sources
Lean · Square, Haiku-class model, SMS digest, shared hosting · v1
~$20–25
AI tokens ~$1 (8.1M in + 0.56M out at $0.10/$0.50 per million) + SMS ~$15 (1,000 segments + number + 10DLC campaign fee) + hosting ~$5 + Square API $0
Anthropic, Twilio, Render (R2 §3)
Typical · Toast, Sonnet-class model, 1,200 voice minutes
~$275
AI ~$22 + Toast portal $50 + voice ~$179 (1,200 min at ~$0.149/min) + SMS ~$18 + hosting ~$5
Retell, MarginEdge on Toast (R2 §3)
Heavy · multi-step agent loops, 3,000 voice minutes, own server
~$670
AI ~$110 (5x tokens) + voice ~$450 + hosting $33 + Toast $50 + SMS ~$25
same as above, Vapi (R2 §3)
Price check: the target price is $79–99 a month (R2 §3), under $100, month-to-month (R2 §10). Only the lean design fits under that price. Typical and heavy cost more than the price, so voice and Toast need their own pricing: TBD — not in sources. Database hosting cost is not broken out in R2: TBD — not in sources.
What this shows: If this node is down, the restaurant runs normally: nothing here sits in the order or payment path. A missed night is re-pulled the next night (design choice). Every arrow here is v1. Element catalog: 12 boxes and 10 arrows, every one a row on artboard 12·A.
Legend
v1 slice
grey context, not in v1
v1 call

## Slide 23 — Deployment catalog: every box and arrow on artboard 12
12·A Deployment catalog

Full text of this artboard (arrows are written as "Arrow from X to Y"):

12·A / 16 · APPENDIX · ELEMENT CATALOG FOR ARTBOARD 12
Deployment catalog: every box and arrow on artboard 12
BOXES (12)
ID
Name
Type
Technology
Phase
Source
DEV
Owner devices
Device
Any phone and browser
v1
(R2 §2)
SQ
Square POS
External: Square APIs
Square APIs
v1
(R2 §2; Checked 2026-10-19)
LTR
Later integrations
External
Grey context; see 10
context
(R2 §2, §10)
LLM
LLM API
External: Anthropic API
Anthropic API
v1
(R2 §3)
TWL
Twilio
External: SMS API
SMS API; 10DLC number
v1
(R2 §3)
EML
Email service
External: vendor TBD
TBD — not in sources
v1
(R2 §2)
CON
Owner Console
Web service on Render
Python web app (design choice)
v1
(R2 §3, §6)
SQC
Square Connector
Cron job on Render
Python job (design choice)
v1
(R2 §3; Checked 2026-10-19)
RUL
Rules & Baselines
Cron job on Render
Python job (design choice)
v1
(R2 §2, §3)
EXP
Explanation Service
Cron job on Render
Python job (design choice)
v1
(R2 §2, §3)
DIG
Digest & Delivery
Cron job on Render
Python job (design choice)
v1
(R2 §2, §3)
DB
PostgreSQL
Managed database; cost TBD — not in sources
Managed PostgreSQL (design choice)
v1
(Checked 2026-10-19)
ARROWS (10) · FROM → TO, VERB PHRASE, DATA, PROTOCOL
ID
From
To
Verb phrase
Data
Protocol
Phase
Source
D1
Owner devices
Owner Console
signs in over HTTPS to
Owner session
HTTPS
v1
(R2 §6)
D2
Square Connector
Square POS
pulls nightly over OAuth from
Orders, refunds, discounts
OAuth + JSON over HTTPS
v1
(Checked 2026-10-19)
D3
Explanation Service
LLM API
sends flagged facts to
Facts of top flags
HTTPS API
v1
(R2 §2–3)
D4
Digest & Delivery
Twilio
sends SMS through
Digest text
HTTPS API
v1
(R2 §3)
D5
Digest & Delivery
Email service
sends email through
Digest email
API TBD
v1
(R2 §2)
D6
Owner Console
PostgreSQL
writes settings, notices, tokens to
Settings, notices, encrypted tokens
SQL over TLS
v1
(Checked 2026-10-19)
D7
Square Connector
PostgreSQL
writes events to
Normalized events
SQL over TLS
v1
(R2 §2)
D8
Rules & Baselines
PostgreSQL
reads events; writes flags to
Events in; flags out
SQL over TLS
v1
(R2 §2)
D9
Explanation Service
PostgreSQL
reads flags; writes text to
Flags in; explanations out
SQL over TLS
v1
(R2 §2)
D10
Digest & Delivery
PostgreSQL
reads flags; logs each digest to
Explained flags; digest log
SQL over TLS
v1
(R2 §6)
Every box and arrow on artboard 12 is one row here. The cost table on artboard 12 is text, not a diagram element. Hosting provider named in the sources: Render (R2 §3).

## Slide 24 — Quality scenarios: the five tests v1 must pass before the pilot
13 Quality attribute scenarios

Full text of this artboard (arrows are written as "Arrow from X to Y"):

13 / 16 · QUALITY ATTRIBUTE SCENARIOS · ARC42 §10 STYLE · TOP 5, IN PRIORITY ORDER
Quality scenarios: the five tests v1 must pass before the pilot
Each one is written so a developer can turn it into a test and an owner can see why it matters. Measures marked “design choice” are targets we set; the sources do not give them.
Quality attribute
Source
Stimulus
Environment · artifact
Response
Response measure
Source tag
1Stays off the service path
Hosting outage, bug or bad deploy
The platform is down during Friday dinner service
Peak service · whole platform
The restaurant takes orders and payments as normal. The next nightly run pulls the missed day.
Zero order or payment interruptions caused by the platform. Missed day recovered on the next run (design choice).
(R1 p.32; R2 §5)
2Facts only
The LLM
An explanation contains a number, time or name that is not in the stored flag
Digest build · Digest & Delivery
The sentence is dropped and the plain template fact line is sent instead. Nothing calls anyone a thief.
100% of numbers in every digest trace to stored flag rows; automated check on every run (design choice).
(R2 §2, §6)
3Tenant isolation and owner-only access
A bug, or a signed-in user probing
A request for another restaurant’s flags, or a staff member trying to sign in
Normal operation · database and console
Row-level security returns nothing; staff have no accounts; the attempt goes in the audit log.
Zero cross-tenant rows in the isolation tests run on every release; every access logged (design choice).
(R2 §6; design choice)
4Square connection keeps working
Square OAuth
A token nears its 30-day expiry, or a refresh fails
Nightly run · Square Connector
The token is refreshed every 7 days or less. If refresh fails, the owner gets one text asking them to reconnect.
No gap longer than one night from an expired token (design choice). Refresh interval of 7 days or less.
(Checked 2026-10-19)
5Cheap per restaurant
Growth
A new restaurant is added
Lean design · shared stack
It runs on the shared host, Haiku-class model and SMS digest with no new infrastructure.
Run cost about $20–25 a month per restaurant, AI tokens about $1, against a $79–99 price.
(R2 §3)
WHY THIS ORDER
A failure during service “burned the trust” in a real operator’s system (R1 p.25). A false accusation is a defamation risk in New York (R2 §6). Both are worse than a missed digest, so they come first.
MEASURED ON THE PILOT INSTEAD (ARTBOARD 15)
Usefulness to the owner: the pilot fails if the owner stops opening the digest (R2 §6). A target reading time for the digest: TBD — not in sources.
Scenarios 1–4 become automated tests in the v1 build. Scenario 5 is checked on each month’s bill.
R1 = Oct 15 report · R2 = Oct 16 report · Checked = Oct 19, 2026

## Slide 25 — Eight decisions that shape v1, and what each one costs us
14 Architecture decision records

Full text of this artboard (arrows are written as "Arrow from X to Y"):

14 / 16 · ARCHITECTURE DECISION RECORDS · NYGARD FORMAT
Eight decisions that shape v1, and what each one costs us
Accepted
Proposed
ADR-001 · One narrow agent, not the platform
Accepted
Context: R1 designs a 7-module platform launching with 3 modules. R2 finds Toast and Square already bundle most of the list, and the one missing product with peer-reviewed payback is a POS-data monitor.
Decision: We will build Agent 1 only for v1 and add agents one at a time, each after the previous one passes.
Consequences: + Small, testable, cheap; proof in dollars. − 12 of the owner’s 15 problems wait; the pitch is narrow.
Source: R2 §1, §6, §10; R1 pp.26–33
ADR-002 · Rules first, LLM second
Accepted
Context: AI tokens cost about $1 a month per restaurant in the lean design, and anomaly logic must be auditable.
Decision: We will compute void, comp, discount and refund ratios and per-login baselines in plain code, and send only flagged anomalies to a small model for plain-English explanation.
Consequences: + Cheap, testable, explainable. − Each new anomaly type needs a new rule. − The LLM sees only flagged events, never full history.
Source: R2 §2–3
ADR-003 · Square first through OAuth; Toast in phase 2
Accepted
Context: Partner apps must use OAuth, not a seller’s personal token; tokens expire every 30 days. Toast integrations need a $50/month portal and a partner path not in the sources.
Decision: We will connect Square through OAuth, pilot included, refresh every 7 days or less, encrypt tokens with AES, and defer Toast.
Consequences: + No fee to the restaurant. − Toast restaurants, about 180,000 locations, wait. − Square app approval is unconfirmed.
Source: Checked 2026-10-19; R2 §1–3, §10
ADR-004 · Count cancelled orders; gate unconfirmed fields
Accepted
Context: Square’s Orders API does not return voided items; voided orders come back CANCELED without line items. Comp detail is not confirmed.
Decision: We will count cancelled orders only, and show void dollars, logins on voided orders, item voids, approving codes, comps and no-sale opens only after a live-account test passes.
Consequences: + No promise the data cannot keep. − The target digest sentence cannot ship on day one; the signal is weaker.
Source: Checked 2026-10-19; R2 §2, §9
ADR-005 · Text and email digest, not a dashboard
Accepted
Context: R1 specifies a dashboard, a Monday summary and up to 3 alerts a day. R2: median products see only 37% of users return after week one.
Decision: We will send one ranked digest 2–3 times a week by text and email, to the owner only.
Consequences: + Meets the owner where they already are. − No drill-down screen; detail comes as a CSV export. − SMS costs scale with message length.
Source: R2 §2–3, §6; R1 pp.28, 31
ADR-006 · Facts only, owner only, notice first
Accepted
Context: A false theft accusation is defamation per se in New York. §52-c*2 requires notice, acknowledgment and posting; whether POS logs count is unconfirmed.
Decision: We will use fixed fact templates, deliver to the owner only, and include a login only after its acknowledgment is on file.
Consequences: + Legally cautious and easy to defend. − Staff paperwork before day one; baselines start later.
Source: R2 §6, §9; Checked 2026-10-19
ADR-007 · Python and PostgreSQL on one shared host
Proposed
Context: The lean design assumes about $5 a month of shared hosting. Tenants must be isolated and tokens encrypted.
Decision: We will run the console and nightly jobs in Python on one Render host, with PostgreSQL row-level security and the AES key held in the host’s secret store.
Consequences: + Cheap and simple; one place to secure. − No high availability, acceptable because v1 is off the service path. − Database cost not in sources.
Source: R2 §3; Checked 2026-10-19; design choice
ADR-008 · No cameras, audio or biometrics; agents never act
Accepted
Context: R1 Module 3 wants biometric clock-in and phone-use logging. NY bars required fingerprinting; NYC requires biometric signage; AI that takes control gets pulled.
Decision: We will exclude cameras, audio and biometrics, and no agent will write to the POS, payroll or schedules.
Consequences: + Legally clean; no hardware. − Plate-level portioning and phone use stay unsolved by software.
Source: R2 §2, §5, §6; Checked 2026-10-19; R1 p.27
“Design choice” items across this pack (Python, PostgreSQL, the acknowledgment gate, two-factor sign-in) trace to these ADRs. ADR-007 stays Proposed until database cost is known.
R1 = Oct 15 report · R2 = Oct 16 report · Checked = Oct 19, 2026

## Slide 26 — Roadmap: prove v1 in dollars, then add one agent at a time
15 Roadmap and pilot pass line

Full text of this artboard (arrows are written as "Arrow from X to Y"):

15 / 16 · PHASED ROADMAP · V1 → V2 → V3 · PILOT PASS LINE
Roadmap: prove v1 in dollars, then add one agent at a time
PILOT PASS LINE · WRITTEN DOWN BEFORE DAY ONE
Measure voids + comps + discounts as a percent of net sales (sales after refunds), for 30 days before and 60 days after (R2 §6).
PASS: a drop of at least 1 point
On $1M of revenue that is $10,000 a year, against a $1,200 price (R2 §6).
FAIL: under 0.5 point
Or the owner stops opening the digest (R2 §6). Between 0.5 and 1 point: TBD — not in sources; agree it before day one.
Square caveat
Void dollars on Square are verify on live account. If they are missing, the owner and we agree a substitute measure before day one: TBD.
BEFORE DAY ONE
Set up the pilot
• Written Design Partner Agreement; charge 10–20% of the intended annual price up front (R2 §6)
• Pass line above, signed by both sides (R2 §6)
• §52-c*2 notices given, acknowledged and posted (Checked 2026-10-19)
• Square connected through OAuth, not a personal token (Checked 2026-10-19)
• Every “verify on live account” item tested on the friend’s account (artboard 16d)
• 30 days of pre-pilot history pulled: availability is a verify item
V1 · FIXED 90-DAY TERM
Agent 1 on Square
• Digest 2–3 times a week, to the owner only (R2 §2)
• Weekly 30-minute check-in; ends “go paid or don’t” (R2 §6)
• Then under $100 a month, $79–99, month-to-month, one-click cancel (R2 §3, §6, §10)
• Get the friend’s name on a one-paragraph result (R2 §6)
Gate to v2: the pilot passes, and a referral counts only after a second owner has paid for 60 days (R2 §10).
V2
Agent 2 and the Toast connector
• Clock checker on Square’s Labor API or 7shifts (R2 §2). Square Plus already blocks early clock-ins for $49 a month, so sell it as a feature (R2 §2)
• Toast only once the partner path is known and the price covers the $50/month portal (Checked 2026-10-19)
Gate to v3: a pass measure for v2: TBD — not in sources.
V3 · ONE AGENT AT A TIME
Agents 3 to 7
• Agent 7 hiring scheduler: replies and booking only, never scoring (R2 §2)
• Agent 6 SOP nudges (R2 §2)
• Agent 3 voice: needs its own price; about $106–179 a month in minutes alone (R2 §2)
• Agent 4 only if recipes and counts stay current; Agent 5 last, low priority (R2 §2)
Order within v3 is a design choice: cheapest and best-evidenced first.
GROWTH, HONESTLY
Referrals: a free month to both sides after the referred owner has paid for 60 days. The NYC Hospitality Alliance costs $365 a year for one unit and runs owner roundtables (R2 §6).
AI search: rank for one narrow phrase, get named by third parties, publish real pilot data, and measure appearance rate over at least 50 runs. Nobody can promise “#1” (R2 §7, §10).
Calendar dates for v2 and v3: TBD — not in sources. Each phase starts only when the one before it passes its gate.
R1 = Oct 15 report · R2 = Oct 16 report · Checked = Oct 19, 2026

## Slide 27 — Where the two reports disagree, and which one this pack follows
16a Known R1 and R2 conflicts

Full text of this artboard (arrows are written as "Arrow from X to Y"):

16a / 16 · RISKS AND REGISTERS · PART A OF D · KNOWN R1 ↔ R2 CONFLICTS
Where the two reports disagree, and which one this pack follows
R2 (Oct 16) is the decision baseline. Checked facts (Oct 19) override both. 16 is split into four parts, 16a to 16d, to keep every line at 14px or larger.
ID
Topic
R1 says
R2 or the checked facts say
This pack follows
Sources
CONFLICTS
K1
Product shape
A 7-module all-in-one platform, launching with 3 modules
Do not build the all-in-one; build one narrow agent
R2: Agent 1 first (ADR-001)
R1 pp.26–33 · R2 §10
K2
First POS
Start with Toast, used by 120,000+ U.S. restaurants (Risk 1)
Start on Square; Toast is phase 2
R2, through OAuth (ADR-003)
R1 p.31 · R2 §10
K3
Price
$149–$199/month; the “sweet spot” is $100–$200/month
Under $100 a month; $79–99 leaves room
R2
R1 p.29, p.25 · R2 §3, §10
K4
POS integration cost
Toast, Square, Lightspeed, Clover integration “included in base price”
Toast’s portal costs $50/month per US location; its self-serve API price is unpublished
R2 and the checked fact
R1 p.29 · R2 §2–3 · Checked 2026-10-19
K5
Owner output
Dashboard; weekly summary every Monday; maximum 3 priority alerts a day
Text and email digest 2–3 times a week, not a dashboard
R2 (ADR-005)
R1 pp.28, 31 · R2 §2
K6
Clocks and phones
Biometric or photo clock-in; $150–$250 clock hardware; the app logs phone use
No one may be required to be fingerprinted (§201-a); NYC biometric signage; phone use cannot be solved without cameras
R2 and the checked fact (ADR-008)
R1 p.27, p.29 · R2 §2, §6 · Checked 2026-10-19
K7
Margins
“Margins are only 3–5%”
Median full-service profit was 2.8% of sales in 2024
R2
R1 p.7 · R2 §1
K8
What round one concluded
Concludes the unified platform is the answer
R2 §1 says round one’s call was “do not build the all-in-one”
Recorded: R2’s summary of R1 is inaccurate; R2 is the baseline anyway
R1 pp.32–33 · R2 §1
SUPERSEDED FIGURES (NOT DISAGREEMENTS)
S1
Toast’s size
About 120,000 U.S. restaurants (June 2024)
About 180,000 locations (June 2026)
R2’s newer figure
R1 p.23 · R2 §1
S2
Unprofitable operators
38% not profitable “the prior year”, year not stated
42% not profitable in 2025
R2’s newer figure
R1 p.1 · R2 §1
R2 OVERRIDDEN BY CHECKED FACTS
O1
Square access
Not addressed
R2: a personal access token is “suitable for production use”. Checked: partner apps must not use one; multi-tenant apps use OAuth
OAuth everywhere, pilot included; personal token only on our test account
R2 §2, §10 · Checked 2026-10-19
O2
Voids
POS anomaly detection on “unusual voids”
R2: monitor voids. Checked: voided items are not in the Orders API; count cancelled orders only
Cancelled-order counts only (ADR-004)
R1 p.27 · R2 §2, §10 · Checked 2026-10-19
Next: 16b new conflicts found while building this pack · 16c risks and technical debt · 16d not confirmed, verify on live account, TBD.
R1 = Oct 15 report · R2 = Oct 16 report · Checked = Oct 19, 2026

## Slide 28 — Fourteen more conflicts the reports do not flag themselves
16b New conflicts found

Full text of this artboard (arrows are written as "Arrow from X to Y"):

16b / 16 · RISKS AND REGISTERS · PART B OF D · NEW CONFLICTS FOUND WHILE BUILDING THIS PACK
Fourteen more conflicts the reports do not flag themselves
Rows marked “High impact” (dark bar) change what gets built or measured. The rest change which numbers this pack is willing to use.
ID
Where
The conflict
Effect on this pack
Sources
N13
R2 vs checked
High impact
The pilot pass line uses voids as a percent of net sales, but void dollars on Square are not confirmed
Agree a substitute measure before day one (15)
R2 §6 · Checked 2026-10-19
N14
R2 internal
High impact
Typical (~$275) and heavy (~$670) run costs are far above the $79–99 price; R2 does not reconcile them
Voice and Toast need their own pricing (12, 15)
R2 §3
N6
R2 internal
High impact
Agent 1’s data lists voids “with the employee login and the manager code”; the next sentence says voided items are unavailable; §4 says Square cannot show badge vs code
Those fields are verify-gated (ADR-004)
R2 §2, §4
N12
R2 vs checked
High impact
“Start on Square because it needs no approval and no fee” rests on personal tokens; under OAuth, app approval is unconfirmed
TBD: confirm Square OAuth approval (16d)
R2 §10 · Checked 2026-10-19
N1
R1 internal
“$6,000–$15,000/year to employee theft (4% of sales × $300K–$500K revenue)”: 4% of $300K–$500K is $12,000–$20,000
R1’s theft estimate is not used
R1 p.29
N2
R1 internal
Biometric clocks cost “$300–$800 per terminal” on one page and “$150–$250” on another
Moot: no biometric clocks (ADR-008)
R1 p.11, p.29
N3
R1 vs R2
R1 presents Black Box 2025 turnover as verified; R2 could not confirm it from a primary page
Turnover figures are not used
R1 p.12 · R2 §9
N4
R2 vs owner
R2 says Toast and Square bundle “nine of the twelve problems”; the owner listed 15, and R2 never says which 12
Traceability uses the owner’s 15 (02)
R2 p.2
N5
R1 internal
“No estimates or invented figures appear here”, yet pp.29–30 give unsourced loss estimates
Those estimates are not used
R1 p.1, pp.29–30
N7
R1 vs R2
“Toast’s API and Square’s API are well-documented” vs an unpublished Toast API price and missing Square voided items
R2 and the checked facts followed
R1 p.31 · R2 §2, §8
N8
R1 vs R2
Training check-offs “not quizzes” vs Agent 6’s “Two-minute SMS quizzes”
R2 followed, in v3
R1 p.27 · R2 §2
N9
R2 internal
Lineup.ai is “$79 a location” in one section and “$79–$149” in another
Low impact; Agent 5 is last
R2 §2, §4
N10
R1 vs R2
“Waste logging with employee attribution (connects to theft detection)” vs facts-only, no-accusation output
Not built; facts-only wording (ADR-006)
R1 p.26 · R2 §6
N11
R1 vs R2
Clock hardware “waived on annual subscription” vs month-to-month with one-click cancel
R2 followed
R1 p.29 · R2 §6
IDs keep the order in which the conflicts were found; the table puts the four that matter most first.
R1 = Oct 15 report · R2 = Oct 16 report · Checked = Oct 19, 2026

## Slide 29 — Risks that could sink the pilot, and the shortcuts we are taking on purpose
16c Risks and technical debt

Full text of this artboard (arrows are written as "Arrow from X to Y"):

16c / 16 · RISKS AND REGISTERS · PART C OF D · RISKS AND TECHNICAL DEBT
Risks that could sink the pilot, and the shortcuts we are taking on purpose
Likelihood and impact are this pack’s own assessment, not figures from the sources.
RISKS · RANKED
ID
Risk
Likelihood
Impact
Mitigation
Sources
RK1
Square’s API returns too little (voids, comps, no-sale opens, logins) for a useful digest
High
High
Test every verify item on the friend’s account before day one; start with the fallback wording; stop if the signal is too thin
R2 §2, §9 · Checked 2026-10-19
RK2
The pass line cannot be measured as written (void dollars)
High
High
Agree a substitute measure and the 0.5–1 point zone in the Design Partner Agreement before day one
R2 §6
RK3
A flag leads to an unfair accusation or a wrongful firing
Medium
High
Facts only, owner only, never the only basis for a firing; counsel reviews the templates
R2 §6
RK4
The owner stops opening the digest
Medium
High
Short ranked digest 2–3 times a week; weekly check-in; this is also a fail condition
R2 §2, §6
RK5
Toast or Square ships the same monitor inside the POS
Medium
High
Own the narrow wedge, publish real pilot data, keep the price under $100
R2 §1, §6; R1 p.32
RK6
Voice and Toast cost more than the product’s price
High
Medium
Price them separately before building v2 or Agent 3
R2 §3
RK7
The restaurant changes hands mid-contract
Medium
Medium
Month-to-month billing and the CSV export clause; 26% change hands in year one, 60% by year three
R2 §1, §6
RK8
A failed token refresh leaves a silent data gap
Medium
Medium
Refresh every 7 days or less; text the owner to reconnect on failure (13, scenario 4)
Checked 2026-10-19
RK9
Staff object to monitoring, or the §52-c*2 notice is incomplete
Medium
Medium
Notice gate per login; tell staff nobody is punished just for data showing up
R2 §6 · Checked 2026-10-19
TECHNICAL DEBT TAKEN ON PURPOSE
ID
Shortcut
Why it is acceptable now · when to pay it back
Sources
TD1
Shifts are owner-set time windows
No timecards until v2. Replace with real shifts when Agent 2 reads timecards.
design choice · R2 §2
TD2
One shared host, no high availability
v1 is off the service path; a missed night is re-pulled. Revisit at the heavy design’s own server.
R2 §3, §5
TD3
Event schema shaped by Square
Toast mapping may force changes; budget a schema review before the Toast connector.
design choice · R2 §10
TD4
Hand-tuned rule thresholds per restaurant
Each new anomaly type needs a new rule (ADR-002). Revisit after three paying restaurants.
R2 §2
TD5
Manual acknowledgment capture
Capture method TBD; acceptable for one pilot restaurant, not for scale.
Checked 2026-10-19
R1’s own risks 1–6 (p.31–32) are covered: integration depth (RK1), one bad experience (13, scenario 1), adoption (RK4), feature creep (ADR-001), pricing pressure (RK5), forecast accuracy (Agent 5 is last).
R1 = Oct 15 · R2 = Oct 16 · Checked = Oct 19, 2026

## Slide 30 — Not confirmed, verify on live account, and TBD: the open-questions list
16d Not confirmed, verify, TBD

Full text of this artboard (arrows are written as "Arrow from X to Y"):

16d / 16 · RISKS AND REGISTERS · PART D OF D · WHAT WE DO NOT KNOW YET
Not confirmed, verify on live account, and TBD: the open-questions list
NOT CONFIRMED · R2 §9, AS R2 LISTS THEM
NC1
Sling Pro’s price
NC2
Black Box Intelligence’s 2025 turnover from a primary page
NC3
Toast’s self-serve API price and partner fees
NC4
Whether a Clover merchant token may run in production without app approval
NC5
Whether Square exposes comp data through any API
NC6
Whether §52-c covers reading POS logs
NC7
Whether GOL §5-903 reaches SaaS at all
NC8
Meta AI’s 2026 search provider
NC9
Toast’s churn (no public restaurant-tech company discloses it)
NC10
Any Reddit owner testimony; Reddit was unreachable in both rounds
NC11
An independent owner’s willingness to pay in dollars; no survey gives it
NC12
Restaurant-software queries in AI answers; no audited case of a small company gaining AI citations
NC13
The fates of Foodspace, Spotluck, Hang, Hyper, StockCount and Cheetah
NC14
“None identified” for 2024–2026 training or hiring startup shutdowns means none found, not none occurred
VERIFY ON LIVE ACCOUNT · THE FRIEND’S SQUARE, BEFORE DAY ONE
V1
Dollar amount on cancelled (voided) orders
V2
Employee login on cancelled orders, including “opened by login X”
V3
Item-level voids on paid checks
V4
Approving manager code; Square cannot show badge vs code (R2 §4)
V5
Comp detail through the API; comps show on the ticket at $0.00 (Checked 2026-10-19)
V6
No-sale drawer opens through the API
V7
Employee login on discounts and refunds
V8
30 days of order history for the pre-pilot baseline
Rule: nothing on this list appears in a digest until its test passes. Each test result goes into the audit log, and each failure into the fallback wording (ADR-004).
Sources: Checked 2026-10-19; R2 §2, §4, §9
TBD — NOT IN SOURCES
T1
Square OAuth scope names, and whether Square needs to approve the app for production
T2
Toast partner path and terms for a multi-tenant vendor
T3
Toast order webhooks: R2 §2 says none; Toast docs list “Standard API access webhook subscriptions”. Verify
T4
Whether a vendor may use a 7shifts admin-created token across many restaurants (R2 §2)
T5
Email vendor, authentication and data terms
T6
Twilio credential type, 10DLC approval time and message limits
T7
Voice provider webhook format and authentication
T8
Model-vendor term that keeps restaurant data out of training
T9
Database hosting cost
T10
Pricing for voice and Toast tiers
T11
Pilot rule for a 0.5–1 point drop; substitute measure if void dollars are missing
T12
Gate measure from v2 to v3; calendar dates for v2 and v3
T13
Triggers for Agents 2, 4, 5 and 6
T14
How v1 defines a shift before timecards exist
T15
Retention periods beyond the 30-day CSV export
T16
How staff sign the acknowledgment
T17
NY employment counsel review of the notice and digest templates
T18
AI drafting of SOPs; a target reading time for the digest
Before day one: close V1–V8 and T1, T11, T16, T17. Everything else can wait for its phase.
R1 = Oct 15 report · R2 = Oct 16 report · Checked = Oct 19, 2026
