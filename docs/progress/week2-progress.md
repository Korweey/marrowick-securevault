<!--
Project 4 – Marrowick Health Analytics (CCGC 5506, Humber, Fall 2026)
Group H: Qawiyy A. Rabiu (N10038749), Saheedat O. Abbas (N10038753)
File: docs/progress/week2-progress.md – Week 2 progress log with evidence
-->

# Week 2 – PII gate & audit queries

**Milestone (from brief):** A seeded PII record demonstrably blocked from curated; two answered audit questions.

| Part | Scope | Status | Date |
|---|---|---|---|
| A | SNS alert topic | ✅ Complete | Oct 18 |
| B | Lambda regex PII/PHI scanner | ✅ Complete | Oct 18 |
| C | Step Functions gate (scan → choice → quarantine+notify / promote) | ✅ Complete | Oct 18 |
| D | Gate tests: 3 raw batches blocked, 3 remediated batches promoted | ✅ Complete | Oct 18 |
| E | Glue crawl of curated + access separation (Lake Formation blocked → Athena views, tested) | ✅ Complete | Oct 18 |
| F | CloudTrail audit queries in Athena (Q1, Q2, Q3) | ✅ Complete | Oct 18 |

---

## A. SNS topic
- Topic `marrowick-pii-gate-alerts` (Standard), email subscription to the team inbox – **Confirmed**.
- Topic encryption not enabled: alerts carry **no PII values** (only tenant, object key, row counts, flagged encounter IDs, finding types), so KMS on the topic would add key-policy scope without protecting anything sensitive.
- Evidence: ![](../../evidence/week2/01_sns_subscription_confirmed.png)

## B. Lambda scanner – `marrowick-pii-scan`
- Code: [`src/lambda/pii_scan.py`](../../src/lambda/pii_scan.py) · Python 3.12 · role **LabRole** · timeout 30 s · 128 MB.
- Patterns: health card `NNNN-NNN-NNN XX`, SIN `NNN-NNN-NNN`, email, street address. Structured pseudonymous ID columns (`patient_ref`, `encounter_id`, …) are skipped by design.
- **Leak-safe:** returns/logs only the finding *type* and *location*, never the matched value.
- Offline test vs answer key: [`tests/test_pii_scan.py`](../../tests/test_pii_scan.py) → **TP 14, FP 0, FN 0 (precision 1.00, recall 1.00)**.
- Live Lambda test (clinic-a): 191 rows, `pii_found: true`, 4 flagged; also proves LabRole can decrypt with `marrowick-data-key`.
- Evidence: ![](../../evidence/week2/03_lambda_code_deployed.png) ![](../../evidence/week2/04_lambda_timeout_30s.png) ![](../../evidence/week2/05_lambda_test_clinic-a_pii_found.png)

## C. Step Functions gate – `marrowick-pii-gate`
- Definition: [`src/stepfunctions/pii_gate.asl.json`](../../src/stepfunctions/pii_gate.asl.json) · Standard workflow · role **LabRole**.
- `ScanForPII` (Lambda) → `PIIDetected?` (Choice on `$.scan.result.pii_found`)
  - **true** → `QuarantineBatch` (S3 CopyObject → quarantine) → `NotifySecurityTeam` (SNS) → `GateBlocked` (**Fail**, error `PIIDetected`)
  - **default** → `PromoteToCurated` (S3 CopyObject → curated) → `BatchPromoted` (Succeed)
- Raw objects are never modified – the raw zone is the immutable record of what each clinic submitted.
- Evidence: ![](../../evidence/week2/06_stepfunctions_pii_gate_workflow.png)

## D. Gate test results
| # | Execution | Input object | Path taken | Status | Alert | Flagged |
|---|---|---|---|---|---|---|
| 1 | test1-clinic-a-raw | clinic-a/clinic-a_encounters.csv | Quarantine → Notify → GateBlocked | ❌ Failed (blocked) | ✅ email | 4 |
| 2 | test2-clinic-b-raw | clinic-b/clinic-b_encounters.csv | Quarantine → Notify → GateBlocked | ❌ Failed (blocked) | ✅ email | 6 (incl. SIN) |
| 3 | test3-clinic-c-raw | clinic-c/clinic-c_encounters.csv | Quarantine → Notify → GateBlocked | ❌ Failed (blocked) | ✅ email | 4 |
| 4 | test4-clinic-a-redacted | clinic-a/clinic-a_encounters_v2_redacted.csv | PromoteToCurated → BatchPromoted | ✅ Succeeded | none | 0 |
| 5 | test5-clinic-b-redacted | clinic-b/…_v2_redacted.csv | PromoteToCurated → BatchPromoted | ✅ Succeeded | none | 0 |
| 6 | test6-clinic-c-redacted | clinic-c/…_v2_redacted.csv | PromoteToCurated → BatchPromoted | ✅ Succeeded | none | 0 |

