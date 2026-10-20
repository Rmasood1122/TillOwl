# Evidence folder: the rule

A step is **done** only when `docs/build/evidence/STEP-NN.md` exists, passes
`python tools/check_evidence.py validate --step STEP-NN`, and its done PR passes the `governance` check (G3). Until then the step is not done, whatever anyone says.

Evidence is a short, fixed-format record: the gate command, its exit code, and a summary of the output in allowlisted lines (counts, hashes, run or job ids, field names). Raw output stays in the CI log or the founder's terminal. **Never** write names, values, staff identifiers, free text or "it works".

This folder starts empty. Each step's done PR adds exactly one file here and changes nothing else except that step's status file.

## Format

The first line is `# STEP-NN evidence`. Then one block per gate command, in the same order as the `gate` in `docs/build/status/STEP-NN.json` (commands joined there by ` && `). A block starts with `command:` and is followed by the lines for that command. Blank lines are allowed. Every other line must match one of these, exactly:

| Line | Meaning |
|---|---|
| `command: <gate command>` | Must equal the gate command. `check_artifact.py` may add `--date`, `--count`, `--absent`, `--refused`. |
| `exit_code: 0` | Exactly one per block; must be 0. |
| `sha256: <64 hex> label=<label>` | Labels: `counsel_t17a`, `counsel_t17b`, `sms_optin`, `tendlc_approval`, `terms_t5`, `terms_t6`, `terms_t8`, `t8_template_only`, `notice`, `ack_batch`, `posting`, `authorization`, `support_permission`, `dpa`, `pass_line`, `upfront_invoice`, `t1_approval`, `t1_not_required`, `invoice_settlement`, `notice_export`, `findings`, `criteria`, `template_manifest`, `restore_canary` |
| `count: <n> <unit>` | Units: `passed`, `rows`, `tenants`, `connections`, `refreshes`, `revokes`, `logins_hashed`, `logins_distinct`, `logins_total`, `staff_signed`, `staff_absent`, `staff_refused`, `acks_entered`, `acks_mapped`, `acks_unmapped`, `shift_windows`, `events`, `orders`, `days`, `v_items`, `flags`, `digests`, `sms_segments`, `tokens_in`, `tokens_out`, `tokens_thinking`, `health_checks`, `rows_remaining`, `owners_2fa`, `templates`, `sample_flags`, `scopes`, `steps_done`, `cancelled_orders`, `comps`, `discounts`, `refunds`, `no_sale_opens`, `item_voids` |
| `role: owner\|counsel\|vendor\|staff\|founder` | Who signed. Staff only ever as counts. |
| `date: YYYY-MM-DD` | Between 2026-10-01 and today. At least one per file. |
| `run_id: <digits>` | The GitHub Actions run that ran a pytest gate. |
| `job_id: <id>` | The Render one-off job id of a founder-launched production job. |
| `field: <api.field.name> type=<string\|integer\|money\|timestamp\|boolean\|enum\|object\|array\|absent>` | A Square field name and type, never a value. |
| `v_item: V<n>[.<subfield>] RETURNED\|NOT_RETURNED\|PARTIAL` | Live-spike result (STEP-20). PARTIAL counts as NOT_RETURNED for digests. |
| `v_shape: V<n>[.<subfield>] CAN_RETURN\|CANNOT_RETURN\|NOT_OBSERVABLE_IN_SANDBOX` | Sandbox-spike API shape (STEP-01). |
| `scope: <SQUARE_SCOPE_NAME>` | An OAuth scope name. |
| `decision: GO\|NO-GO` | STEP-21 only; must equal the status file. |
| `backup_expires: YYYY-MM-DD` | When the last backup holding spike or tenant data expires. |
| `oauth_connection: kept\|revoked` | After the spike or exit. |
| `model_id: claude-…` | The pinned model, in the cost step. |
| `usd_month: <n.nn> <unit>` | Cost step only. Units: `total`, `tokens`, `sms`, `hosting_web`, `hosting_cron`, `db_staging`, `db_production`, `email`, `lean_line` |

## What each kind of gate must show

| Gate kind | Required |
|---|---|
| `ci_fixture` | A pytest block with `run_id`, `count: N passed` (N ≥ 1), and a date. CI checks the run is a green `ci` run on the parent of the commit that adds this file, with the step `in_progress` there, and that the commit changes only this step's evidence and status. |
| `ci_staging` | The same, but the run is a `staging` run on `main` whose job `gate STEP-NN` is green, and the gate files are unchanged since. |
| `production_job` | One block per job with `job_id` and `exit_code: 0`, as printed by the job the founder launched. Steps with a findings file also carry `sha256: … label=findings`, which CI recomputes. |
| `sandbox_spike` | `sha256: … label=findings` matching the findings file. |
| `human` | A `role` line. `check_artifact.py` blocks also need `sha256` (label matching `--label`), `role` (matching `--role`) and `date`; staff blocks need signed, absent and refused counts. |

## Examples

ci_fixture (`docs/build/evidence/STEP-24.md`):

```
# STEP-24 evidence
command: pytest -c pytest.ini --rootdir=. tests/gates/step_24
exit_code: 0
count: 14 passed
run_id: 11873456021
date: 2026-11-04
```

production_job (founder pastes the job's own output into the engineer's session):

```
# STEP-14 evidence
command: python -m tillowl.jobs.provision_tenant --kind own
exit_code: 0
job_id: job-d1abc23
count: 1 tenants
date: 2026-11-06
```

human, printed by `tools/check_artifact.py` in the founder's terminal:

```
# STEP-05 evidence
command: python tools/check_artifact.py --step STEP-05 --label notice --role owner --date 2026-11-08
exit_code: 0
sha256: 3f1c…(64 hex)… label=notice
role: owner
date: 2026-11-08

command: python tools/check_artifact.py --step STEP-05 --label ack_batch --role staff --count 11 --absent 1 --refused 0 --date 2026-11-09
exit_code: 0
sha256: 9a0e…(64 hex)… label=ack_batch
role: staff
count: 11 staff_signed
count: 1 staff_absent
count: 0 staff_refused
date: 2026-11-09
```