**Live accuracy:** the 14 encounter IDs listed in the three alert emails match the 14 rows in the answer key exactly – precision 1.00, recall 1.00.

**Remediation model:** a data steward replaced only the flagged `notes_field` values with `[REDACTED - PII removed by data steward]` ([`data/remediated/`](../../data/remediated/)) and resubmitted as a new `_v2_redacted` object. The original stays in raw (and quarantine) as the audit record.

Evidence – blocked runs:
- ![](../../evidence/week2/08_gate_test1_graph_blocked.png) ![](../../evidence/week2/09_gate_test1_event_history.png) ![](../../evidence/week2/10_gate_test1_table_view.png)
- ![](../../evidence/week2/13_gate_test2_clinic-b_blocked.png) ![](../../evidence/week2/14_gate_test2_clinic-b_events.png)
- ![](../../evidence/week2/15_gate_test3_clinic-c_blocked.png) ![](../../evidence/week2/16_gate_test3_clinic-c_events.png)
- Alerts: ![](../../evidence/week2/07_sns_alert_email_quarantined.png) ![](../../evidence/week2/17_sns_alert_clinic-b.png) ![](../../evidence/week2/18_sns_alert_clinic-c.png)
- Proof it never reached curated: ![](../../evidence/week2/11_quarantine_clinic-a_has_file.png) ![](../../evidence/week2/12_curated_clinic-a_empty.png)

Evidence – remediated runs:
- Uploads: ![](../../evidence/week2/19_upload_redacted_clinic-a.png) ![](../../evidence/week2/20_upload_redacted_clinic-b.png) ![](../../evidence/week2/21_upload_redacted_clinic-c.png)
- Raw now holds original + redacted: ![](../../evidence/week2/22_raw_clinic-a_original_and_redacted.png) ![](../../evidence/week2/23_raw_clinic-b_original_and_redacted.png) ![](../../evidence/week2/24_raw_clinic-c_original_and_redacted.png)
- Promoted: ![](../../evidence/week2/25_gate_test4_clinic-a_redacted_promoted.png) ![](../../evidence/week2/26_gate_test5_clinic-b_redacted_promoted.png) ![](../../evidence/week2/27_gate_test6_clinic-c_redacted_promoted.png)

## E. Catalog + access separation
- Crawler `marrowick-curated-crawler` (LabRole) → database `marrowick_curated`, table `marrowick_curated_004716017211`: **615 rows**, 9 columns + `partition_0` (clinic-a/b/c from folder names).
- **Lake Formation blocked:** `voclabs` is denied `lakeformation:GetDataLakeSettings`, so no data-lake admin or grants are possible. The intended Lake Formation design (data cells filters + grants + CLI) is documented as design-only in [`lakeformation/permission-matrix.md`](../../lakeformation/permission-matrix.md).
- **Fallback implemented and tested:** role-scoped Athena views ([`sql/01_access_views.sql`](../../sql/01_access_views.sql), tests in [`sql/02_access_tests.sql`](../../sql/02_access_tests.sql)).

| View | Role | Rows | Hidden columns |
|---|---|---|---|
| `view_clinic_a_analyst` | Clinic analyst (Brambleton) | `tenant_id = 'clinic-a'` | `notes_field` |
| `view_corporate_analyst` | Corporate analyst | all tenants | `notes_field`, `patient_ref` |

| Test | Query | Expected | Actual |
|---|---|---|---|
| T0 | base table, count by tenant | 191/243/181 | ✅ 191/243/181 |
| T1 | clinic view, count by tenant | only clinic-a | ✅ clinic-a 191 |
| T2 | clinic view, `tenant_id='clinic-b'` | no rows | ✅ Results (0) |
| T3 | clinic view, `SELECT notes_field` | denied | ✅ COLUMN_NOT_FOUND |
| T4 | corporate view, count by tenant | 3 clinics | ✅ 191/243/181 |
| T5a | corporate view, `SELECT notes_field` | denied | ✅ COLUMN_NOT_FOUND |
| T5b | corporate view, `SELECT patient_ref` | denied | ✅ COLUMN_NOT_FOUND |

**Honest limitation:** views restrict what a query *through the view* returns; a principal with access to the base table or S3 could bypass them. In production, Lake Formation filters (designed above) enforce this on the table itself, and analysts get no direct base-table/S3 access.

Evidence: ![](../../evidence/week2/38_view_clinic_a_created.png) ![](../../evidence/week2/39_view_corporate_created.png) ![](../../evidence/week2/40_T0_baseline_615_rows.png) ![](../../evidence/week2/41_T1_clinic_analyst_only_clinic-a.png) ![](../../evidence/week2/42_T2_clinic_analyst_clinic-b_no_results.png) ![](../../evidence/week2/43_T3_clinic_analyst_notes_field_denied.png) ![](../../evidence/week2/44_T4_corporate_all_clinics.png) ![](../../evidence/week2/45_T5a_corporate_notes_field_denied.png) ![](../../evidence/week2/46_T5b_corporate_patient_ref_denied.png)

## F. CloudTrail audit (Athena over CloudTrail logs)
- SQL: [`sql/03_cloudtrail_audit.sql`](../../sql/03_cloudtrail_audit.sql) – database `marrowick_audit`, table `cloudtrail_logs` with **partition projection** (no crawler needed).
- Sanity check: 38 AWS services recorded (s3 418, glue 190, iam 155, lambda 110, athena 96, states 62, kms 39, sns 20, lakeformation 18 …).
- Times in results are **UTC** (local EDT = UTC−4).

**Q1 – Who accessed the curated clinic-c data?** (S3 data events, 5 results)
| UTC time | Who | Via | Action | Meaning |
|---|---|---|---|---|
| 22:11:34 | LabRole (Step Functions session) | – | CopyObject | PII gate promoted the redacted clinic-c batch |
| 22:20:34 | LabRole/AWS-Crawler | glue | GetObject | Crawler read the file to build the table |
| 22:41:15, 22:41:37, 22:42:43 | voclabs/Qawiyy | athena | GetObject | Analyst queries (T0/T4 tests) |

**Q2 – Which API calls changed bucket security settings?** (management events, 5 results)
| UTC time | Who | Event | Bucket |
|---|---|---|---|
| 20:17:50 | voclabs/Qawiyy | PutBucketPolicy | aws-cloudtrail-logs-… (set by CloudTrail on trail creation) |
| 20:35:44 | voclabs/Qawiyy | PutBucketPolicy | marrowick-raw |
| 20:36:29 | voclabs/Qawiyy | PutBucketPolicy | marrowick-quarantine |
| 20:37:07 | voclabs/Qawiyy | PutBucketPolicy | marrowick-curated |
| 22:36:08 | voclabs/Qawiyy | PutBucketEncryption | marrowick-athena-results |

**Q3 – Anomaly detection: denied/unauthorized attempts** (50 results, LIMIT reached)
- Clear cluster of **lakeformation GetDataLakeSettings / ListPermissions / ListResources AccessDenied** (22:28–22:33 UTC) – the attempted data-lake-admin setup, i.e. a principal repeatedly probing a security service it is not permitted to use.
- Also `s3 GetBucketObjectLockConfiguration` denied, plus background console noise (notifications, resource-explorer, uxc, datazone).
- **Finding / improvement:** raw "all AccessDenied" is noisy in the Learner Lab; Q3b filters to security/data services so real signals stand out. In production this query would drive a CloudWatch alarm (e.g. >5 lakeformation/kms/iam denials in 5 minutes).

Evidence: ![](../../evidence/week2/48_cloudtrail_table_created.png) ![](../../evidence/week2/49_cloudtrail_sanity_check_38_services.png) ![](../../evidence/week2/51_audit_Q1_who_accessed_curated_clinic-c.png) ![](../../evidence/week2/52_audit_Q2_bucket_security_changes.png) ![](../../evidence/week2/53_audit_Q3_access_denied_page1.png) ![](../../evidence/week2/54_audit_Q3_access_denied_page2.png)

---

## Issues encountered & resolutions
| # | Issue | Impact | Resolution | Evidence |
|---|---|---|---|---|
| 1 | First Lambda test used the console's sample "Hello World" event → `KeyError: 'bucket'`. | Test failed; code was fine. | Replaced test event with `{"bucket", "key"}`; saved as `clinic-a-raw`. | ![](../../evidence/week2/issues/issue1_lambda_test_default_hello_world_event.png) |
| 2 | Step Functions "Create new role" → *Failed to create IAM role* (Learner Lab blocks IAM role creation). | Could not deploy a least-privilege workflow role. | Used existing **LabRole**. The console's auto-generated permission list (lambda:InvokeFunction, sns:Publish, s3:CopyObject) is reused as the **design-only** least-privilege policy in Week 3. | ![](../../evidence/week2/issues/issue2_sfn_cannot_create_iam_role.png) |
| 3 | Code signing toggled on during Lambda creation, blocking "Create". | Function could not be created. | Disabled code signing (needs a signing profile not used in this design). | – |
| 4 | Lake Formation: `voclabs` not authorized for `lakeformation:GetDataLakeSettings`; cannot add data-lake admin. | No Lake Formation grants/filters possible in the lab. | Implemented equivalent row/column restrictions as Athena views and tested them; documented full LF design as design-only. | ![](../../evidence/week2/issues/issue4_lakeformation_access_denied.png) |
